# Plotwright

> **Plotwright is a fork of [novelWriter](https://github.com/vkbo/novelWriter)
> by Veronica Berglyd Olsen and contributors.** novelWriter is licensed under
> GPL-3.0-or-later; this fork is too. The two projects share editor DNA but
> have **opposing positions on AI**: upstream novelWriter is explicitly
> AI-free; Plotwright integrates optional, privacy-gated AI assistance for
> plotters. We ship with AI off by default and a network-zero regression test
> as a hard gate. See `docs/fork.md` for the full rationale and `docs/ai/`
> for the privacy and architecture stance.

## Status

Plotwright is in early development. Sprint 1 (current): fork bootstrap and
AI substrate (privacy-gated network module, provider abstraction, mock
provider, tests). No live AI features ship in Sprint 1.

Upstream baseline: see `.fork-baseline.json` for the pinned upstream commit
and rebase strategy.

## Attribution

This fork is built on novelWriter. All editor and project-format work in this
repository is the work of Veronica Berglyd Olsen and the novelWriter
contributors listed in `CREDITS.md`. AI substrate, fork branding, and the
plotter-focused redesign are fork-specific work.

## License

Plotwright is licensed under [GPL-3.0-or-later](LICENSE.md), inheriting from
novelWriter. Bundled assets retain their original licenses (Apache-2.0,
CC-BY-4.0, ISC where applicable). See `LICENSE.md` and
`setup/LICENSE-Apache-2.0.txt`.

## Upstream project links (novelWriter)

* Website: [novelwriter.io](https://novelwriter.io)
* Documentation: [docs.novelwriter.io](https://docs.novelwriter.io)
* Internationalisation: [crowdin.com/project/novelwriter](https://crowdin.com/project/novelwriter)
* PyPI: [pypi.org/project/novelWriter](https://pypi.org/project/novelWriter)
* Social Media: [fosstodon.org/@novelwriter](https://fosstodon.org/@novelwriter)

---

## About the editor (from upstream)

<img align="left" style="margin: 0 0 4px 0;" src="https://raw.githubusercontent.com/vkbo/novelWriter/main/setup/novelwriter_readme.png">

novelWriter is a plain text editor designed for writing novels assembled from many smaller text
documents. It uses a minimal formatting syntax inspired by Markdown, and adds a meta data syntax
for comments, synopsis, and cross-referencing. It's designed to be a simple text editor that allows
for easy organisation of text and notes, using human readable text files as storage for robustness.
The project format is well suited both for version control software and file synchronisation tools.

For details on the editor, see the upstream documentation linked above.

## Sponsors

<table style="border: none;">
<tr>
  <td><img align="left" style="height: 25px;" src="https://raw.githubusercontent.com/vkbo/novelWriter/main/setup/signpath_logo.png"></td>
  <td>Free code signing on Windows provided by <a href="https://about.signpath.io/">SignPath.io</a>, certificate by <a href="https://signpath.org/">SignPath Foundation</a>.</td>
</tr>
</table>


## Implementation

novelWriter is written in Python and uses Qt6 with PyQt6 Python binding as the UI framework. It is
released on Linux, Windows and MacOS. It can in principle run on any Operating System that also
supports Qt, PyQt and Python.

<p align="center">
  <img width="80%" src="https://raw.githubusercontent.com/vkbo/novelWriter/main/setup/screenshot.png">
</p>


## Project Contributions

Please don't make feature pull requests without first having discussed them with the maintainer.
You can make a feature request in the [issues tracker](https://github.com/vkbo/novelWriter/issues),
or if the idea isn't fully formed, start a [discussion](https://github.com/vkbo/novelWriter/discussions).
Please also don't make pull requests to reformat or rewrite existing code unless there is a very
good reason for doing so. Please do not submit AI generated content.

Fixes and patches are welcome. Contributions related to packaging and installing novelWriter will
also be appreciated, but please make an issue or a discussion topic first. Before contributing any
code, please also read the full
[Contributing Guide](https://github.com/vkbo/novelWriter/blob/main/CONTRIBUTING.md).

Project credits are available in [CREDITS.md](https://github.com/vkbo/novelWriter/blob/main/CREDITS.md).

**Note:** New features and pre-releases are made on the `main` branch. Full releases are made from
the `release` branch. So if you're submitting a fix to a current release, **including changes to
documentation**, they must be made to the `release` branch.


### Translations

New translations are always welcome. This project uses Crowdin to maintain translations, and you
can contribute translations at the [Crowdin project page](https://crowdin.com/project/novelwriter).
If you have any questions, feel free to post them to the
[Translations of novelWriter](https://github.com/vkbo/novelWriter/issues/93) issue thread.


## Licence

This is Open Source software, and novelWriter is licenced under GPLv3. See the
[GNU General Public License website](https://www.gnu.org/licenses/gpl-3.0.en.html) for more
details, or consult the [License](https://github.com/vkbo/novelWriter/blob/main/LICENSE.md)
document. Bundled assets and their licences are listed in the
[Credits](https://github.com/vkbo/novelWriter/blob/main/CREDITS.md) document.
