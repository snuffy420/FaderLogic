# Publishing MixLogic 1.4.0

These tools prepare local artifacts. Nothing has been uploaded or published to GitHub.

## Upload the repository

1. Open the clean GitHub/MixLogic-1.4.0 folder (use the highest numbered suffix if packaging was repeated).
2. Upload **its contents** into https://github.com/snuffy420/MixLogic at the repository root. Include .github, .gitignore, .gitattributes and .nojekyll. Do not add the outer version folder itself.
3. Check README.md, the screenshot galleries and docs/contact.html. The source tree excludes personal playlists, database files, music, test EXEs and old build output.
4. Create a release tagged **v1.4.0**, titled **MixLogic 1.4.0**. Use docs/RELEASE_NOTES_1.4.0.md for the description; replace its relative documentation links with repository URLs in the GitHub Release editor.
5. Attach the four 1.4.0 release files from releases/: setup.exe, portable.7z, source.zip and source.7z. Add their .sha256 sidecars and SHA256SUMS.txt. The .sha files contain the same SHA-256 values if you prefer that extension.
6. Verify the versioned download links in the README after publishing. Binaries belong in Releases, not source commits.

## Enable the contact page after verification

1. Repository **Settings → Pages**.
2. Choose **Deploy from a branch**, select **main** (or your actual source branch), then **/(root)**. Save.
3. Wait for deployment. Open **https://snuffy420.github.io/MixLogic/docs/contact.html**.
4. Confirm your Formspree recipient is verified and the endpoint permits this domain. Perform your own real-message check after publishing.

The README's local SVG contact button links to that URL. The page uses assets/mixlogic.png relative to the repository root; publishing only /docs would change the URL and omit the root assets. Use /(root) as described. No Pages deployment has been performed locally.

## Portable folder and updates

The portable archive contains one top-level MixLogic folder. After use it holds MixLogic-data and waveform_cache.db alongside the EXE. The distributed archive starts clean. Keep a user's MixLogic-data when updating, and do not publish your own populated portable folder.

The installer defaults to Program Files, provides Add/Remove Programs registration, Start menu entries and an optional desktop icon. Installed app data goes to %LOCALAPPDATA%\MixLogic and survives uninstall. The installed.flag marker is included only in installed copies, not portable archives.

## Verification

See [VALIDATION.md](VALIDATION.md). The archive contents, links, app version, clean data state and checksums are checked locally. macOS/Linux GUI/audio testing and an import into your installed Rekordbox remain manual checks.

## Dependency source and redistribution

Keep `LICENSE`, `COPYRIGHT`, `THIRD_PARTY_NOTICES.md` and `licenses/` with the release. MixLogic's application code and original graphics are GPL-3.0-or-later, as selected by its author.

The application source archive is provided with the executable. It is **not** a full corresponding-source mirror of Python, PyQt, Qt, FFmpeg, Pillow or their bundled libraries. The exact runtime versions, available license texts, upstream source locations and FFmpeg build configuration/hashes are recorded in the notices and manifest.

When distributing binaries, provide the dependency corresponding sources/build materials and preserve user rights as required by their applicable GPL/LGPL and other licenses. Arrange that distribution for the exact dependency binaries you publish. A list of upstream links and copied license texts does not by itself replace all corresponding-source obligations.

Relevant upstream references include [Riverbank's PyQt licensing](https://www.riverbankcomputing.com/software/pyqt/), [Qt licensing](https://doc.qt.io/qt-6/licensing.html), [Qt's third-party notices](https://doc.qt.io/qt-6/licenses-used-in-qt.html), and [FFmpeg 7.1.5 source](https://github.com/FFmpeg/FFmpeg/tree/n7.1.5).
