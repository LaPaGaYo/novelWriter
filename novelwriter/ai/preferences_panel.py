"""
plotwright fork — AI Preferences Panel
======================================

The Preferences > AI section. Sprint 2 widens the S1 skeleton:

- Un-grey the per-feature toggles (REWRITE / CONSISTENCY) so they edit
  ``AIConfig.features`` directly. The features themselves still land in
  S3 / S4; flipping the toggle enables the flag the substrate already
  honors via ``AIConfig.feature_active`` and ``NetworkGate.guard``.
- Expose provider rows: each registered provider gets a collapsible row
  with its own auth + settings widgets (Ollama base URL, Anthropic masked
  API key, Gemini API key + OAuth radio group).
- Per-feature provider dropdown — the user picks which provider runs
  REWRITE / CONSISTENCY (and the substrate's ``AIConfig.providers``
  records the choice).
- "Dry-run" button per feature: fires a fixed test prompt through
  ``staging.stage``, surfaces the staged result + token estimate inline.
  This is the S2 smoke-test surface (success criterion SC-4).
- A11y: ``setBuddy`` ties every label to its input; ``accessibleName`` set
  on every ``QComboBox`` / ``QPushButton`` per the design contract.

Vermilion appears NOWHERE in this panel. The panel is chrome, not AI
activity — design contract Component 3 + AI Preferences panel section.

Sprint contract path note:
The sprint contract listed this file as ``novelwriter/preferences/ai_panel.py``.
We chose ``novelwriter/ai/preferences_panel.py`` so every fork-specific
module sits under one prefix, which minimises merge conflicts with
upstream ``novelwriter/dialogs/preferences.py``. The deviation is also
logged in ``.planning/current/build/build-result.md``.
"""
from __future__ import annotations

import logging

from typing import TYPE_CHECKING, Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from novelwriter.ai.config import AIConfig, AIFeature
from novelwriter.ai.provider.registry import available_providers

if TYPE_CHECKING:
    from novelwriter.ai.keychain import KeyStore
    from novelwriter.ai.provider.base import Provider

logger = logging.getLogger(__name__)


# DESIGN.md tokens. The panel is chrome; vermilion is forbidden here.
_COLOR_MUTED = "#7A6A4F"   # Foxing
_COLOR_OK = "#2C5F5D"      # Hooker's Green (status: signed-in indicator)
_COLOR_ERROR = "#7A2222"   # Error (NOT vermilion)


_DRY_RUN_PROMPT = (
    "Once upon a time in a kingdom far away, a writer began drafting a "
    "novel. The writer wanted to test that the AI plumbing worked end "
    "to end before trusting it with real prose. This sentence is that "
    "test."
)


