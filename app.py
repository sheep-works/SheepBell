import argparse
import os
from pathlib import Path
from typing import Optional
import gradio as gr

from lqa_clipper.pipeline import run_pipeline
from lqa_clipper.audio_extractor import extract_preview_audio


def gradio_preview_audio(video_path: str, mic_track_index: int, output_dir: str):
    """Extract audio snippet for user preview."""
    if not video_path or not video_path.strip():
        gr.Warning("動画ファイルパスを入力してください。")
        return None

    clean_video_path = video_path.strip().strip('"').strip("'")
    clean_out_dir = output_dir.strip().strip('"').strip("'") if output_dir else "./issues"

    try:
        preview_wav = extract_preview_audio(
            video_path=clean_video_path,
            mic_track_index=int(mic_track_index),
            duration_sec=30,
            output_dir=clean_out_dir,
        )
        gr.Info(f"トラック {mic_track_index} の音声を読み込みました。再生してマイク音か確認してください。")
        return str(preview_wav)
    except Exception as e:
        gr.Error(str(e))
        return None


def gradio_run(
    video_path: str,
    mic_track_index: int,
    file_prefix: str,
    id_start_index: int,
    vad_threshold: float,
    min_silence_sec: float,
    margin_pre_sec: float,
    margin_post_sec: float,
    output_dir: str,
    run_steps_1_to_3: bool,
    run_step_4: bool,
    enable_transcription: bool,
    whisper_model: str,
    whisper_language: str,
    enable_snapshots: bool,
    snapshot_offset_sec: float,
):
    """Bridge function between Gradio UI and pipeline generator."""
    if not video_path or not video_path.strip():
        yield "❌ エラー: 動画ファイルのパスを入力してください。"
        return

    # Extract language code if formatted like "ja (日本語)"
    lang_code = whisper_language.split()[0].lower() if whisper_language else "auto"

    pipeline_gen = run_pipeline(
        video_path=video_path.strip().strip('"').strip("'"),
        mic_track_index=int(mic_track_index),
        id_start_index=int(id_start_index) if id_start_index else 1,
        file_prefix=file_prefix.strip() if file_prefix else "issue",
        vad_threshold=float(vad_threshold),
        min_silence_sec=float(min_silence_sec),
        margin_pre_sec=float(margin_pre_sec),
        margin_post_sec=float(margin_post_sec),
        output_dir=output_dir.strip().strip('"').strip("'") if output_dir else "./issues",
        run_steps_1_to_3=run_steps_1_to_3,
        run_step_4=run_step_4,
        enable_transcription=enable_transcription,
        whisper_model=whisper_model,
        whisper_language=lang_code,
        enable_snapshots=enable_snapshots,
        snapshot_offset_sec=float(snapshot_offset_sec),
    )

    for log_msg in pipeline_gen:
        yield log_msg


