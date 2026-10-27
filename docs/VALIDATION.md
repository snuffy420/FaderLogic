# FaderLogic 1.4.0 validation

## Application

Verified on Windows x64 on **2026-10-27**: all **64 source tests passed**, the rebuilt FaderLogic executable passed native Windows startup/Options/theme/QR checks, and its bundle and version resources passed inspection.

The source suite covers both charts and all 1,152 directional pairs, accessible palettes including selection, fitted Both labels, independently rendered neighbour borders, all 36 waveform design/mode combinations, FFT bands, metadata Unknown handling, playlist persistence, relinking, ordered exports/reimports, themes, option controls and current-track preview reuse. Rebrand checks cover both playlist headers, direct import without a TXT prompt, migration of source/portable and installed libraries, committed SQLite WAL state, original-folder preservation and restoration of the previous waveform-mode preference.

Native Windows screenshots cover the main UI, both charts, all five wheels, nine waveform designs, all four color modes, Dark/Light, playlist management, metadata, Options, Help, About and Donate. Screenshots use generated original audio and example metadata, never private libraries.

Packaged checks exercise startup, playlist toggling, all appearance choices, theme persistence, QR dependencies and clean shutdown in an isolated directory. Bundle inspection checks 1.4.0 application/Windows resources and rejects Qt Quick/QML dependencies and incompatible injected ICU DLLs.

## Installer and archives

The FaderLogic 1.4.0 installer passed the complete isolated per-user installation, Add/Remove Programs registration, payload comparison, installed startup, user-profile data storage, uninstall and saved-data retention checks. An earlier MixLogic installation was not modified. Final Program Files installation and optional desktop shortcut placement remain available for the author's manual check.

The Inno x64 installer includes the verified 1.4.0 EXE and complete payload. Its separate FaderLogic installer identity keeps it independent of earlier test installations. The included per-user setup/start/uninstall test checks registration/version, full payload, installed.flag, user-profile data storage, executable removal and data retention when run on a machine without an existing FaderLogic registration. It refuses to modify an existing installation with that identity.

Source and portable archives are integrity-tested, checked for one top-level folder and built from allowlisted files. No music, personal playlists, databases, dependency environments or old test EXEs are included. The clean source tree is prepared separately for GitHub upload. SHA-256 checksums accompany each release file.

## Contact page

Real 1280-pixel desktop and 390-pixel mobile browser viewports were checked for horizontal overflow and captured. Success/error DOM states were also checked with mocked responses; no real message was sent. tools/test_contact.mjs executes the actual script against a simulated DOM/fetch, checking success, service errors, offline/timeout paths, whitespace validation, character count and duplicate-submit protection. No real network submission or message is sent. Live Formspree delivery and GitHub Pages require the author's post-upload check.

## Platform and workflow limits

Windows x64 is the tested binary target. macOS and Linux setup commands are documented with and without a venv, but those native GUI/audio environments have not been run here. Platform wheel availability and Linux library requirements are referenced in the source guide.

File-format tests validate exact playlist order and FaderLogic metadata round-trip. A real import in Rekordbox and DJ player/USB workflows remain manual checks; the project does not claim official certification. It does not render continuous mixes or transfer cue/beatgrid databases. Codec support varies by platform/backend.