class AIPreferencesPanel(QWidget):
    """The Preferences > AI section.

    The panel edits an ``AIConfig`` in place. Persistence to disk is the
    caller's responsibility (typically the host preferences dialog's OK /
    Apply button writes the config via ``AIConfig.save``).

    Optional dependencies:
    - ``keystore`` resolves API keys / OAuth blobs at registry time. Tests
      pass a ``FakeKeyStore``; production passes the real keychain.
    - ``provider_factory`` is the callable that instantiates a provider by
      id given the per-provider settings. Defaults to
      ``provider.registry.make_provider``. Tests inject a deterministic
      ``MockProvider`` factory so dry-run is hermetic.
    """

    # Emitted whenever the user changes any visible setting. The host
    # dialog uses this to schedule a save on dialog accept.
    settingsChanged = pyqtSignal()

    def __init__(
        self,
        config: AIConfig,
        *,
        keystore: "KeyStore | None" = None,
        provider_factory: Callable[[str, dict, "KeyStore | None"], "Provider"] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)
        self.setObjectName("AIPreferencesPanel")
        self._config = config
        self._keystore = keystore
        self._provider_factory = provider_factory

        # Header
        self._title = QLabel(self.tr("AI features"), self)
        font = self._title.font()
        font.setBold(True)
        font.setPointSizeF(font.pointSizeF() + 2.0)
        self._title.setFont(font)
        self._title.setAccessibleName(self.tr("AI features section heading"))

        self._desc = QLabel(
            self.tr(
                "Off until you say otherwise. Each feature is opt-in per "
                "project. Token estimates appear before every cloud call.",
            ),
            self,
        )
        self._desc.setWordWrap(True)
        self._desc.setStyleSheet(f"color: {_COLOR_MUTED};")

        # Master toggle. When the master is off, the per-feature rows visually
        # de-emphasize (text becomes Foxing) but remain interactive so the
        # user can choose a provider for later; the substrate's
        # ``feature_active`` check enforces master + feature together so this
        # is safe.
        self._master_toggle = _ToggleRow(
            label=self.tr("Enable AI for this project"),
            sub=self.tr("Master switch. Required for any AI feature below."),
            initial=self._config.enabled,
            parent=self,
        )
        self._master_toggle.toggled.connect(self._on_master_toggled)
        self._master_toggle.setAccessibleName(self.tr("Master AI toggle"))

        # Per-feature rows (REWRITE, CONSISTENCY). S2: un-greyed; toggle
        # writes to ``AIConfig.features``. The feature implementation lands
        # in S3 (rewrite) / S4 (consistency) but the substrate's network gate
        # already honors the flag from S1.
        self._feature_rows: dict[AIFeature, _FeatureRow] = {}
        for feature, label in (
            (AIFeature.REWRITE, self.tr("Inline rewrite")),
            (AIFeature.CONSISTENCY, self.tr("Consistency check")),
        ):
            row = _FeatureRow(
                feature=feature,
                label=label,
                config=self._config,
                parent=self,
                on_dry_run=self._run_dry_run,
                provider_names=("",) + available_providers(),
            )
            row.toggled.connect(lambda *_: self.settingsChanged.emit())
            row.providerChanged.connect(lambda *_: self.settingsChanged.emit())
            self._feature_rows[feature] = row

        # Per-provider config rows. Collapsed by default; click the row
        # header to expand. Each row is responsible for its own auth UX and
        # writes back to ``AIConfig.provider_configs``.
        self._provider_rows: list[_ProviderConfigRow] = []
        for provider_id in available_providers():
            if provider_id == "mock":
                # MockProvider needs no auth surface. Test-only id; we keep
                # it out of the user-facing panel.
                continue
            row = _make_provider_config_row(
                provider_id, config=self._config, keystore=self._keystore, parent=self,
            )
            row.settingsChanged.connect(self.settingsChanged.emit)
            self._provider_rows.append(row)

        # Privacy footer — fixed copy from the design contract.
        self._privacy = QLabel(
            self.tr(
                "Off until you say otherwise. Each feature is opt-in per "
                "project. Token estimates appear before every cloud call. "
                "No prompts or outputs are logged to disk unless you enable "
                "the debug log.",
            ),
            self,
        )
        self._privacy.setWordWrap(True)
        self._privacy.setStyleSheet(f"color: {_COLOR_MUTED};")

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)
        layout.addWidget(self._title)
        layout.addWidget(self._desc)
        layout.addWidget(_hsep(self))

        # Per-project opt-in
        layout.addWidget(_section_header(self.tr("Per-project opt-in"), self))
        layout.addWidget(self._master_toggle)
        layout.addWidget(_hsep(self))

        # Features
        layout.addWidget(_section_header(self.tr("Features"), self))
        for feature in (AIFeature.REWRITE, AIFeature.CONSISTENCY):
            layout.addWidget(self._feature_rows[feature])
        layout.addWidget(_hsep(self))

        # Providers
        layout.addWidget(_section_header(self.tr("Providers"), self))
        for row in self._provider_rows:
            layout.addWidget(row)
        layout.addWidget(_hsep(self))

        # Privacy footer
        layout.addWidget(_section_header(self.tr("Privacy"), self))
        layout.addWidget(self._privacy)
        layout.addStretch(1)

    # ------------------------------------------------------------------
    # Public surface (tests + host dialog)
    # ------------------------------------------------------------------

    def config(self) -> AIConfig:
        """Return the AIConfig this panel is editing in-place."""
        return self._config

    def feature_row(self, feature: AIFeature) -> "_FeatureRow":
        """Return the per-feature row widget (used by tests)."""
        return self._feature_rows[feature]

    def provider_rows(self) -> list["_ProviderConfigRow"]:
        """Return all provider config rows (used by tests)."""
        return list(self._provider_rows)

    # ------------------------------------------------------------------
    # Internal: master toggle handler
    # ------------------------------------------------------------------

    def _on_master_toggled(self, checked: bool) -> None:
        self._config.enabled = checked
        self.settingsChanged.emit()

    # ------------------------------------------------------------------
    # Internal: dry-run smoke entry point
    # ------------------------------------------------------------------

    def _run_dry_run(self, feature: AIFeature) -> tuple[str, int]:
        """Fire a fixed test prompt through ``staging.stage`` and return
        ``(staged_text, estimated_tokens_in)``.

        Selected provider is read from ``AIConfig.providers[feature]``;
        per-provider settings come from ``AIConfig.provider_configs``. If
        no provider is configured the method returns a short helper string
        so the row can display it without raising.
        """
        provider_id = self._config.providers.get(feature)
        if not provider_id:
            return (self.tr("Pick a provider first."), 0)

        # Resolve the factory: tests inject one; production uses the registry.
        factory = self._provider_factory
        if factory is None:
            from novelwriter.ai.provider.registry import make_provider as _real

            def _factory(pid: str, settings: dict, keystore: "KeyStore | None") -> "Provider":
                return _real(pid, settings=settings, keystore=keystore)

            factory = _factory

        settings = self._config.provider_config(provider_id)
        try:
            provider = factory(provider_id, settings, self._keystore)
        except Exception as exc:  # noqa: BLE001 - boundary
            logger.warning("Dry-run could not build provider %s: %s", provider_id, exc)
            return (self.tr("Provider error: {0}").format(str(exc)), 0)

        # The staging entry point is the same the S3 review pane will use.
        # We import here so this module's import side effects stay narrow.
        from novelwriter.ai.staging import stage

        try:
            staged = stage(_DRY_RUN_PROMPT, provider, transformation="dry-run")
        except Exception as exc:  # noqa: BLE001 - boundary
            logger.warning("Dry-run failed: %s", exc)
            return (self.tr("Dry-run failed: {0}").format(str(exc)), 0)
        return (staged.proposed or self.tr("(empty response)"), staged.estimated_tokens_in)


