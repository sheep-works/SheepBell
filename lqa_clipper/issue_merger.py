import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def merge_speech_segments(
    raw_segments: List[Dict[str, float]],
    min_silence_sec: float = 2.0,
    margin_pre_sec: float = 3.0,
    margin_post_sec: float = 3.0,
    id_start_index: int = 1,
    file_prefix: str = "issue",
    video_ext: str = ".mp4",
) -> List[Dict[str, Any]]:
    """Merge raw speech segments and apply pre/post margins to form structured issues.

    Args:
        raw_segments: List of raw segments with 'start' and 'end' keys in seconds.
        min_silence_sec: Minimum silence duration (in seconds) required to treat as separate issues.
            Gaps shorter than this are merged into a single segment.
        margin_pre_sec: Seconds to subtract from the start timestamp.
        margin_post_sec: Seconds to add to the end timestamp.
        id_start_index: Starting integer for issue IDs (default: 1).
        file_prefix: Prefix string for generated files and ID representation (default: 'issue').
        video_ext: Extension of clip video files (e.g. '.mp4', '.mkv').

    Returns:
        List of structured issue dicts.
    """
    if not raw_segments:
        return []

    # Sort segments by start time
    sorted_segments = sorted(raw_segments, key=lambda s: s["start"])

    # 1. Merge segments separated by silence < min_silence_sec
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

    # 2. Apply margins
    margined: List[Dict[str, float]] = []
    for seg in merged_raw:
        m_start = max(0.0, seg["start"] - margin_pre_sec)
        m_end = seg["end"] + margin_post_sec
        margined.append({"start": m_start, "end": m_end})

    # 3. Resolve overlaps caused by added margins
    resolved: List[Dict[str, float]] = []
    c_start = margined[0]["start"]
    c_end = margined[0]["end"]

    for seg in margined[1:]:
        if seg["start"] <= c_end:
            c_end = max(c_end, seg["end"])
        else:
            resolved.append({"start": c_start, "end": c_end})
            c_start = seg["start"]
            c_end = seg["end"]
    resolved.append({"start": c_start, "end": c_end})

    # 4. Format structured issues with prefix and paths
    issues: List[Dict[str, Any]] = []
    ext = video_ext if video_ext.startswith(".") else f".{video_ext}"
    clean_prefix = file_prefix.strip() or "issue"

    for offset, seg in enumerate(resolved):
        curr_id = id_start_index + offset
        name_prefix = f"{clean_prefix}_{curr_id:03d}"
        issues.append({
            "id": curr_id,
            "file_prefix": name_prefix,
            "clip_path": f"{name_prefix}{ext}",
            "snapshot_path": f"{name_prefix}.png",
            "timestamp_start": round(seg["start"], 2),
            "timestamp_end": round(seg["end"], 2),
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
    margin_pre_sec: float = 3.0,
    margin_post_sec: float = 3.0,
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
