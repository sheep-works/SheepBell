import shutil
import subprocess
from pathlib import Path
from typing import Optional, Union


def get_ffmpeg_executable() -> str:
    """Find FFmpeg executable from system PATH or bundled imageio-ffmpeg."""
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass

    return "ffmpeg"


def get_audio_stream_count(file_path: Union[str, Path]) -> int:
    """Count how many audio streams exist in the given media file."""
    file_path = Path(file_path).resolve()
    if not file_path.exists():
        return 0

    ffmpeg_bin = get_ffmpeg_executable()
    cmd = [ffmpeg_bin, "-i", str(file_path)]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output = result.stderr + result.stdout

    count = 0
    for line in output.splitlines():
        if "Stream #" in line and "Audio:" in line:
            count += 1
    return count
