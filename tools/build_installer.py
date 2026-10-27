"""Compile the themed x64 installer using a separately installed/portable Inno Setup 7."""
from pathlib import Path
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from build_release import copy_docs, verify_clean_tree
from faderlogic import __version__
from PIL import Image, ImageDraw, ImageFont


def branding():
    logo = Image.open(ROOT / "assets/faderlogic.png").convert("RGBA")
    side = Image.new("RGB", (328, 628), "#16181C")
    draw = ImageDraw.Draw(side)
    def font(size, bold=False):
        path = Path("C:/Windows/Fonts") / ("segoeuib.ttf" if bold else "segoeui.ttf")
        return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()
    side.paste(logo.resize((150, 150)), (89, 55), logo.resize((150, 150)))
    title_font = font(49, True)
    title_width = draw.textbbox((0, 0), "FaderLogic", font=title_font)[2]
    draw.text(((328-title_width)//2, 235), "FaderLogic", font=title_font, fill="#E4E7EC")
    draw.text((42, 305), __version__, font=font(28), fill="#00E5FF")
    draw.text((42, 385), "Your next set,\nin the right order.", font=font(25), fill="#E4E7EC", spacing=9)
    for index, height in enumerate((18, 36, 54, 30, 70, 42, 56, 22, 48, 32, 62, 26)):
        x = 42 + index * 20
        draw.rounded_rectangle((x, 565-height//2, x+10, 565+height//2), radius=5,
                               fill="#00E5FF" if index % 2 else "#39FF88")
    side.save(ROOT / "assets/installer-side.bmp")
    small = Image.new("RGB", (110, 110), "#16181C")
    icon = logo.resize((96, 96))
    small.paste(icon, (7, 7), icon)
    small.save(ROOT / "assets/installer-small.bmp")


def main():
    branding()
    compiler = os.environ.get("INNO_ISCC") or shutil.which("ISCC.exe")
    for candidate in (ROOT / ".build-tools/InnoSetup/ISCC.exe", Path("C:/Program Files (x86)/Inno Setup 7/ISCC.exe"), Path("C:/Program Files/Inno Setup 7/ISCC.exe")):
        if not compiler and candidate.is_file():
            compiler = str(candidate)
    if not compiler:
        raise SystemExit("Install Inno Setup 7, or set INNO_ISCC to its ISCC.exe path.")
    payload_root = (ROOT / "build/installer-payload").resolve()
    if not payload_root.is_relative_to((ROOT / "build").resolve()):
        raise RuntimeError("Invalid payload staging path")
    if payload_root.exists():
        shutil.rmtree(payload_root)
    payload = payload_root / "FaderLogic"
    payload.mkdir(parents=True)
    shutil.copy2(ROOT / "dist/FaderLogic.exe", payload / "FaderLogic.exe")
    for name in ("README.md", "CHANGELOG.md", "LICENSE", "COPYRIGHT", "THIRD_PARTY_NOTICES.md", "requirements.txt", "requirements-build.txt"):
        shutil.copy2(ROOT / name, payload / name)
    for name in ("assets", "licenses"):
        shutil.copytree(ROOT / name, payload / name)
    copy_docs(payload / "docs")
    verify_clean_tree(payload, portable=True)
    compiler_license = Path(compiler).parent / "license.txt"
    if compiler_license.exists():
        shutil.copy2(compiler_license, ROOT / "licenses/InnoSetup-LICENSE.txt")
        shutil.copy2(compiler_license, payload / "licenses/InnoSetup-LICENSE.txt")
    subprocess.run([compiler, "/DAppVersion="+__version__, str(ROOT / "installer/FaderLogic.iss")], cwd=ROOT, check=True)
    print(f"Built releases/FaderLogic-{__version__}-windows-x64-setup.exe")


if __name__ == "__main__":
    main()
