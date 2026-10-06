import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from lqa_clipper.ffmpeg_utils import get_ffmpeg_executable


def clip_video_issues(
    video_path: Union[str, Path],
    issues_or_json_path: Union[str, Path, List[Dict[str, Any]]],
    output_dir: Union[str, Path] = "./issues",
    file_prefix: str = "issue",
    mix_audio: bool = True,
    game_track_index: int = 0,
    mic_track_index: int = 1,
) -> List[Path]:
    """Step 4: Cut video clips for each issue.

    Args:
        video_path: Path to the original input video.
        issues_or_json_path: Either a list of issue dicts or a path to 'lqa_issues.json'.
        output_dir: Directory where clipped videos will be saved (default: './issues').
        file_prefix: Prefix used for fallback naming (default: 'issue').
        mix_audio: If True, mixes game audio and mic audio into a single audio track for universal playback.
                   If False, keeps separate audio tracks (-map 0 -c copy).
        game_track_index: Index of the game audio track (default: 0).
        mic_track_index: Index of the mic audio track (default: 1).

    Returns:
        List of Paths to generated clip files.
    """
    video_path = Path(video_path).resolve()
    if not video_path.exists():
        raise FileNotFoundError(f"Original video not found: {video_path}")

    # Load issues
    if isinstance(issues_or_json_path, (str, Path)):
        json_path = Path(issues_or_json_path).resolve()
        if not json_path.exists():
            raise FileNotFoundError(f"Issues JSON file not found: {json_path}")
        with open(json_path, "r", encoding="utf-8") as f:
            issues: List[Dict[str, Any]] = json.load(f)
    else:
        issues = issues_or_json_path

    if not issues:
        return []

    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    clip_paths: List[Path] = []
    ext = video_path.suffix or ".mp4"
    ffmpeg_bin = get_ffmpeg_executable()

    for issue in issues:
        issue_id = issue.get("id", 1)
        start_ts = issue.get("timestamp_start", 0.0)
        end_ts = issue.get("timestamp_end", 0.0)

        if end_ts <= start_ts:
            continue

        if "clip_path" in issue and issue["clip_path"]:
            clip_filename = Path(issue["clip_path"]).name
        elif "file_prefix" in issue and issue["file_prefix"]:
            clip_filename = f"{issue['file_prefix']}{ext}"
        else:
            clip_filename = f"{file_prefix}_{issue_id:03d}{ext}"

        clip_path = out_dir / clip_filename

        if mix_audio and game_track_index != mic_track_index:
            # Mix game and mic audio into 1 stereo track (video is still -c:v copy)
            cmd = [
                ffmpeg_bin,
                "-y",
                "-ss",
                str(start_ts),
                "-to",
                str(end_ts),
                "-i",
                str(video_path),
                "-filter_complex",
                f"[0:a:{game_track_index}][0:a:{mic_track_index}]amix=inputs=2:duration=longest[aout]",
                "-map",
                "0:v:0",
                "-map",
                "[aout]",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-avoid_negative_ts",
                "make_zero",
                str(clip_path),
            ]
        else:
            # Preserve separate streams
            cmd = [
                ffmpeg_bin,
                "-y",
                "-ss",
                str(start_ts),
                "-to",
                str(end_ts),
                "-i",
                str(video_path),
                "-map",
                "0",
                "-c",
                "copy",
                "-avoid_negative_ts",
                "make_zero",
                str(clip_path),
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
            # Fallback to simple -map 0 copy if filter_complex fails (e.g. single track video)
            fallback_cmd = [
                ffmpeg_bin,
                "-y",
                "-ss",
                str(start_ts),
                "-to",
                str(end_ts),
                "-i",
                str(video_path),
                "-map",
                "0",
                "-c",
                "copy",
                "-avoid_negative_ts",
                "make_zero",
                str(clip_path),
            ]
            try:
                subprocess.run(
                    fallback_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True,
                )
            except subprocess.CalledProcessError as fallback_e:
                error_msg = fallback_e.stderr or fallback_e.stdout or e.stderr or "Unknown ffmpeg error"
                raise RuntimeError(f"FFmpeg clipping failed for Issue {issue_id}:\n{error_msg}") from fallback_e
        except FileNotFoundError as e:
            raise RuntimeError(
                f"FFmpeg executable '{ffmpeg_bin}' not found. Please ensure FFmpeg is installed."
            ) from e

        clip_paths.append(clip_path)

    return clip_paths
