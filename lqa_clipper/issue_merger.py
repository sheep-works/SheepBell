import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def merge_speech_segments(
    raw_segments: List[Dict[str, float]],
    min_silence_sec: float = 2.0,
    margin_pre_sec: float = 2.0,
    margin_post_sec: float = 2.0,
    id_start_index: int = 1,
    file_prefix: str = "issue",
    video_ext: str = ".mp4",
) -> List[Dict[str, Any]]:
    """Merge raw speech segments and apply pre/post margins.

    If two distinct speech segments are separated by >= min_silence_sec,
    they will ALWAYS remain separate issues. When added margins overlap,
    margins are clamped at the midpoint between the two segments instead
    of merging them into a single issue.

    Args:
        raw_segments: List of raw segments with 'start' and 'end' keys in seconds.
        min_silence_sec: Minimum silence duration (in seconds) required to treat as separate issues.
        margin_pre_sec: Seconds to subtract from the start timestamp.
        margin_post_sec: Seconds to add to the end timestamp.
        id_start_index: Starting integer for issue IDs.
        file_prefix: Prefix string for generated files and ID representation.
        video_ext: Extension of clip video files (e.g. '.mp4', '.mkv').

    Returns:
        List of structured issue dicts.
    """
    if not raw_segments:
        return []

    # Sort segments by start time
    sorted_segments = sorted(raw_segments, key=lambda s: s["start"])

    # 1. Merge raw segments only if silence gap < min_silence_sec
    merged_raw: List[Dict[str, float]] = []
    current_start = sorted_segments[0]["start"]
    current_end = sorted_segments[0]["end"]

    for seg in sorted_segments[1:]:
        gap = seg["start"] - current_end
        if gap < min_silence_sec:
            # Merge: extend current end
            current_end = max(current_end, seg["end"])
        else:
            merged_raw.append({"start": current_start, "end": current_end})
            current_start = seg["start"]
            current_end = seg["end"]
    merged_raw.append({"start": current_start, "end": current_end})

    # 2. Apply margins while preserving separation for all distinct segments
    # If margins between adjacent segments overlap, clamp at the midpoint between them.
    margined: List[Dict[str, float]] = []
    n = len(merged_raw)

    for i in range(n):
        seg = merged_raw[i]
        orig_start = seg["start"]
        orig_end = seg["end"]

        # Calculate start timestamp with pre-margin
        if i == 0:
            m_start = max(0.0, orig_start - margin_pre_sec)
        else:
            prev_end = merged_raw[i - 1]["end"]
            midpoint = (prev_end + orig_start) / 2.0
            # Start cannot go before the midpoint of the gap with previous segment
            m_start = max(0.0, max(orig_start - margin_pre_sec, midpoint))

        # Calculate end timestamp with post-margin
        if i == n - 1:
            m_end = orig_end + margin_post_sec
        else:
            next_start = merged_raw[i + 1]["start"]
            midpoint = (orig_end + next_start) / 2.0
            # End cannot go past the midpoint of the gap with next segment
            m_end = min(orig_end + margin_post_sec, midpoint)

        margined.append({
            "start": round(m_start, 2),
            "end": round(m_end, 2),
        })

    # 3. Format structured issues with prefix and paths
    issues: List[Dict[str, Any]] = []
    ext = video_ext if video_ext.startswith(".") else f".{video_ext}"
    clean_prefix = file_prefix.strip() or "issue"

    for offset, seg in enumerate(margined):
        curr_id = id_start_index + offset
        name_prefix = f"{clean_prefix}_{curr_id:03d}"
        issues.append({
            "id": curr_id,
            "file_prefix": name_prefix,
            "clip_path": f"{name_prefix}{ext}",
            "snapshot_path": f"{name_prefix}.png",
            "timestamp_start": seg["start"],
            "timestamp_end": seg["end"],
            "issue_tag": "",
            "description": "",
        })

    return issues


def export_issues_to_csv(
    issues: List[Dict[str, Any]],
    output_csv_path: Union[str, Path],
) -> Path:
    """Export issue list to a UTF-8 BOM CSV file for Excel and Google Sheets compatibility."""
    out_path = Path(output_csv_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "id",
        "file_prefix",
        "clip_path",
        "snapshot_path",
        "timestamp_start",
        "timestamp_end",
        "issue_tag",
        "description",
    ]

    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for issue in issues:
            writer.writerow(issue)

    return out_path


def merge_and_export_issues(
    raw_segments: List[Dict[str, float]],
    min_silence_sec: float = 2.0,
    margin_pre_sec: float = 2.0,
    margin_post_sec: float = 2.0,
    id_start_index: int = 1,
    file_prefix: str = "issue",
    video_ext: str = ".mp4",
    output_json_path: Optional[Union[str, Path]] = None,
    output_csv_path: Optional[Union[str, Path]] = None,
) -> List[Dict[str, Any]]:
    """Step 3: Merge raw speech segments, apply margins, and export to JSON and CSV."""
    issues = merge_speech_segments(
        raw_segments=raw_segments,
        min_silence_sec=min_silence_sec,
        margin_pre_sec=margin_pre_sec,
        margin_post_sec=margin_post_sec,
        id_start_index=id_start_index,
        file_prefix=file_prefix,
        video_ext=video_ext,
    )

    if output_json_path is not None:
        out_json = Path(output_json_path).resolve()
        out_json.parent.mkdir(parents=True, exist_ok=True)
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(issues, f, indent=2, ensure_ascii=False)

    if output_csv_path is not None:
        export_issues_to_csv(issues, output_csv_path)

    return issues
