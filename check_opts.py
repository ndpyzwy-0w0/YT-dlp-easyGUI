"""Assert format presets wire into yt-dlp options. Run: python check_opts.py"""

from app import FORMAT_PRESETS, build_ydl_opts

opts = build_ydl_opts("D:\\out", "仅音频 (MP3)", False, print, lambda d: None, has_ffmpeg=True)
assert opts["format"] == FORMAT_PRESETS["仅音频 (MP3)"]["format"]
assert opts["postprocessors"][0]["preferredcodec"] == "mp3"
assert opts["noplaylist"] is True
assert "%(title)s.%(ext)s" in opts["outtmpl"]

opts2 = build_ydl_opts(".", "最佳画质", True, print, lambda d: None, has_ffmpeg=True)
assert opts2["noplaylist"] is False
assert "postprocessors" not in opts2
assert opts2["format"] == FORMAT_PRESETS["最佳画质"]["format"]

opts3 = build_ydl_opts(".", "1080p", False, print, lambda d: None, has_ffmpeg=False)
assert opts3["format"] == "b[height<=1080]/b"
print("ok")
