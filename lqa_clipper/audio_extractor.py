import subprocess
from pathlib import Path
from typing import Optional, Union

from lqa_clipper.ffmpeg_utils import get_ffmpeg_executable


def extract_mic_audio(
    video_path: Union[str, Path],
    mic_track_index: int = 1,
    output_wav_path: Optional[Union[str, Path]] = None,
) -> Path:
    """Step 1: Extract microphone audio track from video as 16kHz mono WAV file.

    Args:
        video_path: Path to the input video file.
        mic_track_index: Index of the audio track (0-based for -map 0:a:N).
        output_wav_path: Optional destination path for extracted WAV.
            Defaults to '<video_parent>/<video_stem>_mic_track<index>.wav'.

    Returns:
        Path to the generated WAV file.

    Raises:
        FileNotFoundError: If video_path does not exist.
        RuntimeError: If FFmpeg execution fails.
    """
    video_path = Path(video_path).resolve()
    if not video_path.exists():
        raise FileNotFoundError(f"Input video file not found: {video_path}")

    if output_wav_path is None:
        output_wav_path = video_path.parent / f"{video_path.stem}_mic_track{mic_track_index}.wav"
    else:
        output_wav_path = Path(output_wav_path).resolve()

    output_wav_path.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg_bin = get_ffmpeg_executable()
    cmd = [
        ffmpeg_bin,
        "-y",
        "-i",
        str(video_path),
        "-map",
        f"0:a:{mic_track_index}",
        "-ar",
        "16000",
        "-ac",
        "1",
        "-vn",
        str(output_wav_path),
    ]

    try:
        subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or e.stdout or "Unknown ffmpeg error"
        raise RuntimeError(f"FFmpeg audio extraction failed:\n{error_msg}") from e
    except FileNotFoundError as e:
        raise RuntimeError(
            f"FFmpeg executable '{ffmpeg_bin}' not found. Please ensure FFmpeg is installed."
        ) from e

    return output_wav_path


def extract_preview_audio(
    video_path: Union[str, Path],
    mic_track_index: int = 1,
    duration_sec: int = 30,
    output_dir: Union[str, Path] = "./issues",
) -> Path:
    """Extract a short audio snippet for user preview in the UI.

    Args:
        video_path: Path to the video file.
        mic_track_index: Audio track index to preview (0-based).
        duration_sec: Length of audio snippet in seconds (default: 30s).
        output_dir: Directory where preview WAV will be saved.

    Returns:
        Path to the generated preview audio file.
    """
    video_path = Path(video_path).resolve()
    if not video_path.exists():
        raise FileNotFoundError(f"動画ファイルが見つかりません: {video_path}")

    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    preview_wav = out_dir / f"preview_track{mic_track_index}.wav"

    ffmpeg_bin = get_ffmpeg_executable()
    cmd = [
        ffmpeg_bin,
        "-y",
        "-i",
        str(video_path),
        "-map",
        f"0:a:{mic_track_index}",
        "-t",
        str(duration_sec),
        "-ar",
        "16000",
        "-ac",
        "1",
        "-vn",
        str(preview_wav),
    ]

    try:
        subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or e.stdout or ""
        raise RuntimeError(f"トラック {mic_track_index} の抽出に失敗しました (存在しないトラック番号の可能性があります):\n{error_msg}") from e

    return preview_wav
