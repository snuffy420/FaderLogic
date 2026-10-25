# MixLogic 1.3.0 validation

## Automated coverage

Run `python -m unittest discover -s tests -v`. The current suite contains **26 tests**, covering:

- Both supplied relation charts: all 24 starting keys and all 24 destination keys, **1,152 directional pairs** in total. Listed chart cells, alternatives, unlisted pairs and directional differences are checked.
- M3U8 order and repeated tracks, absolute/relative paths, local file URLs, UTF-8 BOM input, punctuation/non-ASCII filenames and missing-file handling before overwrite.
- Current exported sets reopening with complete example metadata and exact order, without a TXT prompt.
- UTF-16 BOM, UTF-16 LE/BE and UTF-8 TXT decoding.
- Saved-source copies, last-playlist/session restore, update-without-duplicate imports, rename/removal, cancelled/failed imports and earlier database-schema migration.
- Per-playlist folder restore/reuse, relinking set references without order changes, and retained source metadata after the original export files are removed.
- Real header boundary dragging, panel-size persistence, independent column visibility and the last-visible-column guard.
- Set-track preview, chart changes, selection preservation, filtering and reordering.
- Themed message/rename windows and a BTC copy confirmation that does not resize the dialog.
- A single main title/header row, aligned right-panel footer, active relink styling and Playlists toggle persistence.

## Compiled application

`python tools/smoke_test_exe.py dist/MixLogic.exe` runs a copied executable with temporary state and the offscreen Qt backend. It checks startup, both directions of the playlist-browser toggle, Options/column controls and About donation/QR dependencies.

`python tools/check_bundle.py` verifies the packaged version and feature modules, rejects the incompatible third-party ICU DLL names associated with the earlier QtGui startup failure, and checks the Windows version resource.

## Layout and screenshots

The 1.3.0 UI was checked at **150% display scaling**, with the browser open and closed at **1100 × 700**, **1280 × 700**, and **1480 × 920**. The default smaller layouts retain at least four complete rows per table. Public screenshots are generated from the current Qt UI using temporary demo WAV audio and example metadata, not private libraries or commercial music.

## Manual checks kept separate

These automated checks do not establish official compatibility certification by Rekordbox/AlphaTheta. A live import into the Rekordbox desktop application, subjective audio review and real DJ/player/USB workflows remain manual checks. The official Rekordbox manual documents M3U8 playlist import via File → Import → Import Playlist.

Playlist round-trip tests verify MixLogic's file output and reimport behaviour. They do not export a USB database, transfer Rekordbox cues/beatgrids, render transitions or test every codec/hardware combination.