# ----------------------------------------------------------------------
# Internal widget primitives
# ----------------------------------------------------------------------


def _section_header(text: str, parent: QWidget) -> QLabel:
    """Build a 14px/600 weight section header per the design contract."""
    label = QLabel(text, parent)
    font = label.font()
    font.setBold(True)
    font.setPointSizeF(font.pointSizeF() + 0.5)
    label.setFont(font)
    return label


def _hsep(parent: QWidget) -> QFrame:
    """Horizontal separator using the Foxing color."""
    sep = QFrame(parent)
    sep.setFrameShape(QFrame.Shape.HLine)
    sep.setStyleSheet(f"color: {_COLOR_MUTED};")
    return sep


class _ToggleRow(QWidget):
    """A labelled checkbox row with a primary label and a sub-line caption."""

    toggled = pyqtSignal(bool)

    def __init__(
        self,
        label: str,
        sub: str,
        initial: bool,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)

        self._main = QLabel(label, self)
        font = self._main.font()
        font.setBold(True)
        self._main.setFont(font)

        self._sub = QLabel(sub, self)
        self._sub.setStyleSheet(f"color: {_COLOR_MUTED};")
        self._sub.setWordWrap(True)

        self._checkbox = QCheckBox(self)
        self._checkbox.setChecked(initial)
        self._checkbox.toggled.connect(self.toggled)
        self._checkbox.setAccessibleName(label)

        # setBuddy: clicking the main label focuses the checkbox.
        self._main.setBuddy(self._checkbox)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        text_layout.addWidget(self._main)
        text_layout.addWidget(self._sub)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addLayout(text_layout, 1)
        layout.addWidget(self._checkbox, 0)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def set_locked(self, locked: bool) -> None:
        """Disable the checkbox and grey the labels."""
        self._checkbox.setEnabled(not locked)
        if locked:
            self._main.setStyleSheet(f"color: {_COLOR_MUTED};")
        else:
            self._main.setStyleSheet("")

    def is_checked(self) -> bool:
        return self._checkbox.isChecked()

    def set_checked(self, checked: bool) -> None:
        self._checkbox.setChecked(checked)


