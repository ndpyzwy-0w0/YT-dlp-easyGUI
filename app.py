"""简易 yt-dlp 下载工具。"""

from __future__ import annotations

import os
import re
import shutil
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from ensure_tools import ensure_tools, find_deno, find_ffmpeg

_HTTP_URL_RE = re.compile(r"https?://[^\s<>\"'`]+", re.I)
_YTDLP_DOC_RE = re.compile(r"github\.com/yt-dlp", re.I)
_BARE_SITE_RE = re.compile(
    r"^(?:www\.)?(?:youtube\.com|youtu\.be|youtube-nocookie\.com)/\S+",
    re.I,
)


def parse_url(text: str) -> str | None:
    """Return a usable http(s) URL, or None if the field is not a video link."""
    raw = (text or "").strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        raw = raw[1:-1].strip()
    if not raw:
        return None

    found = []
    for m in _HTTP_URL_RE.finditer(raw):
        url = m.group(0).rstrip(".,);]>\"'")
        if url and not _YTDLP_DOC_RE.search(url):
            found.append(url)
    if found:
        return found[0]
    if _BARE_SITE_RE.match(raw):
        return "https://" + raw
    return None


try:
    import yt_dlp
except ImportError:
    yt_dlp = None

FORMAT_PRESETS = {
    "最佳画质": {"format": "bv*+ba/b/bv*"},
    "1080p": {"format": "bv*[height<=1080]+ba/b[height<=1080]/bv*[height<=1080]/b"},
    "720p": {"format": "bv*[height<=720]+ba/b[height<=720]/bv*[height<=720]/b"},
    "仅音频 (MP3)": {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    },
}


# 没有 ffmpeg 时无法合并音视频轨；加 bv* 避免「一体流不存在」直接失败。
NO_FFMPEG_FORMATS = {
    "最佳画质": "b/bv*/best",
    "1080p": "b[height<=1080]/bv*[height<=1080]/b/bv*",
    "720p": "b[height<=720]/bv*[height<=720]/b/bv*",
}


def ydl_tool_opts(ffmpeg_path: str | Path | None = None, deno_path: str | Path | None = None) -> dict:
    opts = {}
    if ffmpeg_path:
        opts["ffmpeg_location"] = str(ffmpeg_path)
    deno = deno_path or find_deno()
    if deno:
        opts["js_runtimes"] = {"deno": {"path": str(deno)}}
    return opts


def build_ydl_opts(
    out_dir: str,
    preset: str,
    playlist: bool,
    log_hook,
    progress_hook,
    has_ffmpeg: bool | None = None,
    ffmpeg_path: str | Path | None = None,
    deno_path: str | Path | None = None,
    download_thumbnail: bool = False,
) -> dict:
    opts = {
        "outtmpl": str(Path(out_dir) / "%(title)s.%(ext)s"),
        "noplaylist": not playlist,
        "noprogress": True,
        "progress_hooks": [progress_hook],
        "logger": _YdlLogger(log_hook),
        "retries": 3,
        "fragment_retries": 3,
        "concurrent_fragment_downloads": 4,
        **ydl_tool_opts(ffmpeg_path, deno_path),
    }
    if ffmpeg_path:
        has_ffmpeg = True
    elif has_ffmpeg is None:
        has_ffmpeg = shutil.which("ffmpeg") is not None
    if not has_ffmpeg and preset in NO_FFMPEG_FORMATS:
        opts["format"] = NO_FFMPEG_FORMATS[preset]
    else:
        opts.update(FORMAT_PRESETS[preset])
    if download_thumbnail:
        opts["writethumbnail"] = True
    return opts


