# Changelog

## 1.4.2 - 2026-10-28

- Release the wheel filtering, Behavior sorting controls and detailed waveform introduced in the 1.4.1 review build.
- Center the active key-filter control immediately beneath the wheel and reserve its height and width while hidden, keeping the wheel, tables and footer stable when a key is selected or cleared.
- Replace the sorting-option descriptions with short, generic explanations. Keep detailed supported-prefix examples in Help.
- Refresh the README, in-app Help, appearance/source/build/publishing guides and screenshots for 1.4.2. Preserve beginner macOS/Linux setup with and without virtual environments.
- Provide the themed Windows x64 installer, portable ZIP and 7z, source ZIP and 7z, SHA-256 checksums and a clean GitHub upload folder. Both portable formats contain a nested FaderLogic folder.
- Add a geometry regression check for the centered filter control and an unchanged workspace across filter toggles.

## 1.4.1 test build - 2026-10-28

- Add an Options → Behavior tab with independent, saved choices to ignore leading punctuation and track-number prefixes in library Title sorting. Both default off; disabling both retains literal sorting.
- Recognize zero-padded counters with spaces and short numeric prefixes with explicit separators. Preserve meaningful numeric titles, displayed metadata, filenames and audio paths.
- Make the actual highlighted Camelot wedges clickable in every wheel design and both relation charts. Filter the library to the clicked exact A/B key without replacing its reference track or changing harmonic relationship colors.
- Mark the active filter with a brighter wedge fill, white dashed inset and white dot, including the colour-blind design. Click the wedge again or the clear button to restore the list while respecting text search.
- Combine key filters with search and sorting, show a clear empty state, and clear key filters when switching saved playlists. Prevent adding a reference track hidden by a filter.
- Preserve built-set order and exact-order M3U8 exports throughout sorting/filtering.
- Add Detailed audio waveform: a continuous signed peak envelope built from 4096 measured sub-bins, retaining short transients and quiet sections. Aggregate peaks to display pixels instead of dropping them.
- Support Normal, measured RGB, shared-centreline 3-band and original-colour modes for the new waveform. Retain all previous non-3D designs and separate-lane Split bands options.
- Retain background decoding, interruption of obsolete work and cached painting. Store finer analysis in a new waveform cache table; existing cached overviews refresh once.
- Regenerate the offline dance preview with the same fine PCM envelope as decoded tracks. Keep Options previews on the same renderer and loaded-track data as the main display.
- Expand in-app Help and README with workflow examples, exact sorting formats, filter indicators and clearing, waveform modes and actual limitations.
- Provide a local Windows test EXE first. Public GitHub archives and installer are unchanged pending testing.

## 1.4.0 — 2026-10-27

First public release. Earlier 1.x versions were local development/test builds.

### Public name and compatibility

- Rename the application from its private-test name MixLogic to FaderLogic. Keep version 1.4.0.
- Update the window titles, tooltips, Help, About, export filenames, waveform labels, icons' filenames, source package, launchers, Windows executable metadata, installer, shortcuts, documentation, screenshots and contact page.
- Write new FaderLogic metadata comments in exported M3U8 files while continuing to read older MixLogic exports without requiring a TXT file. Track order, duplicates and Unknown values are preserved.
- Copy a previous portable/source library beside the app to FaderLogic-data on first launch, including saved source exports, linked folders, sets and preferences. Leave the original library intact and never merge over an existing FaderLogic library.
- Discover the previous installed user-data folder when starting the installed FaderLogic copy. Use a consistent SQLite backup, including committed WAL data, and check the copy before activating it.
- Preserve the original waveform color preference when restoring a pre-rename session.
- Give FaderLogic its own installer registration, Program Files folder, Start menu entries and optional desktop shortcut. Retain user data after uninstall.

### Rekordbox import, library and session

- Import matching Rekordbox M3U8/TXT exports, retaining source copies and declared track metadata.
- Read UTF-16 and UTF-8 TXT input, Windows/Unix-style paths and supported audio extensions.
- Save multiple libraries in a searchable, collapsible playlist browser with rename/remove controls.
- Remember each playlist's linked audio folder; relink nested music folders and show the configured-folder highlight.
- Reimport matching source pairs without repeatedly creating the same library; retain a chosen name and folder.
- Restore the previous library, preview selection, active set, panel/column sizes and preferences. Playback stays stopped on startup.
- Keep the active set while changing libraries, allowing sets assembled from multiple playlists.

### Set building and exact-order export

- Add, reorder, remove and clear tracks; confirm duplicate additions and replacement of an existing set when needed.
- Export standard UTF-8 M3U8 with the exact set order, including repeated tracks.
- Include optional FaderLogic metadata comments so its exported sets reopen with titles, artists, BPM, keys, duration and order without another TXT file.
- Check missing audio paths before export. Audio files and embedded tags are not modified or bundled with the playlist.
- Calculate estimated set length from track durations and the selected Transition Time overlap.
- Use explicit Unknown fields and Unknown total length when required duration metadata is missing.

