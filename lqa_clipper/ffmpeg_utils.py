import shutil
from typing import Optional


def get_ffmpeg_executable() -> str:
    """Find FFmpeg executable from system PATH or bundled imageio-ffmpeg."""
    # 1. System PATH
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    # 2. imageio-ffmpeg fallback
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass

    # 3. Default name
    return "ffmpeg"
