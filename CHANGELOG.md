# Changelog

## 1.3.0 — 2026-10-25

This release consolidates the improvements made since 1.1.3, including the 1.2.x development builds and the final 1.3.0 test build.

### Saved playlists and portable sessions

- Added a collapsible **Playlists** browser with search, quick switching, import, rename and removal.
- Save each imported Rekordbox M3U8/TXT pair and its parsed track metadata locally; reopening a saved playlist no longer requires finding the original export files again.
- Reimporting the same file pair updates its saved entry while retaining its chosen name and linked music folder.
- Added a dedicated `MixLogic-data` directory beside the executable, containing the SQLite catalogue/session and saved source copies.
- Restore the last playlist, selected preview track, current set and exact set order on startup.
- Restore the relation chart, wheel label mode, variation highlighting, transition overlap, browser visibility, column visibility, custom column widths and table panel heights.
- Switching source playlists keeps the current set intact, allowing tracks from several libraries to be combined.
- Removing a browser entry keeps the original music and retained source-export copies.
- Added automatic migration from the initial saved-playlist database schema without discarding existing playlists or sessions.
- Sessions save automatically with a short debounce and flush on normal close. Save failures are reported rather than silently discarding the session.

### Linked music folders

- Each saved playlist now retains its own music-folder selection and resolved audio paths.
- The Relink Folder picker starts from the playlist's saved folder.
- Reimported source playlists reuse their remembered folder for matching tracks.
- Relinking updates matching tracks already in the current set, preserving order and duplicates.
- Display the active playlist's music folder in the browser and in tooltips.
- Relink Folder is enabled when a library is loaded and uses an active highlight when a folder is configured.

### Main window and track tables

- Replaced duplicate small title-bar branding with one compact, draggable toolbar/header containing the larger logo, app name, version and window controls.
- Moved the toolbar to the top of the window, retaining minimize, maximize/restore and close controls.
- Increased the space available to the Camelot wheel by sizing its column against the workspace height and the track tables' minimum width.
- Shortened the right-side table area horizontally, reduced table/footer text, tightened row spacing, and removed the redundant Imported Library and Set Builder headings.
- Retained at least four complete rows per table at the supported minimum window size; default layouts used in validation show six rows at 1100 × 700.
- Removed the scrolling/repeated ticker. Selected-track details now stay on one line, with long content available on hover.
- Added a dedicated, always-visible **Relation to last** label so long track titles cannot hide the transition information.
- Moved Play and Stop into the toolbar, centered between Export and Options, with cyan Play/Pause and red Stop styling.
- Moved Search library below the right panel and renamed Mix time to **Transition Time**.
- Made every table column interactive, including Title and Artist, and added a draggable divider between the two tables.
- Added **Options → Table columns** with independent visibility checkboxes for each table; at least one column remains visible.
- Removed the old **Open MixLogic Set (.m3u8)** toolbar button in favour of saved playlists, session restore and direct reimport of current exports.
- Fixed the set table's missing musical-key value and displaced duration cell; all seven columns are now populated and tinted correctly.

### Selection, preview and relations

- Selecting a track in either table updates the Camelot wheel, library compatibility colours, track details and playback preview.
- Set selection remains available to Move Up, Move Down and Remove, and the same previewed track is retained while reordering.
- Avoid restarting playback or rebuilding a waveform just because the same track is moved within the set.
- Re-clicking an already-selected row can switch the preview back to that table.
- Library filtering can preserve a selected set track as the preview reference.
- Waveform results now follow the current preview source, including set tracks.
- Switching charts recomputes the wheel, relation label and table colours in place without resetting the selected track or interrupting playback.
- Clear stale wheel relation details when the selected key changes.
- Verified all 24 starting-key rows of each supplied chart, including Chart 1's parenthesized alternatives and unlisted key pairs.
- Renamed Chart 2 to **Harmonic Transitions**, keeping its relation mappings unchanged; saved Chart 2 preferences migrate to the new name.

### Export, encoding and reopening sets

- Export UTF-8 Extended M3U8 playlists with standard `#EXTM3U` / `#EXTINF` entries and absolute native audio paths.
- Preserve the exact set order and repeated tracks; library sorting/filtering does not affect export.
- Check for missing audio and invalid paths before writing, so a missing-file failure does not replace an existing playlist.
- Resolve imported relative audio paths against the original playlist's directory, rather than the application's working directory.
- Support local file URLs, percent-encoded paths, UTF-8 BOM input and filenames containing spaces, punctuation or non-ASCII characters.
- Write the actual available duration, falling back to the saved time string or an unknown-duration value instead of an arbitrary export duration.
- Keep EXTINF display metadata on one line when imported tags contain line breaks.
- Include optional MixLogic metadata comments so current exported sets reopen directly with titles, artists, BPM, keys, times and order, without a separate TXT file.
- Reopening an exported set restores it to the lower table for editing, with confirmation before replacing a non-empty current set.
- Corrected TXT encoding detection so UTF-8 files are not accidentally decoded as UTF-16. Added coverage for UTF-16 BOM, UTF-16 LE/BE and UTF-8 variants.
- Clarified that Rekordbox TXT exports use UTF-16 while M3U8 remains UTF-8.

### Dialogs, About, Help and donations

- Replaced native message/rename windows with app-styled frameless dialogs using the shared title bar and MixLogic icon.
- Replaced the generic information icon in messages with the app icon.
- Expanded About with a clearer product description, saved-library workflow, harmonic planning, export/editing overview and creator credits.
- Updated Help for saved playlists, remembered folders, session restore, either-table preview, Transition Time, adjustable tables, column visibility and reopening exports.
- Explicitly separated the default table-row colour legend from wheel dimming/outlines and per-variation highlighting.
- Added a centered **Copy BTC address** button under the donation address.
- Added a reserved confirmation footer; copying and clearing the status do not resize or reflow the dialog.

### Build, release and validation

- Fixed the QtGui startup failure caused by an incompatible ICU DLL being collected from an unrelated build-machine tool. Dependency discovery uses Windows system paths and rejects unexpected bundled ICU libraries.
- Added a frozen-executable smoke test covering startup, the Playlists toggle, Options and donation/QR dependency loading.
- Added a Windows version resource for the public executable: MixLogic 1.3.0, zerØ software.
- Added pinned runtime/build dependency files, source launch/setup helpers and reproducible release tools.
- Added current versioned screenshots, a detailed README, release notes, building/publishing instructions, third-party notices and GPL-3.0-or-later licensing.
- Public distribution includes nested-folder portable and source `.7z` archives, SHA-256 sidecars (`.sha256` and `.sha`), `SHA256SUMS.txt`, and a clean GitHub upload tree.
- Release packaging excludes saved personal playlists, settings, waveform databases, generated demo audio, old test executables and local backups.
- All 26 automated regression tests pass. Validation includes the 1,152 directional key pairs across the two charts, real column dragging, session/database migration, Unicode paths, export/reimport order, set preview/reordering and fixed-size BTC confirmation.
- Checked the UI at 150% scaling, with the browser open and closed at 1100 × 700, 1280 × 700 and 1480 × 920. Public screenshots use generated demo audio and example metadata.

### Current scope

- Windows x64 and Rekordbox-oriented playlist workflows are the release focus. There is no Denon/Serato-specific integration.
- MixLogic exports playlists, not rendered audio mixes or Rekordbox USB/device databases.
- Live desktop import in Rekordbox and subjective audio/transition review remain manual validation steps; see `docs/VALIDATION.md`.
