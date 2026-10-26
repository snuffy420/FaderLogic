# Changelog

## 1.4.0 — 2026-10-26

First public release. Earlier 1.x versions were local development/test builds.

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
- Include optional MixLogic metadata comments so its exported sets reopen with titles, artists, BPM, keys, duration and order without another TXT file.
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
- Support Normal, RGB, 3-band and MixLogic original-color modes on every design.
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
- Add a MixLogic-themed Formspree contact page, a local SVG README button and GitHub Pages setup instructions.
- Provide detailed Windows, macOS and Linux source setup, including venv and app-local non-venv methods for macOS/Linux.
- Package Windows x64 portable files inside a nested MixLogic folder, plus source ZIP and 7z archives.
- Provide a dark logo-themed Inno x64 installer with Program Files default, uninstaller, Add/Remove Programs entry, Start menu and optional desktop shortcut.
- Store installed app data under the user's profile and preserve it on uninstall; retain portable data alongside the portable app.
- Include GPL-3.0-or-later licensing, third-party notices and exact dependency provenance/license manifests.
- Include public screenshots/galleries, 57 source tests, browser-free contact-script tests, build/installer checks and SHA-256 release manifests.

Windows x64 is tested. Native macOS/Linux GUI and audio behavior, live Formspree delivery after Pages publication, and end-to-end Rekordbox/device workflows remain separate manual checks described in the documentation.
