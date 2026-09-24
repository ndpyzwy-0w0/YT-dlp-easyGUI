"""Assert format presets wire into yt-dlp options. Run: python check_opts.py"""

from app import FORMAT_PRESETS, build_ydl_opts, parse_url, ydl_tool_opts

opts = build_ydl_opts("D:\\out", "仅音频 (MP3)", False, print, lambda d: None, has_ffmpeg=True)
assert opts["format"] == FORMAT_PRESETS["仅音频 (MP3)"]["format"]
assert opts["postprocessors"][0]["preferredcodec"] == "mp3"
assert opts["noplaylist"] is True
assert "%(title)s.%(ext)s" in opts["outtmpl"]

opts2 = build_ydl_opts(".", "最佳画质", True, print, lambda d: None, has_ffmpeg=True)
assert opts2["noplaylist"] is False
assert "postprocessors" not in opts2
assert "writethumbnail" not in opts2
assert opts2["format"] == FORMAT_PRESETS["最佳画质"]["format"]

opts_thumbnail = build_ydl_opts(
    ".", "最佳画质", False, print, lambda d: None, has_ffmpeg=True, download_thumbnail=True
)
assert opts_thumbnail["writethumbnail"] is True

opts3 = build_ydl_opts(".", "1080p", False, print, lambda d: None, has_ffmpeg=False)
assert opts3["format"] == "b[height<=1080]/bv*[height<=1080]/b/bv*"

opts4 = build_ydl_opts(
    ".", "最佳画质", False, print, lambda d: None, ffmpeg_path=r"D:\tools\ffmpeg.exe", deno_path=r"D:\tools\deno.exe"
)
assert opts4["ffmpeg_location"] == r"D:\tools\ffmpeg.exe"
assert opts4["js_runtimes"]["deno"]["path"] == r"D:\tools\deno.exe"
assert opts4["format"] == FORMAT_PRESETS["最佳画质"]["format"]
assert ydl_tool_opts(r"D:\tools\ffmpeg.exe", r"D:\tools\deno.exe") == {
    "ffmpeg_location": r"D:\tools\ffmpeg.exe",
    "js_runtimes": {"deno": {"path": r"D:\tools\deno.exe"}},
}

assert parse_url("WARNING: [youtube] No supported JavaScript runtime could be found. Only deno is enabled by default. See https://github.com/yt-dlp/yt-dlp#js-runtimes for details on installing one") is None
assert parse_url("https://www.youtube.com/watch?v=znOUACYRdeQ") == "https://www.youtube.com/watch?v=znOUACYRdeQ"
print("ok")