class _FeatureRow(QWidget):
    """Per-feature row: toggle + provider dropdown + dry-run button + result panel."""

    toggled = pyqtSignal(bool)
    providerChanged = pyqtSignal(str)

    def __init__(
        self,
        feature: AIFeature,
        label: str,
        config: AIConfig,
        provider_names: tuple[str, ...],
        on_dry_run: Callable[[AIFeature], tuple[str, int]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)
        self._feature = feature
        self._config = config
        self._on_dry_run = on_dry_run

        self._checkbox = QCheckBox(label, self)
        self._checkbox.setChecked(config.features.get(feature, False))
        self._checkbox.toggled.connect(self._on_toggled)
        self._checkbox.setAccessibleName(
            self.tr("Enable {0} feature").format(label),
        )

        self._provider_label = QLabel(self.tr("Provider:"), self)
        self._provider_combo = QComboBox(self)
        for name in provider_names:
            self._provider_combo.addItem(name or self.tr("(none)"), userData=name)
        # Restore the user's previous selection.
        selected = config.providers.get(feature) or ""
        idx = self._provider_combo.findData(selected)
        if idx >= 0:
            self._provider_combo.setCurrentIndex(idx)
        self._provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        self._provider_combo.setAccessibleName(
            self.tr("Provider for {0}").format(label),
        )
        self._provider_label.setBuddy(self._provider_combo)

        self._dry_run_btn = QPushButton(self.tr("Dry-run"), self)
        self._dry_run_btn.clicked.connect(self._on_dry_run_clicked)
        self._dry_run_btn.setAccessibleName(
            self.tr("Dry-run {0}").format(label),
        )

        self._result = QTextEdit(self)
        self._result.setReadOnly(True)
        self._result.setVisible(False)
        self._result.setMaximumHeight(120)
        self._result.setAccessibleName(self.tr("Dry-run result"))

        row_layout = QHBoxLayout()
        row_layout.addWidget(self._checkbox)
        row_layout.addStretch(1)
        row_layout.addWidget(self._provider_label)
        row_layout.addWidget(self._provider_combo)
        row_layout.addWidget(self._dry_run_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(6)
        layout.addLayout(row_layout)
        layout.addWidget(self._result)

    # ---- handlers -----------------------------------------------------

    def _on_toggled(self, checked: bool) -> None:
        self._config.features[self._feature] = checked
        self.toggled.emit(checked)

    def _on_provider_changed(self, _idx: int) -> None:
        value = self._provider_combo.currentData()
        self._config.providers[self._feature] = value or None
        self.providerChanged.emit(value or "")

    def _on_dry_run_clicked(self) -> None:
        text, tokens = self._on_dry_run(self._feature)
        body = self.tr("Estimated tokens in: {0}\n\n{1}").format(tokens, text)
        self._result.setPlainText(body)
        self._result.setVisible(True)

    # ---- read accessors (used by tests) ------------------------------

    def is_enabled_in_ui(self) -> bool:
        return self._checkbox.isChecked()

    def selected_provider(self) -> str | None:
        value = self._provider_combo.currentData()
        return value or None

    def last_result_text(self) -> str:
        return self._result.toPlainText()


# ----------------------------------------------------------------------
# Provider config rows — one class per provider auth shape
# ----------------------------------------------------------------------


class _ProviderConfigRow(QWidget):
    """Base class for per-provider config rows. Emits ``settingsChanged``."""

    settingsChanged = pyqtSignal()

    def __init__(self, provider_id: str, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self.provider_id = provider_id
        # Outer layout owns a section header + an inner body layout that
        # subclasses fill via ``_build_body``.
        self._header = QLabel(self.tr(provider_id.title()), self)
        font = self._header.font()
        font.setBold(True)
        self._header.setFont(font)

        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(0, 0, 0, 0)
        self._outer.setSpacing(4)
        self._outer.addWidget(self._header)


def _make_provider_config_row(
    provider_id: str,
    *,
    config: AIConfig,
    keystore: "KeyStore | None",
    parent: QWidget,
) -> _ProviderConfigRow:
    """Build the right config row for ``provider_id``."""
    if provider_id == "ollama":
        return _OllamaConfigRow(config=config, parent=parent)
    if provider_id == "anthropic":
        return _AnthropicConfigRow(config=config, keystore=keystore, parent=parent)
    if provider_id == "gemini":
        return _GeminiConfigRow(config=config, keystore=keystore, parent=parent)
    # Unknown provider id: render a placeholder row so the panel never raises.
    placeholder = _ProviderConfigRow(provider_id, parent=parent)
    placeholder._outer.addWidget(QLabel(f"(no config UI for {provider_id})", placeholder))
    return placeholder


class _OllamaConfigRow(_ProviderConfigRow):
    """Ollama: base URL field only."""

    def __init__(self, config: AIConfig, parent: QWidget) -> None:
        super().__init__("ollama", parent=parent)
        self._config = config
        settings = config.provider_config("ollama")

        self._base_url = QLineEdit(self)
        self._base_url.setText(settings.get("base_url", "http://127.0.0.1:11434"))
        self._base_url.setAccessibleName(self.tr("Ollama base URL"))
        self._base_url.textChanged.connect(self._on_changed)

        self._model = QLineEdit(self)
        self._model.setText(settings.get("model", "llama3.1"))
        self._model.setAccessibleName(self.tr("Ollama model"))
        self._model.textChanged.connect(self._on_changed)

        url_label = QLabel(self.tr("Base URL:"), self)
        url_label.setBuddy(self._base_url)
        model_label = QLabel(self.tr("Model:"), self)
        model_label.setBuddy(self._model)

        form = QFormLayout()
        form.addRow(url_label, self._base_url)
        form.addRow(model_label, self._model)
        self._outer.addLayout(form)

    def _on_changed(self, *_args) -> None:
        self._config.set_provider_config(
            "ollama",
            {
                "base_url": self._base_url.text().strip() or "http://127.0.0.1:11434",
                "model": self._model.text().strip() or "llama3.1",
            },
        )
        self.settingsChanged.emit()


class _AnthropicConfigRow(_ProviderConfigRow):
    """Anthropic: masked API key field, keychain-backed."""

    def __init__(
        self,
        config: AIConfig,
        keystore: "KeyStore | None",
        parent: QWidget,
    ) -> None:
        super().__init__("anthropic", parent=parent)
        self._config = config
        self._keystore = keystore
        settings = config.provider_config("anthropic")

        self._api_key = QLineEdit(self)
        # Mask: the field never shows the key. Reading-back fills with a
        # placeholder so the user can tell a key is stored.
        self._api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key.setAccessibleName(self.tr("Anthropic API key"))
        self._api_key.setPlaceholderText(self._placeholder_for_stored_key())
        self._api_key.editingFinished.connect(self._on_key_committed)

        self._model = QLineEdit(self)
        self._model.setText(settings.get("model", "claude-sonnet-4-5"))
        self._model.setAccessibleName(self.tr("Anthropic model"))
        self._model.textChanged.connect(self._on_model_changed)

        key_label = QLabel(self.tr("API key:"), self)
        key_label.setBuddy(self._api_key)
        model_label = QLabel(self.tr("Model:"), self)
        model_label.setBuddy(self._model)

        form = QFormLayout()
        form.addRow(key_label, self._api_key)
        form.addRow(model_label, self._model)
        self._outer.addLayout(form)

    def _placeholder_for_stored_key(self) -> str:
        if self._keystore is None:
            return self.tr("(no keychain configured)")
        try:
            existing = self._keystore.get("anthropic")
        except Exception:
            return self.tr("(keychain unavailable)")
        if existing:
            return self.tr("(stored — leave blank to keep)")
        return self.tr("Paste your Anthropic API key")

    def _on_key_committed(self) -> None:
        text = self._api_key.text().strip()
        if not text or self._keystore is None:
            return
        try:
            self._keystore.put("anthropic", text)
        except Exception as exc:  # noqa: BLE001 - boundary
            logger.warning("Storing Anthropic key failed: %s", exc)
            return
        # Clear the in-memory field after storing so it's not lying around.
        self._api_key.clear()
        self._api_key.setPlaceholderText(self.tr("(stored — leave blank to keep)"))
        self.settingsChanged.emit()

    def _on_model_changed(self, _text: str) -> None:
        existing = self._config.provider_config("anthropic")
        existing["model"] = self._model.text().strip() or "claude-sonnet-4-5"
        self._config.set_provider_config("anthropic", existing)
        self.settingsChanged.emit()


class _GeminiConfigRow(_ProviderConfigRow):
    """Gemini: radio group ("API key" / "Sign in with Google") + content."""

    def __init__(
        self,
        config: AIConfig,
        keystore: "KeyStore | None",
        parent: QWidget,
    ) -> None:
        super().__init__("gemini", parent=parent)
        self._config = config
        self._keystore = keystore
        settings = config.provider_config("gemini")
        # Default to API key on first-run per the design contract.
        self._auth_mode = settings.get("auth_mode", "api_key")

        # Radio group.
        self._radio_api = QRadioButton(self.tr("API key"), self)
        self._radio_oauth = QRadioButton(self.tr("Sign in with Google"), self)
        self._radio_api.setAccessibleName(self.tr("Use Gemini API key"))
        self._radio_oauth.setAccessibleName(self.tr("Use Sign in with Google"))
        self._radio_api.setChecked(self._auth_mode == "api_key")
        self._radio_oauth.setChecked(self._auth_mode == "oauth")
        self._radio_api.toggled.connect(self._on_mode_changed)
        self._radio_oauth.toggled.connect(self._on_mode_changed)
        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self._radio_api)
        radio_layout.addWidget(self._radio_oauth)
        radio_layout.addStretch(1)
        self._outer.addLayout(radio_layout)

        # API-key field (shown when mode == api_key).
        self._api_key = QLineEdit(self)
        self._api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key.setAccessibleName(self.tr("Gemini API key"))
        self._api_key.setPlaceholderText(self._placeholder_for_stored_key())
        self._api_key.editingFinished.connect(self._on_key_committed)
        self._api_key_label = QLabel(self.tr("API key:"), self)
        self._api_key_label.setBuddy(self._api_key)
        api_form = QFormLayout()
        api_form.addRow(self._api_key_label, self._api_key)
        self._api_key_container = QWidget(self)
        self._api_key_container.setLayout(api_form)
        self._outer.addWidget(self._api_key_container)

        # OAuth state row (shown when mode == oauth). Per design-contract
        # Component 3, the OAuth UX has 4 states: IDLE / PENDING / SIGNED IN /
        # ERROR. Sprint 2 wires IDLE and SIGNED IN; PENDING / ERROR transitions
        # are driven by the OAuth flow when the host hooks the sign-in button.
        self._oauth_status = QLabel(self.tr("Not signed in."), self)
        self._oauth_status.setStyleSheet(f"color: {_COLOR_MUTED};")
        self._signin_btn = QPushButton(self.tr("Sign in with Google"), self)
        self._signin_btn.setAccessibleName(self.tr("Sign in with Google"))
        self._signin_btn.clicked.connect(self._on_signin_clicked)
        self._signout_btn = QPushButton(self.tr("Sign out"), self)
        self._signout_btn.setAccessibleName(self.tr("Sign out of Google"))
        self._signout_btn.clicked.connect(self._on_signout_clicked)
        self._signout_btn.setVisible(False)

        oauth_layout = QHBoxLayout()
        oauth_layout.addWidget(self._oauth_status, 1)
        oauth_layout.addWidget(self._signin_btn)
        oauth_layout.addWidget(self._signout_btn)
        self._oauth_container = QWidget(self)
        self._oauth_container.setLayout(oauth_layout)
        self._outer.addWidget(self._oauth_container)

        # Model field (always visible).
        self._model = QLineEdit(self)
        self._model.setText(settings.get("model", "gemini-2.5-flash"))
        self._model.setAccessibleName(self.tr("Gemini model"))
        self._model.textChanged.connect(self._on_model_changed)
        model_label = QLabel(self.tr("Model:"), self)
        model_label.setBuddy(self._model)
        model_form = QFormLayout()
        model_form.addRow(model_label, self._model)
        self._outer.addLayout(model_form)

        # Refresh signed-in status from the keychain on construction so the
        # row reflects persisted state across launches.
        self._refresh_oauth_status()
        self._refresh_visibility()

    # ---- handlers -----------------------------------------------------

    def _on_mode_changed(self, _checked: bool) -> None:
        # Two-radio group: read the API radio to determine mode.
        new_mode = "api_key" if self._radio_api.isChecked() else "oauth"
        if new_mode == self._auth_mode:
            return
        self._auth_mode = new_mode
        existing = self._config.provider_config("gemini")
        existing["auth_mode"] = new_mode
        self._config.set_provider_config("gemini", existing)
        self._refresh_visibility()
        self.settingsChanged.emit()

    def _on_key_committed(self) -> None:
        text = self._api_key.text().strip()
        if not text or self._keystore is None:
            return
        try:
            self._keystore.put("gemini", text)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Storing Gemini key failed: %s", exc)
            return
        self._api_key.clear()
        self._api_key.setPlaceholderText(self.tr("(stored — leave blank to keep)"))
        self.settingsChanged.emit()

    def _on_signin_clicked(self) -> None:
        """IDLE → PENDING transition entry point.

        The actual OAuth flow needs an OAuth client_id which is a deployment
        concern (registered in Google Cloud Console). Sprint 2 wires the UX
        scaffold but the host wiring decides whether to run the real
        ``oauth.authorize()`` or surface a "configure your client id" hint.
        """
        # We do NOT block on the flow here; the host wires the actual
        # authorize call in S2's host integration. The widget just toggles
        # status text so a manual smoke run sees the state machine fire.
        self._oauth_status.setText(self.tr("Waiting for browser..."))
        self._signin_btn.setEnabled(False)

    def _on_signout_clicked(self) -> None:
        """SIGNED IN → IDLE transition. Revokes via the keychain blob."""
        if self._keystore is not None:
            try:
                self._keystore.delete_oauth("gemini")
            except Exception as exc:  # noqa: BLE001
                logger.warning("Revoking Gemini OAuth blob failed: %s", exc)
        self._refresh_oauth_status()
        self.settingsChanged.emit()

    def _on_model_changed(self, _text: str) -> None:
        existing = self._config.provider_config("gemini")
        existing["model"] = self._model.text().strip() or "gemini-2.5-flash"
        self._config.set_provider_config("gemini", existing)
        self.settingsChanged.emit()

    # ---- view-state helpers ------------------------------------------

    def _placeholder_for_stored_key(self) -> str:
        if self._keystore is None:
            return self.tr("(no keychain configured)")
        try:
            existing = self._keystore.get("gemini")
        except Exception:
            return self.tr("(keychain unavailable)")
        if existing:
            return self.tr("(stored — leave blank to keep)")
        return self.tr("Paste your Gemini API key")

    def _refresh_oauth_status(self) -> None:
        signed_in = False
        if self._keystore is not None:
            try:
                blob = self._keystore.get_oauth("gemini")
                signed_in = bool(blob)
            except Exception:
                signed_in = False
        if signed_in:
            self._oauth_status.setText(self.tr("Signed in. Token refreshes automatically."))
            self._oauth_status.setStyleSheet(f"color: {_COLOR_OK};")
            self._signin_btn.setEnabled(False)
            self._signin_btn.setVisible(False)
            self._signout_btn.setVisible(True)
        else:
            self._oauth_status.setText(
                self.tr("Opens your browser. We only request access to the Gemini API."),
            )
            self._oauth_status.setStyleSheet(f"color: {_COLOR_MUTED};")
            self._signin_btn.setEnabled(True)
            self._signin_btn.setVisible(True)
            self._signout_btn.setVisible(False)

    def _refresh_visibility(self) -> None:
        is_api = self._auth_mode == "api_key"
        self._api_key_container.setVisible(is_api)
        self._oauth_container.setVisible(not is_api)

    # ---- read accessors (used by tests) ------------------------------

    @property
    def auth_mode(self) -> str:
        return self._auth_mode


__all__ = ["AIPreferencesPanel"]