### Metadata accuracy

- Never substitute guessed keys or BPM values for unavailable or unverifiable metadata.
- Display Unknown consistently in Title, Artist, BPM, Camelot, Key and Time in both tables when those fields are missing/invalid.
- Provide ! row markers and field tooltips, including when optional columns are hidden.
- Provide an optional bounded Metadata details table instead of intrusive import popups or a permanent warning banner.
- Keep known metadata intact and treat unknown keys neutrally in compatibility displays.

### Harmonic mixing and the wheel

- Include two directional relation charts covering all 24 Camelot keys: Chart 1 energy boost/drop and Chart 2 harmonic transitions.
- Update the wheel, details and Relation to last when selecting a track in either table.
- Keep five non-3D designs: Classic, Obsidian Neon, Dark Minimal, Neon Outline and Colour-blind.
- Preserve the original standard key/relation palettes across designs and both themes.
- Show the selected Camelot code and musical key in every wheel's center.
- Offer Camelot number, musical key and Both labels, plus grouped or detailed relation highlighting.
- Give each wedge its own inset border and isolated inner/outer glow area, so neighbouring outlines retain their own colors.
- Dim unlisted keys clearly and explain the active chart with a live legend separated by | dividers.
- Add color-blind relation colors, patterns, text codes, selected white double outlines and a blue same-key perfect-match indication.
- Fit accessible Both labels on separate number/key/relation rows and explain both charts independently in Help.
- Remove all experimental 3D scenes and runtime dependencies to keep startup and interaction responsive.

### Waveforms and auditioning

- Preview selected tracks through toolbar Play/Pause and Stop controls with distinct cyan/red styling.
- Decode/analyze audio in cancellable background workers and cache the measured overview.
- Coalesce rapid browsing requests, cancel stale work and keep PCM memory compact.
- Seek by clicking or dragging in any waveform design.
- Offer nine designs: Classic bars, Enhanced glow bars, Smooth filled, Spectrogram, Multilayer, Energy segments, Minimal glow line, Split bands bars and Split bands ribbons.
- Support Normal, RGB, 3-band and FaderLogic original-color modes on every design.
- Use shared-center blue/orange/white 3-band display; reserve separate lanes for explicitly named Split bands designs.
- Retain original overlapping cyan/orange/pink Classic bars as a saved option.
- Use measured FFT bands/frequency bins for spectral views; energy labels describe measured intensity rather than guessed song sections.
- Preview a copy of the loaded track's actual waveform data, playhead and display height in Appearance.
- Bundle an original dance example generated offline with the same 256-bin overview analyzer for use when no waveform is loaded.
- Display the exact loading text Analyzing Waveform.

### Interface and preferences

- Offer saved Dark and Light themes, local Appearance previews and explicit Apply for design/theme changes.
- Redesign Wheel settings with clickable sample cards, clear radio indicators, chart descriptions and a live preview.
- Redesign Table columns with aligned alternating rows, field descriptions, visible counts and themed checkmarks.
- Independently hide/show columns in Library and Set builder, retaining at least one visible column.
- Resize columns and the library/set divider; remember their sizes.
- Keep appearance hints to one elided line so descriptions do not move the preview panel.
- Consolidate the top toolbar, relocate transport controls, reduce footer clutter and place Search beside Transition Time.
- Use app-themed popup headers/icons, stationary track details and consistent rename/relink dialogs.

### Help, contact, licensing and distribution

- Include expanded About/Help, playlist guidance for the saved-library system, both chart/color explanations and source-installation guides.
- Include optional Bitcoin support with QR, Copy BTC address and a stable confirmation area.
- Add a FaderLogic-themed Formspree contact page, a local SVG README button and GitHub Pages setup instructions.
- Provide detailed Windows, macOS and Linux source setup, including venv and app-local non-venv methods for macOS/Linux.
- Package Windows x64 portable files inside a nested FaderLogic folder, plus source ZIP and 7z archives.
- Provide a dark logo-themed Inno x64 installer with Program Files default, uninstaller, Add/Remove Programs entry, Start menu and optional desktop shortcut.
- Store installed app data under the user's profile and preserve it on uninstall; retain portable data alongside the portable app.
- Include GPL-3.0-or-later licensing, third-party notices and exact dependency provenance/license manifests.
- Include public screenshots/galleries, 57 source tests, browser-free contact-script tests, build/installer checks and SHA-256 release manifests.

Windows x64 is tested. Native macOS/Linux GUI and audio behavior, live Formspree delivery after Pages publication, and end-to-end Rekordbox/device workflows remain separate manual checks described in the documentation.
