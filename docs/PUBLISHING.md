# Publishing MixLogic 1.3.0

The release tools prepare local files. They do not create a remote GitHub repository, upload files or publish a release.

## Source repository

`GitHub/MixLogic-1.3.0/` contains the clean upload tree. Upload **its contents** at your repository root; avoid adding an extra enclosing version directory to the repository.

The tree includes application code, tests, pinned requirements, assets, versioned screenshots, release tools, documentation and license notices. Personal playlists, databases, generated audio, test executables, backups and build output are excluded.

1. Create or choose the repository in your own GitHub account.
2. Commit the clean source files on your chosen branch.
3. Push to that repository using its actual remote URL.
4. Create a release tagged **v1.3.0**, titled **MixLogic 1.3.0**.
5. Paste `docs/RELEASE_NOTES_1.3.0.md` into the release description and link the full changelog.
6. Attach both `.7z` files, their `.sha256` and `.sha` sidecars, and `SHA256SUMS.txt` from `releases/`.
7. Preview the README/screenshots and verify that the release's source archive matches the published binary.

Executable archives belong in GitHub Releases, not regular source commits. Keep the README's versioned screenshot paths intact when uploading the repository.

## Portable folder and upgrades

The portable archive contains a top-level **MixLogic/** folder. This keeps `MixLogic.exe`, its documentation and the runtime-created `MixLogic-data/` / `waveform_cache.db` together after extraction.

The distributed archive starts clean. To update an existing user installation, close the app and retain the user's `MixLogic-data/` folder while replacing the executable. Do not publish a copy of your own populated portable folder.

## Validation before publishing

Source, layout, chart and packaged startup checks are documented in [VALIDATION.md](VALIDATION.md). Complete a manual import into your installed Rekordbox and audition representative files as an end-user compatibility check. The project does not claim official certification or affiliation.

## Dependency source and redistribution

Keep `LICENSE`, `COPYRIGHT`, `THIRD_PARTY_NOTICES.md` and `licenses/` with the release. MixLogic's application code and original graphics are GPL-3.0-or-later, as selected by its author.

The application source archive is provided with the executable. It is **not** a full corresponding-source mirror of Python, PyQt, Qt, FFmpeg, Pillow or their bundled libraries. The exact runtime versions, available license texts, upstream source locations and FFmpeg build configuration/hashes are recorded in the notices and manifest.

When distributing binaries, provide the dependency corresponding sources/build materials and preserve user rights as required by their applicable GPL/LGPL and other licenses. Arrange that distribution for the exact dependency binaries you publish. A list of upstream links and copied license texts does not by itself replace all corresponding-source obligations.

Relevant upstream references include [Riverbank's PyQt licensing](https://www.riverbankcomputing.com/software/pyqt/), [Qt licensing](https://doc.qt.io/qt-6/licensing.html), [Qt's third-party notices](https://doc.qt.io/qt-6/licenses-used-in-qt.html), and [FFmpeg 7.1.5 source](https://github.com/FFmpeg/FFmpeg/tree/n7.1.5).
