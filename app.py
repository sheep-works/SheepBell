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


custom_css = """
/* 全体のフォントとベース調整 */
.gradio-container {
    max-width: 960px !important;
    margin: 0 auto !important;
}

/* セクション見出しのアンダーラインスタイル */
.section-title {
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    color: #0f766e !important;
    border-bottom: 2px solid #0d9488 !important;
    padding-bottom: 6px !important;
    margin-top: 28px !important;
    margin-bottom: 16px !important;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* セクション間のマージン */
.section-block {
    margin-bottom: 28px !important;
}

/* 入力ヒント (info) を input の下に配置して視線のガタつきを防ぐ */
.gradio-container label,
.gradio-container .block {
    display: flex !important;
    flex-direction: column !important;
}

/* ラベルを最上部に */
.gradio-container label > span:first-child,
.gradio-container label > .label-text {
    order: 1 !important;
    margin-bottom: 4px !important;
}

/* 入力フィールドを真ん中に配置 */
.gradio-container label > div,
.gradio-container label > input,
.gradio-container label > textarea,
.gradio-container label > select,
.gradio-container label > .wrap {
    order: 2 !important;
}

/* info (補足説明) を入力欄の下部に配置 */
.gradio-container label > .info,
.gradio-container label > span:not(:first-child):not(.label-text) {
    order: 3 !important;
    margin-top: 4px !important;
    margin-bottom: 0 !important;
    font-size: 0.78rem !important;
    color: #64748b !important;
    line-height: 1.3 !important;
}

/* 実行ボタンのスタイリング */
.primary-btn {
    background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%) !important;
    color: white !important;
    font-size: 1.1rem !important;
    font-weight: bold !important;
    border-radius: 8px !important;
    padding: 12px 24px !important;
    margin-top: 16px !important;
    margin-bottom: 24px !important;
}

/* ログ表示エリア */
.log-box textarea {
    font-family: Consolas, 'Courier New', monospace !important;
    font-size: 0.9rem !important;
    background-color: #f8fafc !important;
}
"""


