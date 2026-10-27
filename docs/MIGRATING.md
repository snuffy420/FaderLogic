# Moving from earlier test builds to FaderLogic

The public application is named **FaderLogic**, version **1.4.0**. Earlier private builds used the name MixLogic.

## Existing exported sets

Use **Import Playlist** to choose an M3U8 exported by either name. FaderLogic recognizes both versions of the embedded metadata and does not ask for a TXT file. Track order, repeated tracks, metadata and Unknown values are retained. Audio still needs to be available at the referenced paths; use **Relink Folder** if it has moved.

New exports use FaderLogic metadata comments alongside standard M3U8 entries. Other playlist readers can ignore these comments. Keep the audio files with your music collection; playlists do not contain audio.

## Portable or source updates

1. Close the older program.
2. Back up its **MixLogic-data** folder. This contains your saved library and preferences.
3. Extract the complete new portable folder, or source folder. Do not run it from inside the archive.
4. Copy **MixLogic-data** into the folder containing **FaderLogic.exe** or **main.py**.
5. Start FaderLogic. When no **FaderLogic-data** folder exists, it copies the older library and saved source exports into a new **FaderLogic-data** folder.
6. Check your saved playlists, linked folders, active set and preferences.

The original folder remains unchanged. An existing FaderLogic-data folder always takes priority, so subsequent launches do not overwrite your edits. The waveform cache can be regenerated and does not need to be copied.

## Installed updates

The installer uses **Program Files\FaderLogic** by default and writes saved data under **%LOCALAPPDATA%\FaderLogic\FaderLogic-data**. It has its own Add/Remove Programs entry.

On first launch, when its new library is absent, the installed app looks for **%LOCALAPPDATA%\MixLogic\MixLogic-data**, copies the saved library and source exports, and leaves the previous data intact. Close the older program before switching. A portable library is not imported from an arbitrary location automatically; use the portable-copy steps above or import its exported sets.

Uninstalling FaderLogic removes the program and its shortcuts while retaining its saved data. The new installer does not uninstall an earlier test build under the previous name.

## Repository and contact links

The release documentation targets **https://github.com/snuffy420/FaderLogic**. Rename or create that repository before uploading. Enable GitHub Pages from **main / (root)** for **https://snuffy420.github.io/FaderLogic/docs/contact.html**. The contact form keeps the same owner-provided Formspree endpoint.
