"""Download portable ffmpeg and deno into tools/ if missing."""

from __future__ import annotations

import shutil
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOOLS = ROOT / "tools"

FFMPEG_URL = (
    "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/"
    "ffmpeg-master-latest-win64-gpl.zip"
)
DENO_URL = (
    "https://github.com/denoland/deno/releases/latest/download/"
    "deno-x86_64-pc-windows-msvc.zip"
)
_UA = "ytdlp-downloader"


def _which_file(*candidates: Path | str | None) -> Path | None:
    for raw in candidates:
        if not raw:
            continue
        p = Path(raw)
        if p.is_file():
            return p
    return None


def find_ffmpeg() -> Path | None:
    return _which_file(
        shutil.which("ffmpeg"),
        TOOLS / "ffmpeg.exe",
        TOOLS / "ffmpeg" / "ffmpeg.exe",
        TOOLS / "ffmpeg" / "bin" / "ffmpeg.exe",
        *TOOLS.glob("ffmpeg-*/bin/ffmpeg.exe") if TOOLS.is_dir() else (),
    )


def find_deno() -> Path | None:
    return _which_file(
        TOOLS / "deno.exe",
        *TOOLS.glob("deno-*/deno.exe") if TOOLS.is_dir() else (),
        shutil.which("deno"),
    )


def _download(url: str, dest: Path, log) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    log(f"正在下载 {dest.name} …")
    with urllib.request.urlopen(req, timeout=120) as resp, tmp.open("wb") as out:
        shutil.copyfileobj(resp, out, length=1024 * 256)
    tmp.replace(dest)


def _unzip(archive: Path, target: Path, log) -> None:
    log(f"正在解压 {archive.name} …")
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(target)


def ensure_ffmpeg(log=print) -> Path | None:
    found = find_ffmpeg()
    if found:
        return found
    archive = TOOLS / "ffmpeg.zip"
    extract_to = TOOLS / "_ffmpeg_extract"
    try:
        _download(FFMPEG_URL, archive, log)
        if extract_to.exists():
            shutil.rmtree(extract_to)
        _unzip(archive, extract_to, log)
        exe = next(extract_to.rglob("ffmpeg.exe"))
        dest_dir = TOOLS / "ffmpeg"
        dest_dir.mkdir(parents=True, exist_ok=True)
        for name in ("ffmpeg.exe", "ffprobe.exe"):
            src = exe.with_name(name)
            if src.is_file():
                shutil.copy2(src, dest_dir / name)
        archive.unlink(missing_ok=True)
        shutil.rmtree(extract_to, ignore_errors=True)
    except Exception as e:
        log(f"下载 ffmpeg 失败: {e}")
        return find_ffmpeg()
    found = find_ffmpeg()
    if found:
        log(f"ffmpeg 已就绪: {found}")
    return found


def ensure_deno(log=print) -> Path | None:
    found = find_deno()
    if found:
        return found
    archive = TOOLS / "deno.zip"
    extract_to = TOOLS / "_deno_extract"
    try:
        _download(DENO_URL, archive, log)
        if extract_to.exists():
            shutil.rmtree(extract_to)
        _unzip(archive, extract_to, log)
        exe = next(extract_to.rglob("deno.exe"))
        shutil.copy2(exe, TOOLS / "deno.exe")
        archive.unlink(missing_ok=True)
        shutil.rmtree(extract_to, ignore_errors=True)
    except Exception as e:
        log(f"下载 deno 失败: {e}")
        return find_deno()
    found = find_deno()
    if found:
        log(f"deno 已就绪: {found}")
    return found


def ensure_tools(log=print) -> tuple[Path | None, Path | None]:
    return ensure_ffmpeg(log), ensure_deno(log)


if __name__ == "__main__":
    ensure_tools()
