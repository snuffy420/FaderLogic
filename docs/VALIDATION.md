# MixLogic 1.4.0 validation

## Application

The 57-test source suite covers both charts and all 1,152 directional pairs, accessible palettes including selection, fitted Both labels, independently rendered neighbour borders, all 36 waveform design/mode combinations, FFT bands, metadata Unknown handling, playlist persistence, relinking, ordered exports/reimports, themes, option controls and current-track preview reuse.

Native Windows screenshots cover the main UI, both charts, all five wheels, nine waveform designs, all four color modes, Dark/Light, playlist management, metadata, Options, Help, About and Donate. Screenshots use generated original audio and example metadata, never private libraries.

Packaged checks exercise startup, playlist toggling, all appearance choices, theme persistence, QR dependencies and clean shutdown in an isolated directory. Bundle inspection checks 1.4.0 application/Windows resources and rejects Qt Quick/QML dependencies and incompatible injected ICU DLLs.

## Installer and archives

The Inno x64 installer compiled successfully with the verified 1.4.0 EXE and complete payload. The included per-user setup/start/uninstall test refused to run because an existing MixLogic installation is registered on this machine; it was preserved. A live 1.4.0 install/uninstall cycle therefore remains unverified here. The test checks registration/version, full payload, installed.flag, user-profile data storage, executable removal and data retention when run on a machine without an existing registration.

Source and portable archives are integrity-tested, checked for one top-level folder and built from allowlisted files. No music, personal playlists, databases, dependency environments or old test EXEs are included. The clean source tree is prepared separately for GitHub upload. SHA-256 checksums accompany each release file.

## Contact page

Real 1280-pixel desktop and 390-pixel mobile browser viewports were checked for horizontal overflow and captured. Success/error DOM states were also checked with mocked responses; no real message was sent. tools/test_contact.mjs executes the actual script against a simulated DOM/fetch, checking success, service errors, offline/timeout paths, whitespace validation, character count and duplicate-submit protection. No real network submission or message is sent. Live Formspree delivery and GitHub Pages require the author's post-upload check.

## Platform and workflow limits

Windows x64 is the tested binary target. macOS and Linux setup commands are documented with and without a venv, but those native GUI/audio environments have not been run here. Platform wheel availability and Linux library requirements are referenced in the source guide.

File-format tests validate exact playlist order and MixLogic metadata round-trip. A real import in Rekordbox and DJ player/USB workflows remain manual checks; the project does not claim official certification. It does not render continuous mixes or transfer cue/beatgrid databases. Codec support varies by platform/backend.
