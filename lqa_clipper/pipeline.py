import os
import json
import time
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

from lqa_clipper.audio_extractor import extract_mic_audio
from lqa_clipper.vad_detector import detect_speech_segments
from lqa_clipper.issue_merger import merge_speech_segments, export_issues_to_csv
from lqa_clipper.transcriber import transcribe_issues
from lqa_clipper.video_clipper import clip_video_issues
from lqa_clipper.snapshot_extractor import extract_snapshots


def run_pipeline(
    video_path: Union[str, Path],
    mic_track_index: int = 1,
    vad_threshold: float = 0.5,
    min_silence_sec: float = 2.0,
    margin_pre_sec: float = 3.0,
    margin_post_sec: float = 3.0,
    output_dir: Union[str, Path] = "./issues",
    run_steps_1_to_3: bool = True,
    run_step_4: bool = True,
    enable_transcription: bool = True,
    whisper_model: str = "base",
    whisper_language: str = "ja",
    enable_snapshots: bool = True,
    snapshot_offset_sec: float = 0.1,
    id_start_index: int = 1,
    file_prefix: str = "issue",
) -> Generator[str, None, Dict[str, Any]]:
    """Pipeline orchestrator for LQA video clipping, transcription, snapshots, and JSON/CSV export.

    Yields:
        Progress/log messages in real-time.

    Returns:
        Summary dict containing status, issue list, and output file paths.
    """
    logs: List[str] = []

    def log(msg: str) -> str:
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] {msg}"
        logs.append(entry)
        return "\n".join(logs)

    video_path = Path(video_path).resolve()
    clean_prefix = file_prefix.strip() or "issue"
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "lqa_issues.json"
    csv_path = out_dir / "lqa_issues.csv"
    wav_path = out_dir / f"{video_path.stem}_mic_track{mic_track_index}.wav"
    ext = video_path.suffix or ".mp4"

    issues: List[Dict[str, Any]] = []
    clip_paths: List[Path] = []
    snapshot_paths: List[Path] = []

    yield log(f"🚀 パイプライン開始: {video_path.name} (Prefix: '{clean_prefix}', Start ID: {id_start_index})")

    if not video_path.exists():
        yield log(f"❌ エラー: 動画ファイルが存在しません: {video_path}")
        return {"status": "error", "message": "Video file not found", "issues": []}

    try:
        if run_steps_1_to_3:
            # Step 1: Extract mic audio
            yield log(f"--- [Step 1/4] マイク音声抽出中 (Track: {mic_track_index}) ---")
            extracted_wav = extract_mic_audio(
                video_path=video_path,
                mic_track_index=mic_track_index,
                output_wav_path=wav_path,
            )
            yield log(f"✅ Step 1 完了: {extracted_wav.name} ({extracted_wav.stat().st_size / 1024 / 1024:.2f} MB)")

            # Step 2: Silero VAD
            yield log(f"--- [Step 2/4] Silero VAD による発話区間検出中 (Threshold: {vad_threshold:.2f}) ---")
            raw_segments = detect_speech_segments(
                wav_path=extracted_wav,
                vad_threshold=vad_threshold,
            )
            yield log(f"✅ Step 2 完了: {len(raw_segments)} 箇所の生発話を検出")

            # Step 3: Merge & margins with id_start_index and file_prefix
            yield log(
                f"--- [Step 3/4] 発話マージ & 構造化 (無音許容: {min_silence_sec}s, 前マージン: {margin_pre_sec}s, 後マージン: {margin_post_sec}s) ---"
            )
            issues = merge_speech_segments(
                raw_segments=raw_segments,
                min_silence_sec=min_silence_sec,
                margin_pre_sec=margin_pre_sec,
                margin_post_sec=margin_post_sec,
                id_start_index=id_start_index,
                file_prefix=clean_prefix,
                video_ext=ext,
            )
            yield log(f"✅ Step 3 完了: {len(issues)} 件のIssue区間を算出 (ID: {id_start_index}〜{id_start_index + len(issues) - 1 if issues else id_start_index})")

            # Speech to Text with Faster-Whisper
            if enable_transcription and issues:
                lang_display = whisper_language if whisper_language else "auto"
                yield log(f"--- [文字起こし] Faster-Whisper ({whisper_model}, 言語: {lang_display}) 実行中 ---")
                issues = transcribe_issues(
                    wav_path=extracted_wav,
                    issues=issues,
                    model_size=whisper_model,
                    language=whisper_language,
                )
                for issue in issues:
                    yield log(f"  📝 [{issue['file_prefix']}] {issue.get('description', '')}")
                yield log("✅ 文字起こし完了")

            # Save to JSON
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(issues, f, indent=2, ensure_ascii=False)
            yield log(f"💾 JSON出力完了: {json_path}")

            # Save to CSV
            export_issues_to_csv(issues, csv_path)
            yield log(f"📊 CSV出力完了 (Excel/スプレッドシート用 UTF-8 BOM): {csv_path}")

        else:
            yield log("ℹ️ Step 1〜3 はスキップされました。既存の JSON を探します。")
            if json_path.exists():
                with open(json_path, "r", encoding="utf-8") as f:
                    issues = json.load(f)
                yield log(f"📄 既存の JSON ({len(issues)} 件のIssue) を読み込みました: {json_path}")
            else:
                yield log(f"❌ エラー: 既存の JSON ファイルが見つかりません: {json_path}")
                return {"status": "error", "message": "JSON file not found", "issues": []}

        if run_step_4:
            # Step 4: Video clips (all audio tracks retained with -map 0)
            yield log(f"--- [Step 4/4] FFmpeg による高速クリップ生成中 (-c copy, -map 0 全トラック保持) ---")
            clip_paths = clip_video_issues(
                video_path=video_path,
                issues_or_json_path=issues,
                output_dir=out_dir,
                file_prefix=clean_prefix,
            )
            yield log(f"✅ Step 4 (動画クリップ) 完了: {len(clip_paths)} 個のクリップ動画を生成 -> {out_dir}")

            # Step 4.5: Snapshots
            if enable_snapshots and issues:
                yield log(f"--- [スナップショット] 開始 + {snapshot_offset_sec}s の静止画を抽出中 ---")
                snapshot_paths = extract_snapshots(
                    video_path=video_path,
                    issues_or_json_path=issues,
                    output_dir=out_dir,
                    snapshot_offset_sec=snapshot_offset_sec,
                    file_prefix=clean_prefix,
                )
                yield log(f"✅ スナップショット画像完了: {len(snapshot_paths)} 枚の画像を生成 -> {out_dir}")

        else:
            yield log("ℹ️ Step 4 はスキップされました。")

        yield log("🎉 すべての指定処理が正常に完了しました！")

        return {
            "status": "success",
            "issues": issues,
            "json_path": str(json_path),
            "csv_path": str(csv_path),
            "clips": [str(p) for p in clip_paths],
            "snapshots": [str(p) for p in snapshot_paths],
        }

    except Exception as e:
        yield log(f"❌ パイプライン実行中にエラーが発生しました: {e}")
        return {"status": "error", "message": str(e), "issues": []}