def create_app() -> gr.Blocks:
    """Create and configure the Gradio web interface."""
    theme = gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="slate",
    )

    with gr.Blocks(title="ゲームLQA 自動動画クリップツール", theme=theme) as app:
        gr.Markdown(
            """
            # 🎮 ゲームLQA用 自動動画クリップツール
            OBS等のプレイ録画動画からテスターの発話音声を検出し、**全トラック保持動画クリップ・静止画スナップショット・Faster-Whisper文字起こし・CSV/JSON**を自動生成します。
            """
        )

        with gr.Row():
            with gr.Column(scale=5):
                gr.Markdown("### ⚙️ 入力 & 出力設定")
                video_input = gr.Textbox(
                    label="動画ファイルパス (Video Path)",
                    placeholder=r"sample/sample_0game_1mic.mkv",
                    value=r"sample/sample_0game_1mic.mkv",
                    lines=1,
                )
                with gr.Row():
                    mic_track_input = gr.Number(
                        label="マイク音声トラック番号 (0-indexed)",
                        value=1,
                        precision=0,
                        info="OBSマルチトラック録画 (例: 0=ゲーム音, 1=マイク音)",
                    )
                    output_dir_input = gr.Textbox(
                        label="出力先ディレクトリ",
                        value="./issues",
                        lines=1,
                    )

                with gr.Group():
                    with gr.Row():
                        preview_btn = gr.Button("🎧 指定トラックの音声を試聴する (先頭30秒)", variant="secondary", size="sm")
                    audio_preview = gr.Audio(
                        label="音声プレビュー (再生してマイク音声か確認)",
                        type="filepath",
                        interactive=False,
                    )

                with gr.Row():
                    file_prefix_input = gr.Textbox(
                        label="ファイル名 Prefix (接頭辞)",
                        value="issue",
                        placeholder="例: stage1, bug, issue",
                        info="出力ファイル名の接頭辞 (例: issue_001.mp4, issue_001.png)",
                    )
                    id_start_index_input = gr.Number(
                        label="開始 ID 番号 (Start Index)",
                        value=1,
                        precision=0,
                        info="動画分割撮影時に連番を引き継ぐための開始番号",
                    )

                gr.Markdown("### 🎙️ 音声検出 (Silero VAD) & マージ設定")
                with gr.Group():
                    vad_threshold_slider = gr.Slider(
                        minimum=0.1,
                        maximum=0.9,
                        value=0.5,
                        step=0.05,
                        label="VAD しきい値 (vad_threshold)",
                        info="音声を検知する感度 (値が大きいほど誤検知が減り、小さいほど小さな声も拾う)",
                    )
                    min_silence_slider = gr.Slider(
                        minimum=1.0,
                        maximum=10.0,
                        value=2.0,
                        step=0.5,
                        label="無音許容時間 (min_silence_sec) [秒]",
                        info="この秒数未満の無音であれば同一発話(Issue)として結合します",
                    )
                    with gr.Row():
                        margin_pre_slider = gr.Slider(
                            minimum=0.0,
                            maximum=15.0,
                            value=3.0,
                            step=0.5,
                            label="前マージン (margin_pre_sec) [秒]",
                            info="発話開始前の余白時間",
                        )
                        margin_post_slider = gr.Slider(
                            minimum=0.0,
                            maximum=15.0,
                            value=3.0,
                            step=0.5,
                            label="後マージン (margin_post_sec) [秒]",
                            info="発話終了後の余白時間",
                        )

                gr.Markdown("### 🤖 Speech to Text (Faster-Whisper)")
                with gr.Group():
                    cb_transcription = gr.Checkbox(
                        label="Faster-Whisper で文字起こしを行う (APIキー不要・ローカル/GPU実行)",
                        value=True,
                    )
                    with gr.Row():
                        whisper_model_dd = gr.Dropdown(
                            label="Whisper モデルサイズ",
                            choices=["tiny", "base", "small", "medium", "large-v3"],
                            value="base",
                            info="base / small / medium 推奨",
                        )
                        whisper_lang_dd = gr.Dropdown(
                            label="文字起こし認識言語",
                            choices=[
                                "ja (日本語)",
                                "en (英語)",
                                "zh (中国語)",
                                "auto (自動検出)",
                            ],
                            value="ja (日本語)",
                            info="対象言語または自動検出を選択",
                        )

                gr.Markdown("### 📸 スナップショット画像生成")
                with gr.Group():
                    cb_snapshots = gr.Checkbox(
                        label="開始直後のスナップショット画像を自動生成する",
                        value=True,
                    )
                    snapshot_offset_slider = gr.Slider(
                        minimum=0.0,
                        maximum=2.0,
                        value=0.1,
                        step=0.05,
                        label="スナップショット抽出位置 (開始 + N秒後)",
                        info="Issue開始タイムスタンプから何秒後のフレームを画像化するか (デフォルト: 0.1秒)",
                    )

                gr.Markdown("### 🚦 実行制御")
                with gr.Row():
                    cb_steps_1_to_3 = gr.Checkbox(
                        label="Step 1〜3を実行 (マイク抽出・VAD・文字起こし・JSON/CSV)",
                        value=True,
                    )
                    cb_step_4 = gr.Checkbox(
                        label="Step 4を実行 (全トラック保持クリップ動画 & 静止画生成)",
                        value=True,
                    )

                run_btn = gr.Button("🚀 処理を開始する (Run Pipeline)", variant="primary", size="lg")

            with gr.Column(scale=5):
                gr.Markdown("### 📜 実行ログ & 進捗")
                log_output = gr.Textbox(
                    label="実行ログ (Execution Log)",
                    lines=26,
                    max_lines=35,
                    interactive=False,
                    autoscroll=True,
                )

        preview_btn.click(
            fn=gradio_preview_audio,
            inputs=[video_input, mic_track_input, output_dir_input],
            outputs=[audio_preview],
        )

        run_btn.click(
            fn=gradio_run,
            inputs=[
                video_input,
                mic_track_input,
                file_prefix_input,
                id_start_index_input,
                vad_threshold_slider,
                min_silence_slider,
                margin_pre_slider,
                margin_post_slider,
                output_dir_input,
                cb_steps_1_to_3,
                cb_step_4,
                cb_transcription,
                whisper_model_dd,
                whisper_lang_dd,
                cb_snapshots,
                snapshot_offset_slider,
            ],
            outputs=[log_output],
        )

    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SheepBell Gradio Web UI")
    parser.add_argument("--share", action="store_true", help="Create a publicly shareable Gradio link (for Colab)")
    parser.add_argument("--port", type=int, default=7860, help="Port to run the web server on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (e.g. 0.0.0.0 for containers)")
    args = parser.parse_args()

    demo = create_app()
    demo.launch(
        server_name="0.0.0.0" if args.share else args.host,
        server_port=args.port,
        share=args.share,
    )