class _YdlLogger:
    def __init__(self, hook):
        self.hook = hook

    def debug(self, msg):
        if msg.startswith("[debug] "):
            return
        self.hook(msg)

    def info(self, msg):
        self.hook(msg)

    def warning(self, msg):
        self.hook(f"警告: {msg}")

    def error(self, msg):
        self.hook(f"错误: {msg}")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("简易 yt-dlp 下载工具")
        self.geometry("760x600")
        self.minsize(600, 480)

        self._busy = False
        default_dir = str(Path.home() / "Downloads")
        self.url_var = tk.StringVar()
        self.dir_var = tk.StringVar(value=default_dir)
        self.preset_var = tk.StringVar(value="最佳画质")
        self.playlist_var = tk.BooleanVar(value=False)
        self.thumbnail_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value=self._startup_status())
        self.progress_var = tk.DoubleVar(value=0)
        self.info_title_var = tk.StringVar(value="尚未获取视频信息")
        self.info_meta_var = tk.StringVar(value="粘贴链接后可查看标题、时长和上传者")
        self.log_visible = False

        self._build()

    def _startup_status(self) -> str:
        parts = ["yt-dlp ✓" if yt_dlp else "yt-dlp 未安装"]
        parts.append("ffmpeg ✓" if find_ffmpeg() else "ffmpeg 待安装")
        parts.append("deno ✓" if find_deno() else "deno 待安装")
        return "环境：" + "  ·  ".join(parts)

    def _build(self):
        style = ttk.Style(self)
        style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"))
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("Status.TLabel", foreground="#5f6368")
        style.configure("Success.TLabel", foreground="#188038")
        style.configure("Error.TLabel", foreground="#c5221f")

        pad = {"padx": 8, "pady": 5}
        frm = ttk.Frame(self, padding=16)
        frm.pack(fill=tk.BOTH, expand=True)
        frm.columnconfigure(1, weight=1)
        frm.rowconfigure(8, weight=1)

        ttk.Label(frm, text="简易 yt-dlp 下载工具", style="Title.TLabel").grid(
            row=0, column=0, columnspan=5, sticky="w", pady=(0, 12)
        )

        ttk.Label(frm, text="视频链接").grid(row=1, column=0, sticky="w")
        self.url_entry = ttk.Entry(frm, textvariable=self.url_var)
        self.url_entry.grid(row=1, column=1, columnspan=2, sticky="ew", **pad)
        self.paste_btn = ttk.Button(frm, text="粘贴", command=self._paste, width=8)
        self.paste_btn.grid(row=1, column=3, **pad)

        ttk.Label(frm, text="保存到").grid(row=2, column=0, sticky="w")
        self.dir_entry = ttk.Entry(frm, textvariable=self.dir_var)
        self.dir_entry.grid(row=2, column=1, columnspan=2, sticky="ew", **pad)
        self.browse_btn = ttk.Button(frm, text="浏览…", command=self._browse, width=8)
        self.browse_btn.grid(row=2, column=3, **pad)
        self.open_btn = ttk.Button(frm, text="打开目录", command=self._open_dir, width=8)
        self.open_btn.grid(row=2, column=4, padx=(0, 8), pady=5)

        ttk.Label(frm, text="下载设置").grid(row=3, column=0, sticky="w")
        self.preset_combo = ttk.Combobox(
            frm,
            textvariable=self.preset_var,
            values=list(FORMAT_PRESETS),
            state="readonly",
        )
        self.preset_combo.grid(row=3, column=1, sticky="w", **pad)
        self.playlist_check = ttk.Checkbutton(
            frm, text="下载整个播放列表", variable=self.playlist_var
        )
        self.playlist_check.grid(row=3, column=2, columnspan=2, sticky="w")
        self.thumbnail_check = ttk.Checkbutton(
            frm, text="下载视频封面", variable=self.thumbnail_var
        )
        self.thumbnail_check.grid(row=3, column=4, sticky="w", padx=8, pady=5)

        btns = ttk.Frame(frm)
        btns.grid(row=4, column=0, columnspan=5, sticky="ew", pady=(8, 12))
        self.info_btn = ttk.Button(btns, text="查看信息", command=self._info)
        self.dl_btn = ttk.Button(
            btns, text="开始下载", command=self._download, style="Primary.TButton"
        )
        self.info_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.dl_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.status_label = ttk.Label(btns, textvariable=self.status_var, style="Status.TLabel")
        self.status_label.pack(side=tk.RIGHT, padx=(8, 0))

        info_frame = ttk.LabelFrame(frm, text="视频信息", padding=10)
        info_frame.grid(row=5, column=0, columnspan=5, sticky="ew", pady=(0, 10))
        info_frame.columnconfigure(0, weight=1)
        ttk.Label(info_frame, textvariable=self.info_title_var).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(info_frame, textvariable=self.info_meta_var, style="Status.TLabel").grid(
            row=1, column=0, sticky="w", pady=(4, 0)
        )

        self.progress = ttk.Progressbar(frm, variable=self.progress_var, maximum=100)
        self.progress.grid(row=6, column=0, columnspan=5, sticky="ew", pady=(0, 4))

        self.log_toggle = ttk.Button(frm, text="显示详细日志", command=self._toggle_log)
        self.log_toggle.grid(row=7, column=0, columnspan=5, sticky="w", pady=(4, 4))
        self.log_frame = ttk.Frame(frm)
        self.log_frame.grid(row=8, column=0, columnspan=5, sticky="nsew")
        self.log_frame.grid_remove()
        self.log_frame.columnconfigure(0, weight=1)
        self.log_frame.rowconfigure(0, weight=1)
        self.log = tk.Text(self.log_frame, height=8, wrap="word", state="disabled")
        self.log.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(self.log_frame, command=self.log.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.log.configure(yscrollcommand=scroll.set)
        self.url_entry.focus_set()

    def _paste(self):
        try:
            raw = self.clipboard_get().strip()
        except tk.TclError:
            messagebox.showinfo("提示", "剪贴板是空的")
            return
        url = parse_url(raw)
        if not url:
            messagebox.showwarning("提示", "链接无效，请粘贴视频网址")
            return
        self.url_var.set(url)

    def _browse(self):
        path = filedialog.askdirectory(initialdir=self.dir_var.get() or ".")
        if path:
            self.dir_var.set(path)

    def _open_dir(self):
        path = self.dir_var.get().strip()
        if not path or not Path(path).is_dir():
            messagebox.showerror("错误", "保存目录不存在")
            return
        os.startfile(path)

    def _toggle_log(self):
        self.log_visible = not self.log_visible
        if self.log_visible:
            self.log_frame.grid()
            self.log_toggle.configure(text="隐藏详细日志")
        else:
            self.log_frame.grid_remove()
            self.log_toggle.configure(text="显示详细日志")

    def _url(self) -> str | None:
        raw = self.url_var.get().strip()
        if not raw:
            messagebox.showwarning("提示", "请先粘贴视频链接")
            return None
        url = parse_url(raw)
        if not url:
            messagebox.showwarning("提示", "链接无效，请粘贴视频网址")
            return None
        if yt_dlp is None:
            messagebox.showerror("错误", "未安装 yt-dlp，请运行: pip install -r requirements.txt")
            return None
        if url != raw:
            self.url_var.set(url)
        return url

    def _set_busy(self, busy: bool):
        self._busy = busy
        state = "disabled" if busy else "normal"
        for widget in (
            self.url_entry,
            self.dir_entry,
            self.paste_btn,
            self.browse_btn,
            self.open_btn,
            self.preset_combo,
            self.playlist_check,
            self.thumbnail_check,
            self.info_btn,
            self.dl_btn,
        ):
            widget.configure(state=state)
        if not busy:
            self.preset_combo.configure(state="readonly")
            self.status_label.configure(style="Status.TLabel")

    def _log(self, msg: str):
        def _append():
            self.log.configure(state="normal")
            self.log.insert("end", msg.rstrip() + "\n")
            self.log.see("end")
            self.log.configure(state="disabled")

        self.after(0, _append)

    def _status(self, msg: str, percent: float | None = None):
        def _set():
            self.status_var.set(msg)
            if msg in {"下载完成", "信息已获取"}:
                self.status_label.configure(style="Success.TLabel")
            elif "失败" in msg:
                self.status_label.configure(style="Error.TLabel")
            else:
                self.status_label.configure(style="Status.TLabel")
            if percent is not None:
                self.progress_var.set(percent)
                self.progress.stop()
                self.progress.configure(mode="determinate")

        self.after(0, _set)

    def _set_info(self, title: str, meta: str):
        self.after(0, lambda: self.info_title_var.set(title))
        self.after(0, lambda: self.info_meta_var.set(meta))

    def _set_progress_indeterminate(self):
        def _set():
            self.progress.configure(mode="indeterminate")
            self.progress.start(12)

        self.after(0, _set)

    def _progress_hook(self, d: dict):
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            done = d.get("downloaded_bytes") or 0
            pct = (done / total * 100) if total else 0
            speed = d.get("_speed_str") or ""
            eta = d.get("_eta_str") or ""
            name = Path(d.get("filename") or "").name
            extra = "  ".join(x for x in (speed, f"剩余 {eta}" if eta else "") if x)
            self._status(f"下载中 {pct:.1f}%  {name}  {extra}".strip(), pct)
        elif status == "finished":
            name = Path(d.get("filename") or "").name
            self._status(f"处理中… {name}", 100)
            self._log(f"下载完成，正在后处理: {name}")

    def _info(self):
        url = self._url()
        if not url or self._busy:
            return
        self._set_busy(True)
        self._set_progress_indeterminate()
        self._status("正在获取信息…")
        threading.Thread(target=self._info_worker, args=(url,), daemon=True).start()

    def _info_worker(self, url: str):
        try:
            ffmpeg, deno = ensure_tools(self._log)
            opts = {
                "quiet": True,
                "noplaylist": not self.playlist_var.get(),
                **ydl_tool_opts(ffmpeg, deno),
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
            if info is None:
                raise RuntimeError("没有解析到视频信息")
            entries = info.get("entries")
            if entries:
                titles = [e.get("title") or "?" for e in entries if e]
                self._set_info(
                    info.get("title") or "播放列表",
                    f"播放列表 · 共 {len(titles)} 项",
                )
                self._log(f"播放列表: {info.get('title') or ''}  共 {len(titles)} 项")
                for i, t in enumerate(titles[:30], 1):
                    self._log(f"  {i}. {t}")
                if len(titles) > 30:
                    self._log(f"  …还有 {len(titles) - 30} 项")
            else:
                mins, secs = divmod(int(info.get("duration") or 0), 60)
                self._set_info(
                    info.get("title") or "未命名视频",
                    f"时长 {mins}:{secs:02d}  ·  上传者 {info.get('uploader') or '-'}",
                )
                self._log(
                    f"标题: {info.get('title')}\n"
                    f"时长: {mins}:{secs:02d}  上传者: {info.get('uploader') or '-'}\n"
                    f"网页: {info.get('webpage_url') or url}"
                )
            self._status("信息已获取")
        except Exception as e:
            self._log(f"获取信息失败: {e}")
            self._status("获取信息失败")
        finally:
            self.after(0, lambda: self._set_busy(False))

    def _download(self):
        url = self._url()
        if not url or self._busy:
            return
        out_dir = self.dir_var.get().strip()
        if not out_dir:
            messagebox.showwarning("提示", "请选择保存目录")
            return
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        preset = self.preset_var.get()
        self._set_busy(True)
        self.progress_var.set(0)
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self._status("开始下载…")
        threading.Thread(
            target=self._download_worker,
            args=(url, out_dir, preset, self.playlist_var.get(), self.thumbnail_var.get()),
            daemon=True,
        ).start()

    def _download_worker(
        self, url: str, out_dir: str, preset: str, playlist: bool, download_thumbnail: bool
    ):
        try:
            self._status("正在准备 ffmpeg / deno…")
            ffmpeg, deno = ensure_tools(self._log)
            if preset == "仅音频 (MP3)" and not ffmpeg:
                self._log("转 MP3 需要 ffmpeg，自动安装失败")
                self._status("下载失败")
                return
            if not ffmpeg:
                self._log("未找到 ffmpeg，将尽量下载单文件；音视频分轨时可能没有声音")
            opts = build_ydl_opts(
                out_dir,
                preset,
                playlist,
                self._log,
                self._progress_hook,
                has_ffmpeg=bool(ffmpeg),
                ffmpeg_path=ffmpeg,
                deno_path=deno,
                download_thumbnail=download_thumbnail,
            )
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            self._status("下载完成", 100)
            self._log("全部完成。")
        except Exception as e:
            self._log(f"下载失败: {e}")
            self._status("下载失败")
        finally:
            self.after(0, lambda: self._set_busy(False))


def main():
    App().mainloop()


if __name__ == "__main__":
    main()
