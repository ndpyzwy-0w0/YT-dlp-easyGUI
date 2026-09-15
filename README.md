# YT-dlp Easy GUI

简易 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 图形界面：粘贴链接、选目录和画质，后台下载。

A small [yt-dlp](https://github.com/yt-dlp/yt-dlp) GUI: paste a URL, pick a folder and quality, then download in the background.

[中文](#中文) · [English](#english)

仓库 / Repo: <https://github.com/ndpyzwy-0w0/YT-dlp-easyGUI>

---

## 中文

### 能做什么

- 下载 yt-dlp 支持的站点（YouTube、Bilibili 等）
- 粘贴链接时自动抽出 `http(s)` 地址，拒绝把日志里的 `WARNING:` 当成网址
- 查看标题、时长、上传者；播放列表会列出条目
- 画质：最佳 / 1080p / 720p / 仅音频 MP3
- 可选下载整个播放列表
- 进度条 + 日志；默认保存到「下载」文件夹
- 首次查看信息或下载时，若本机没有 **ffmpeg** / **deno**，会自动装到项目的 `tools/`（Windows）

### 环境

- Windows 10/11（`run.bat`、`os.startfile`、自动下载的 ffmpeg/deno 都按 Windows 编写）
- [Python 3.12+](https://www.python.org/downloads/)，安装时勾选 **Add python.exe to PATH**
- 网络：能访问 GitHub（拉 ffmpeg / deno）、以及要下载的视频站点

不需要事先把 ffmpeg 或 deno 加进系统 PATH。

### 快速开始

1. 克隆仓库：

   ```bat
   git clone https://github.com/ndpyzwy-0w0/YT-dlp-easyGUI.git
   cd YT-dlp-easyGUI
   ```

2. 双击 `run.bat`。没有虚拟环境时会自动 `python -m venv .venv` 并安装 `yt-dlp`。

3. 窗口打开后：粘贴视频链接 → 选保存目录（默认为用户「下载」）→ 选画质 → **查看信息** 或 **开始下载**。

第一次点「查看信息」或「开始下载」可能要等一两分钟：正在把 ffmpeg 和 deno 下到 `tools/`。YouTube 需要 deno 才能解析完整格式；合视频轨和音轨、转 MP3 需要 ffmpeg。

手动启动（已有 venv 时）：

```bat
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

只预装工具、不打开窗口：

```bat
.venv\Scripts\python.exe ensure_tools.py
```

### 界面说明

| 控件 | 作用 |
| --- | --- |
| 视频链接 / 粘贴 | 填 `https://...`。粘贴会从剪贴板抽出第一条有效网址 |
| 保存目录 / 浏览 | 输出文件夹，文件名是 `标题.扩展名` |
| 下载格式 | 见下表 |
| 下载整个播放列表 | 默认只下单条；勾选则下整个列表 |
| 查看信息 | 不下载，只解析标题/时长/列表 |
| 开始下载 | 后台下载，界面不卡死 |
| 打开目录 | 用资源管理器打开保存目录 |

画质对应的 yt-dlp 选择器（有 ffmpeg 时优先音视频分轨再合并）：

| 选项 | 行为 |
| --- | --- |
| 最佳画质 | 最高可用视频 + 最佳音轨 |
| 1080p | 高度 ≤ 1080 |
| 720p | 高度 ≤ 720 |
| 仅音频 (MP3) | 抽音频并转 MP3（必须有 ffmpeg） |

没有 ffmpeg 时会退回「单文件 / 仅视频轨」，可能没有声音。工具会尽量自动安装 ffmpeg，一般不必走到这条路径。

### 目录结构

```
YT-dlp-easyGUI/
├── app.py              # tkinter 界面与下载逻辑
├── ensure_tools.py     # 查找或下载 ffmpeg、deno
├── check_opts.py       # 格式选项与 URL 解析的自检
├── requirements.txt    # yt-dlp
├── run.bat             # Windows 一键启动
├── README.md
├── .gitignore          # 忽略 .venv、tools/、缓存
├── .venv/              # 本地虚拟环境（不入库）
└── tools/              # 首次运行后的 ffmpeg、deno（不入库）
```

`tools/` 体积大，已 gitignore。换电脑或删掉该目录后，下次下载会再装一遍。

### 工作原理（简要）

1. `parse_url()` 只接受 `http(s)`（以及不带协议的 youtube.com / youtu.be）。混在日志里的 yt-dlp 文档链接会被丢掉，避免把 `WARNING:` 交给 urllib。
2. `ensure_tools()` 在项目 `tools/` 和 PATH 里找 ffmpeg、deno；没有就从 GitHub 拉官方 zip。
3. 调用 yt-dlp Python API，传入 `ffmpeg_location` 和 `js_runtimes.deno`。
4. 下载在后台线程里跑，进度通过 `progress_hooks` 更新界面。

### 常见问题

**`Requested format is not available`**  
旧版本在没有 ffmpeg 时只找「音视频一体」流，YouTube 现在经常只有分轨。请用当前代码，并确保已装 ffmpeg（看日志里「ffmpeg 已就绪」）。

**`No supported JavaScript runtime`**  
YouTube 需要 deno（≥ 2.3）。关掉旧窗口，重新用 `run.bat` 打开，再点「查看信息」或「开始下载」，让程序带上 `tools/deno.exe`。

**`Unsupported url scheme: "warning"`**  
链接框里进的是警告原文，不是视频地址。清空后再只粘贴 `https://...`。新版本会直接提示「链接无效，请粘贴视频网址」。

**转 MP3 失败**  
ffmpeg 没装上。看日志里的下载错误，或手动运行 `python ensure_tools.py`。

**改完代码没变化**  
必须关掉正在跑的窗口再开，旧进程还是旧代码。

### 自检

```bat
.venv\Scripts\python.exe check_opts.py
```

成功会打印 `ok`。

### 依赖与声明

- 下载引擎：[yt-dlp](https://github.com/yt-dlp/yt-dlp)
- 合流转码：[FFmpeg Builds](https://github.com/yt-dlp/FFmpeg-Builds)（首次自动获取）
- YouTube JS 运行时：[Deno](https://github.com/denoland/deno)（首次自动获取）

请只下载你有权获取的内容，并遵守目标网站条款。本工具是对 yt-dlp 的薄封装，不提供破解或绕过付费墙的功能。

---

## English

### What it does

- Downloads from sites supported by yt-dlp (YouTube, Bilibili, and many others)
- Paste extracts a real `http(s)` URL and rejects log dumps that start with `WARNING:`
- Inspect title, duration, and uploader; playlists list their entries
- Quality presets: best / 1080p / 720p / audio-only MP3
- Optional full-playlist download
- Progress bar + log; default output is the user Downloads folder
- On first **View info** or **Download**, missing **ffmpeg** / **deno** are fetched into `tools/` (Windows)

### Requirements

- Windows 10/11 (`run.bat`, folder open, and the auto-fetched binaries are Windows-specific)
- [Python 3.12+](https://www.python.org/downloads/) with **Add python.exe to PATH**
- Network access to GitHub (ffmpeg/deno) and the video site

You do not need ffmpeg or deno on PATH beforehand.

### Quick start

1. Clone:

   ```bat
   git clone https://github.com/ndpyzwy-0w0/YT-dlp-easyGUI.git
   cd YT-dlp-easyGUI
   ```

2. Double-click `run.bat`. If there is no venv yet, it creates `.venv` and installs `yt-dlp`.

3. Paste a video URL → choose a folder (default: Downloads) → pick a format → **查看信息** (view info) or **开始下载** (download).

The first info/download click may take a minute while ffmpeg and deno land in `tools/`. YouTube needs deno for full format lists; merging A/V tracks and MP3 conversion need ffmpeg.

Manual start:

```bat
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

Prefetch tools only:

```bat
.venv\Scripts\python.exe ensure_tools.py
```

### UI

| Control | Role |
| --- | --- |
| URL / 粘贴 (Paste) | `https://...`. Paste pulls the first valid URL from the clipboard |
| Save folder / 浏览 | Output directory; files are named `title.ext` |
| Format | See table below |
| Download whole playlist | Off = single item; on = entire playlist |
| 查看信息 | Metadata only |
| 开始下载 | Download on a background thread |
| 打开目录 | Open the save folder in Explorer |

Format presets (with ffmpeg, video+audio are merged):

| Preset | Behavior |
| --- | --- |
| 最佳画质 (best) | Best video + best audio |
| 1080p | Height ≤ 1080 |
| 720p | Height ≤ 720 |
| 仅音频 (MP3) | Audio → MP3 (ffmpeg required) |

Without ffmpeg the app falls back to a single file / video-only stream and audio may be missing. Auto-install usually avoids that.

### Layout

```
YT-dlp-easyGUI/
├── app.py              # tkinter UI and download logic
├── ensure_tools.py     # locate or download ffmpeg and deno
├── check_opts.py       # assertions for format opts and URL parsing
├── requirements.txt    # yt-dlp
├── run.bat             # one-click Windows launcher
├── README.md
├── .gitignore          # ignores .venv, tools/, caches
├── .venv/              # local venv (not committed)
└── tools/              # ffmpeg and deno after first run (not committed)
```

`tools/` is large and gitignored. Delete it and the next download will fetch again.

### How it works

1. `parse_url()` keeps `http(s)` (and bare youtube.com / youtu.be). yt-dlp doc links mixed into warning text are ignored so `WARNING:` never reaches urllib.
2. `ensure_tools()` looks in `tools/` and PATH; otherwise it downloads official zips from GitHub.
3. The yt-dlp Python API is called with `ffmpeg_location` and `js_runtimes.deno`.
4. Downloads run on a worker thread; `progress_hooks` update the UI.

### Troubleshooting

**`Requested format is not available`**  
Older builds asked for a single progressive file when ffmpeg was missing; YouTube often only offers separate A/V. Use this tree and confirm ffmpeg is ready in the log.

**`No supported JavaScript runtime`**  
YouTube needs deno (≥ 2.3). Close the old window, start again via `run.bat`, then View info / Download so `tools/deno.exe` is passed in.

**`Unsupported url scheme: "warning"`**  
The URL box contained warning text, not a video link. Clear it and paste `https://...` only. Current builds show **链接无效，请粘贴视频网址**.

**MP3 conversion failed**  
ffmpeg is missing. Check the log, or run `python ensure_tools.py`.

**Code changes do nothing**  
Quit the running window and launch again; an old process keeps old code.

### Self-check

```bat
.venv\Scripts\python.exe check_opts.py
```

Prints `ok` on success.

### Credits and legal

- Engine: [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- Muxing / transcode: [FFmpeg Builds](https://github.com/yt-dlp/FFmpeg-Builds) (fetched on first use)
- YouTube JS runtime: [Deno](https://github.com/denoland/deno) (fetched on first use)

Only download content you have the right to obtain, and follow the site’s terms. This app is a thin GUI over yt-dlp; it does not bypass paywalls or DRM.
