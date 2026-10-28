# Run FaderLogic from source on macOS or Linux

These instructions are for **FaderLogic 1.4.2 source**, not the Windows `.exe`. FaderLogic uses PyQt6, which supports macOS and Linux. The release is tested on Windows; macOS/Linux source operation is provided on a best-effort basis and has not been tested on those operating systems here. Audio codecs and window appearance can vary.

You do not need to be a programmer. Copy one command at a time, paste it into Terminal, then press **Enter**. Do not type the surrounding ``` marks. Keep the source folder in your own Downloads, Documents or home folder so FaderLogic can save its data.

## First: download and open the source folder

1. Download **FaderLogic-1.4.2-source.zip** (the easiest choice on macOS/Linux), or **FaderLogic-1.4.2-source.7z** from the GitHub release.
2. Extract the entire ZIP using your computer’s normal Extract/Open command. For the 7z alternative, use an archive manager that supports 7z. If your computer cannot extract it, use a 7z-capable archive app, or download the repository with **Code → Download ZIP** and extract that instead.
3. Open the extracted folder. You should see **main.py**, **requirements.txt**, **run_faderlogic.sh**, and a **faderlogic** folder. This is the folder you need below.
4. Choose **one** installation method: a virtual environment (recommended), or the no-venv app-local method. You do not need both.

**What is a venv?** A virtual environment is a private Python environment inside this app's folder. It keeps FaderLogic's packages separate from other Python programs. The no-venv method below instead puts the required packages in a `.packages` folder; it also avoids changing your system's Python packages.

## macOS

### 1. Install Python

1. Visit [python.org's macOS downloads](https://www.python.org/downloads/macos/).
2. Install a compatible **Python 3.12 or 3.13** macOS package. The current dependency versions are pinned in `requirements.txt`; the Windows release was tested with Python 3.12.
3. If the installer offers an **Install Certificates.command** helper, run it after installing. This can prevent certificate errors during package downloads.
4. Open **Terminal**: press **Command + Space**, type **Terminal**, then press Enter.
5. Type this and press Enter:

```sh
python3 --version
```

It should print a Python version. If it says `command not found`, close/reopen Terminal after installing Python. On Apple Silicon, use a Python installer that supports your Mac's architecture; avoid mixing Intel and native ARM environments.

### 2. Tell Terminal where the source folder is

Type `cd ` with a space after it, **drag the extracted source folder from Finder into Terminal**, then press Enter. The drag inserts the correct path, including any spaces.

Check the folder by running:

```sh
ls
```

You should see `main.py` and `requirements.txt`. If you do not, open the inner source folder and repeat the `cd` step.

### 3A. With a venv — recommended

Run these commands one at a time:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

The package installation needs internet access and can take a few minutes. When it finishes, the last command opens FaderLogic. The `(.venv)` prefix in Terminal means the private environment is active; it is normal.

**To open FaderLogic another day:** open Terminal in the same source folder and run:

```sh
sh run_faderlogic.sh
```

This uses the existing venv automatically. You do not need to reinstall packages or activate it every time. Close the FaderLogic window to stop the program. If you activated the venv manually, `deactivate` leaves it when you are finished.

### 3B. Without a venv — app-local packages

Do not run the venv commands above for this method. From the source folder, run:

```sh
python3 -m pip install --target .packages -r requirements.txt
sh run_faderlogic.sh --no-venv
```

The first command downloads the dependencies into `.packages` inside the source folder. The second launches FaderLogic using those packages. This is not a virtual environment and does not require activation.

**To open it again later**, return to the source folder and run:

```sh
sh run_faderlogic.sh --no-venv
```

Do not delete `.packages`, because it contains the dependencies for this method. If you switch Python versions, create a fresh source folder and reinstall its dependencies for that Python version rather than mixing old binary packages.

## Linux

### 1. Install Python and desktop dependencies

Use a recent desktop Linux system supported by the pinned Qt wheels. For the pinned Qt packages, Linux x64 needs glibc 2.34 or newer; Linux ARM64 needs glibc 2.39 or newer. Alpine/musl is not covered by these wheel instructions. See the [published Qt runtime wheels](https://pypi.org/project/PyQt6-Qt6/6.11.2/#files). A graphical desktop is required; an SSH-only terminal or bare server is not enough to display the app.

For **Ubuntu / Linux Mint / Debian**, open Terminal (often **Ctrl + Alt + T**) and run:

```sh
sudo apt update
sudo apt install python3 python3-pip python3-venv libxcb-cursor0 libxkbcommon-x11-0 libegl1
```

The computer may ask for your login password. The password does not show as you type; that is normal. Press Enter after typing it. These commands install operating-system packages, not FaderLogic itself.

Other distributions use different package managers and package names. Install Python, pip, venv support and the Qt desktop runtime dependencies through your distribution's instructions. Current Qt wheels require a sufficiently recent system C library; x64 and ARM64 wheel requirements can differ. See [Qt's Linux/X11 requirements](https://doc.qt.io/qt-6/linux-requirements.html).

Check Python:

```sh
python3 --version
```

Python 3.12 is the tested release interpreter. Use a Python version supported by the pinned dependencies; Python 3.12/3.13 are suitable choices for these instructions.

### 2. Open Terminal inside the source folder

Open the extracted folder in your file manager. If available, right-click an empty space and choose **Open in Terminal**. Otherwise, type `cd ` in Terminal, drag the folder into the Terminal window, and press Enter.

Check you are in the right place:

```sh
ls
```

You should see `main.py` and `requirements.txt`.

### 3A. With a venv — recommended

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Run each line separately. Wait for the dependency installation to finish before starting the last command.

**To launch it later**, open Terminal in the same folder and run:

```sh
sh run_faderlogic.sh
```

### 3B. Without a venv — app-local packages

From the source folder, run:

```sh
python3 -m pip install --target .packages -r requirements.txt
sh run_faderlogic.sh --no-venv
```

This puts FaderLogic's Python dependencies in `.packages`, not into the system Python installation. It does not need `sudo`, venv activation, `--break-system-packages`, or disabling your distribution's Python protections.

**To launch it later:**

```sh
sh run_faderlogic.sh --no-venv
```

If you see `externally-managed-environment`, confirm that you copied the entire installation command including `--target .packages`. The recommended venv method is another way to keep packages separate.

## Using playlists moved from another operating system

A Windows playlist can contain paths such as `D:\Music\Track.wav`; those locations do not automatically exist on macOS or Linux. Import the playlist and matching TXT file, then select **Relink Folder** and choose the actual music folder on this computer. FaderLogic recognizes Windows-style filenames during relinking and remembers the new folder.

Re-export the set after relinking so the M3U8 points to paths that exist on the computer where you will use it. The playlist does not copy the audio files.

## Where your data is saved

When running from source, `FaderLogic-data/` and `waveform_cache.db` are created beside `main.py`. Keep the entire source folder in a writable location. Back up `FaderLogic-data/` while the app is closed.

The `.venv` and `.packages` folders are dependency folders, not saved playlists. You can recreate them from `requirements.txt`; do not move dependency binaries between macOS/Linux or between different CPU architectures.

## Common problems

| Message or symptom | What to do |
| --- | --- |
| `No such file or directory: main.py` | Terminal is in the wrong folder. Repeat the `cd` / Open in Terminal step and check `ls`. |
| `No module named PyQt6` | Use the launcher for the method you installed: `sh run_faderlogic.sh` for venv, or `sh run_faderlogic.sh --no-venv` for `.packages`. |
| `No module named venv` or `ensurepip` | On Ubuntu/Mint/Debian, install `python3-venv`, then recreate `.venv`. |
| `No module named pip` | Install pip using your Python installer's or Linux distribution's instructions; do not use `sudo pip install`. |
| `Could not load the Qt platform plugin xcb` | Install the missing Qt/X11 libraries, including `libxcb-cursor0`, through the Linux package manager. This is not fixed by repeatedly reinstalling FaderLogic. |
| `No matching distribution found` | Check Python version, CPU architecture and OS age against the wheel requirements. Avoid mixing Intel and ARM installations. |
| macOS certificate error during pip install | Run the Python installer's Install Certificates helper, then retry. |
| The app opens but preview does not play | Relink the audio first. Codec/backend support can differ between operating systems; try a known-good WAV. |
| The program seems to keep Terminal busy | That is normal while the GUI is running. Close FaderLogic to return to the prompt. |

The Windows `.exe` and Windows installer do not run natively on macOS or Linux. Use the source instructions above; native Mac/Linux application bundles are not included in this release.

## Where these commands come from

The private-environment method follows [Python venv documentation](https://docs.python.org/3/library/venv.html). The app-local method uses [pip's documented --target option](https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-t), so it does not modify system Python. Available [PyQt6 runtime wheels](https://pypi.org/project/PyQt6-Qt6/6.11.2/#files) determine supported OS/CPU combinations. Native macOS and Linux GUI/audio tests have not been performed on the Windows release machine.