def create_app() -> gr.Blocks:
    """Create and configure the Gradio web interface with clean Teal theme."""
    theme = gr.themes.Soft(
        primary_hue="teal",
        secondary_hue="slate",
        neutral_hue="slate",
    ).set(
        button_primary_background_fill="*primary_600",
        button_primary_background_fill_hover="*primary_700",
        button_primary_text_color="white",
    )

    with gr.Blocks(title="ゲームLQA 自動動画クリップツール", theme=theme, css=custom_css) as app:
        gr.Markdown(
            """
            # 🎮 ゲームLQA用 自動動画クリップ & 文字起こしツール
            OBSプレイ録画からマイク音声を検出し、**全トラック保持動画クリップ・静止画・Faster-Whisper文字起こし・CSV/JSON**を自動生成します。
            """
        )

        # ① 入力 & 出力設定
        with gr.Column(elem_classes=["section-block"]):
            gr.HTML('<div class="section-title">📁 1. 入力・出力 & ファイル設定</div>')
            video_input = gr.Textbox(
                label="動画ファイルパス (Video Path)",
                placeholder=r"sample/sample_0game_1mic.mkv または Google Driveのパス",
                value=r"sample/sample_0game_1mic.mkv",
                lines=1,
            )
            with gr.Row():
                output_dir_input = gr.Textbox(
                    label="出力先ディレクトリ (Output Directory)",
                    value="./issues",
                    lines=1,
                    scale=6,
                )
                file_prefix_input = gr.Textbox(
                    label="ファイル名 Prefix",
                    value="issue",
                    info="例: issue, stage1",
                    scale=4,
                )
                id_start_index_input = gr.Number(
                    label="開始 ID 番号",
                    value=1,
                    precision=0,
                    scale=2,
                )

        # ② マイク音声トラック & 試聴プレビュー
        with gr.Column(elem_classes=["section-block"]):
            gr.HTML('<div class="section-title">🎙️ 2. マイク音声トラック & 試聴確認</div>')
            with gr.Row():
                mic_track_input = gr.Number(
                    label="マイク音声トラック番号 (0-indexed)",
                    value=1,
                    precision=0,
                    info="OBS録画 (0=ゲーム音, 1=マイク音)",
                    scale=3,
                )
                preview_btn = gr.Button("🎧 指定トラックの音声を試聴する (先頭30秒)", variant="secondary", scale=4)

            audio_preview = gr.Audio(
                label="音声プレビュー (再生してマイク音声か確認できます)",
                type="filepath",
                interactive=False,
            )

        # ③ 音声検出 (VAD) & マージ設定
        with gr.Column(elem_classes=["section-block"]):
            gr.HTML('<div class="section-title">🎛️ 3. 音声検出 (Silero VAD) & 発話マージ設定</div>')
            with gr.Row():
                vad_threshold_slider = gr.Slider(
                    minimum=0.1,
                    maximum=0.9,
                    value=0.5,
                    step=0.05,
                    label="VAD しきい値 (感度)",
                    info="大きいほど誤検知減少、小さいほど小声を検知",
                )
                min_silence_slider = gr.Slider(
                    minimum=1.0,
                    maximum=10.0,
                    value=2.0,
                    step=0.5,
                    label="無音許容時間 [秒]",
                    info="この秒数未満の無音は同一Issueとして結合",
                )
            with gr.Row():
                margin_pre_slider = gr.Slider(
                    minimum=0.0,
                    maximum=15.0,
                    value=3.0,
                    step=0.5,
                    label="前マージン [秒]",
                    info="発話開始前の余白時間",
                )
                margin_post_slider = gr.Slider(
                    minimum=0.0,
                    maximum=15.0,
                    value=3.0,
                    step=0.5,
                    label="後マージン [秒]",
                    info="発話終了後の余白時間",
                )

        # ④ 文字起こし & スナップショット設定
        with gr.Column(elem_classes=["section-block"]):
            gr.HTML('<div class="section-title">🤖 4. 文字起こし & 静止画スナップショット設定</div>')
            with gr.Row():
                with gr.Column(scale=5):
                    cb_transcription = gr.Checkbox(
                        label="Faster-Whisper で文字起こしを行う (ローカル/GPU)",
                        value=True,
                    )
                    with gr.Row():
                        whisper_model_dd = gr.Dropdown(
                            label="モデルサイズ",
                            choices=["tiny", "base", "small", "medium", "large-v3"],
                            value="base",
                        )
                        whisper_lang_dd = gr.Dropdown(
                            label="認識言語",
                            choices=[
                                "ja (日本語)",
                                "en (英語)",
                                "zh (中国語)",
                                "auto (自動検出)",
                            ],
                            value="ja (日本語)",
                        )
                with gr.Column(scale=5):
                    cb_snapshots = gr.Checkbox(
                        label="開始直後のスナップショット静止画を自動生成する",
                        value=True,
                    )
                    snapshot_offset_slider = gr.Slider(
                        minimum=0.0,
                        maximum=2.0,
                        value=0.1,
                        step=0.05,
                        label="スナップショット位置 (開始 + N秒後)",
                        info="デフォルト: 0.1秒後のフレーム",
                    )

        # ⑤ 実行制御 & 開始ボタン
        with gr.Column(elem_classes=["section-block"]):
            gr.HTML('<div class="section-title">🚦 5. パイプライン実行</div>')
            with gr.Row():
                cb_steps_1_to_3 = gr.Checkbox(
                    label="Step 1〜3を実行 (マイク抽出・VAD・文字起こし・JSON/CSV出力)",
                    value=True,
                )
                cb_step_4 = gr.Checkbox(
                    label="Step 4を実行 (全トラック保持クリップ動画 & 静止画生成)",
                    value=True,
                )

            run_btn = gr.Button("🚀 処理を開始する (Run Pipeline)", variant="primary", elem_classes=["primary-btn"])

        # ⑥ 実行ログ（ページ最下部にワイド表示）
        with gr.Column(elem_classes=["section-block"]):
            gr.HTML('<div class="section-title">📜 実行ログ & 進捗状況</div>')
            log_output = gr.Textbox(
                label="ログコンソール",
                show_label=False,
                lines=12,
                max_lines=25,
                interactive=False,
                autoscroll=True,
                elem_classes=["log-box"],
            )

        # イベントハンドラ
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
