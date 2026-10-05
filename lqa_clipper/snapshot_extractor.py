import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from lqa_clipper.ffmpeg_utils import get_ffmpeg_executable


def extract_snapshots(
    video_path: Union[str, Path],
    issues_or_json_path: Union[str, Path, List[Dict[str, Any]]],
    output_dir: Union[str, Path] = "./issues",
    snapshot_offset_sec: float = 0.1,
    image_format: str = "png",
    file_prefix: str = "issue",
) -> List[Path]:
    """Extract a snapshot image for each issue at (timestamp_start + snapshot_offset_sec).

    Args:
        video_path: Path to the original video file.
        issues_or_json_path: List of issue dicts or path to lqa_issues.json.
        output_dir: Directory to save generated snapshots (default: './issues').
        snapshot_offset_sec: Offset in seconds after timestamp_start (default: 0.1s).
        image_format: Image file extension ('png' or 'jpg').
        file_prefix: Fallback prefix string (default: 'issue').

    Returns:
        List of Paths to generated snapshot images.
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

    snapshot_paths: List[Path] = []
    ffmpeg_bin = get_ffmpeg_executable()
    fmt = image_format.lstrip(".")

    for issue in issues:
        issue_id = issue.get("id", 1)
        start_ts = issue.get("timestamp_start", 0.0)
        snapshot_ts = max(0.0, start_ts + snapshot_offset_sec)

        if "snapshot_path" in issue and issue["snapshot_path"]:
            img_filename = Path(issue["snapshot_path"]).name
        elif "file_prefix" in issue and issue["file_prefix"]:
            img_filename = f"{issue['file_prefix']}.{fmt}"
        else:
            img_filename = f"{file_prefix}_{issue_id:03d}.{fmt}"

        img_path = out_dir / img_filename

        cmd = [
            ffmpeg_bin,
            "-y",
            "-ss",
            f"{snapshot_ts:.3f}",
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(img_path),
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
            raise RuntimeError(
                f"FFmpeg snapshot extraction failed for Issue {issue_id}:\n{error_msg}"
            ) from e
        except FileNotFoundError as e:
            raise RuntimeError(
                f"FFmpeg executable '{ffmpeg_bin}' not found. Please ensure FFmpeg is installed."
            ) from e

        snapshot_paths.append(img_path)

    return snapshot_paths
