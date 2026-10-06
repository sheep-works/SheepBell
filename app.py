import argparse
import os
from pathlib import Path
from typing import Optional
import gradio as gr

from lqa_clipper import __version__
from lqa_clipper.pipeline import run_pipeline
from lqa_clipper.audio_extractor import extract_preview_audio
from lqa_clipper.i18n import get_locale, get_language_choices


# デフォルト値の定義
DEFAULT_VALUES = {
    "video_path": r"sample/sample_0game_1mic.mkv",
    "game_track_index": 0,
    "mic_track_index": 1,
    "mix_audio": True,
    "output_dir": "./issues",
    "file_prefix": "issue",
    "id_start_index": 1,
    "vad_threshold": 0.5,
    "min_silence_sec": 2.0,
    "margin_pre_sec": 2.0,
    "margin_post_sec": 2.0,
    "enable_transcription": True,
    "whisper_model": "base",
    "whisper_language": "ja (日本語)",
    "enable_snapshots": True,
    "snapshot_offset_sec": 0.1,
    "run_steps_1_to_3": True,
    "run_step_4": True,
}


def reset_to_defaults():
    """Reset all UI inputs to their default states."""
    return (
        DEFAULT_VALUES["video_path"],
        DEFAULT_VALUES["game_track_index"],
        DEFAULT_VALUES["mic_track_index"],
        DEFAULT_VALUES["mix_audio"],
        DEFAULT_VALUES["output_dir"],
        DEFAULT_VALUES["file_prefix"],
        DEFAULT_VALUES["id_start_index"],
        DEFAULT_VALUES["vad_threshold"],
        DEFAULT_VALUES["min_silence_sec"],
        DEFAULT_VALUES["margin_pre_sec"],
        DEFAULT_VALUES["margin_post_sec"],
        DEFAULT_VALUES["enable_transcription"],
        DEFAULT_VALUES["whisper_model"],
        DEFAULT_VALUES["whisper_language"],
        DEFAULT_VALUES["enable_snapshots"],
        DEFAULT_VALUES["snapshot_offset_sec"],
        DEFAULT_VALUES["run_steps_1_to_3"],
        DEFAULT_VALUES["run_step_4"],
        None,  # audio_preview
        "",    # log_output
    )


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
    game_track_index: int,
    mic_track_index: int,
    mix_audio: bool,
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
        game_track_index=int(game_track_index) if game_track_index is not None else 0,
        mic_track_index=int(mic_track_index) if mic_track_index is not None else 1,
        mix_audio=mix_audio,
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


def on_change_language(lang_code: str):
    """Dynamically update all UI components when language changes."""
    t = get_locale(lang_code)
    header_text = f"{t.get('header_title', '')}\n\n{t.get('header_subtitle', '')}"
    sec1_text = f'<div class="section-title">{t.get("section_1", "")}</div>'
    sec2_text = f'<div class="section-title">{t.get("section_2", "")}</div>'
    sec3_text = f'<div class="section-title">{t.get("section_3", "")}</div>'
    sec4_text = f'<div class="section-title">{t.get("section_4", "")}</div>'
    sec5_text = f'<div class="section-title">{t.get("section_5", "")}</div>'
    sec_log_text = f'<div class="section-title">{t.get("section_log", "")}</div>'

    return (
        gr.update(value=header_text),
        gr.update(value=sec1_text),
        gr.update(label=t.get("video_path_label"), placeholder=t.get("video_path_placeholder")),
        gr.update(label=t.get("output_dir_label")),
        gr.update(label=t.get("file_prefix_label"), info=t.get("file_prefix_info")),
        gr.update(label=t.get("id_start_index_label")),
        gr.update(value=sec2_text),
        gr.update(label=t.get("game_track_label"), info=t.get("game_track_info")),
        gr.update(label=t.get("mic_track_label"), info=t.get("mic_track_info")),
        gr.update(value=t.get("preview_btn")),
        gr.update(label=t.get("audio_preview_label")),
        gr.update(label=t.get("cb_mix_audio_label"), info=t.get("cb_mix_audio_info")),
        gr.update(value=sec3_text),
        gr.update(label=t.get("vad_threshold_label"), info=t.get("vad_threshold_info")),
        gr.update(label=t.get("min_silence_label"), info=t.get("min_silence_info")),
        gr.update(label=t.get("margin_pre_label"), info=t.get("margin_pre_info")),
        gr.update(label=t.get("margin_post_label"), info=t.get("margin_post_info")),
        gr.update(value=sec4_text),
        gr.update(label=t.get("cb_transcription_label")),
        gr.update(label=t.get("whisper_model_label")),
        gr.update(label=t.get("whisper_lang_label")),
        gr.update(label=t.get("cb_snapshots_label")),
        gr.update(label=t.get("snapshot_offset_label"), info=t.get("snapshot_offset_info")),
        gr.update(value=sec5_text),
        gr.update(label=t.get("cb_steps_1_to_3_label")),
        gr.update(label=t.get("cb_step_4_label")),
        gr.update(value=t.get("run_btn")),
        gr.update(value=t.get("reset_btn")),
        gr.update(value=sec_log_text),
        gr.update(label=t.get("lang_selector_label")),
    )


custom_css = """
/* 全体のフォントとベース調整 */
.gradio-container {
    max-width: 960px !important;
    margin: 0 auto !important;
}

/* 言語選択ヘッダー */
.top-bar {
    display: flex !important;
    justify-content: flex-end !important;
    margin-bottom: 8px !important;
}

/* セクション見出しのアンダーラインスタイル */
.section-title {
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    color: #14b8a6 !important;
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
    color: #94a3b8 !important;
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
}

/* リセットボタン */
.reset-btn {
    border-radius: 8px !important;
    padding: 12px 20px !important;
    color: #94a3b8 !important;
    border-color: #334155 !important;
}

/* ログ表示エリア（ターミナル風ダークスタイル） */
.log-box textarea {
    font-family: Consolas, 'Courier New', monospace !important;
    font-size: 0.88rem !important;
    line-height: 1.5 !important;
    background-color: #0b0f19 !important;
    color: #38bdf8 !important;
    border: 1px solid #1e293b !important;
    border-radius: 8px !important;
}

/* フッターバー */
.footer-bar {
    margin-top: 36px !important;
    padding: 20px 0 12px 0 !important;
    border-top: 1px solid #1e293b !important;
    text-align: center !important;
    font-size: 0.85rem !important;
    color: #64748b !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    gap: 12px !important;
}

.footer-bar a {
    color: #14b8a6 !important;
    text-decoration: none !important;
    transition: color 0.2s ease !important;
}

.footer-bar a:hover {
    color: #2dd4bf !important;
    text-decoration: underline !important;
}
"""


def create_app(initial_lang: str = "ja") -> gr.Blocks:
    """Create and configure the Gradio web interface with i18n support."""
    t = get_locale(initial_lang)
    lang_choices = get_language_choices()

    theme = gr.themes.Soft(
        primary_hue="teal",
        secondary_hue="slate",
        neutral_hue="slate",
    ).set(
        button_primary_background_fill="*primary_600",
        button_primary_background_fill_hover="*primary_700",
        button_primary_text_color="white",
    )

    with gr.Blocks(title=f"ゲームLQA 自動動画クリップツール v{__version__}", theme=theme, css=custom_css) as app:
        # 言語セレクター（右上）
        with gr.Row():
            gr.HTML('<div style="flex-grow: 1;"></div>')
            lang_selector = gr.Dropdown(
                label=t.get("lang_selector_label", "🌐 Display Language"),
                choices=lang_choices,
                value=initial_lang,
                scale=2,
                min_width=180,
            )

        header_md = gr.Markdown(
            f"{t.get('header_title', '')}\n\n{t.get('header_subtitle', '')}"
        )

        # ① 入力 & 出力設定
        with gr.Column(elem_classes=["section-block"]):
            sec1_html = gr.HTML(f'<div class="section-title">{t.get("section_1", "")}</div>')
            video_input = gr.Textbox(
                label=t.get("video_path_label"),
                placeholder=t.get("video_path_placeholder"),
                value=DEFAULT_VALUES["video_path"],
                lines=1,
            )
            with gr.Row():
                output_dir_input = gr.Textbox(
                    label=t.get("output_dir_label"),
                    value=DEFAULT_VALUES["output_dir"],
                    lines=1,
                    scale=6,
                )
                file_prefix_input = gr.Textbox(
                    label=t.get("file_prefix_label"),
                    value=DEFAULT_VALUES["file_prefix"],
                    info=t.get("file_prefix_info"),
                    scale=4,
                )
                id_start_index_input = gr.Number(
                    label=t.get("id_start_index_label"),
                    value=DEFAULT_VALUES["id_start_index"],
                    precision=0,
                    scale=2,
                )

        # ② 音声トラック & 試聴プレビュー & 音声ミックス設定
        with gr.Column(elem_classes=["section-block"]):
            sec2_html = gr.HTML(f'<div class="section-title">{t.get("section_2", "")}</div>')
            with gr.Row():
                game_track_input = gr.Number(
                    label=t.get("game_track_label"),
                    value=DEFAULT_VALUES["game_track_index"],
                    precision=0,
                    info=t.get("game_track_info"),
                    scale=3,
                )
                mic_track_input = gr.Number(
                    label=t.get("mic_track_label"),
                    value=DEFAULT_VALUES["mic_track_index"],
                    precision=0,
                    info=t.get("mic_track_info"),
                    scale=3,
                )
                preview_btn = gr.Button(t.get("preview_btn"), variant="secondary", scale=4)

            audio_preview = gr.Audio(
                label=t.get("audio_preview_label"),
                type="filepath",
                interactive=False,
            )

            cb_mix_audio = gr.Checkbox(
                label=t.get("cb_mix_audio_label"),
                value=DEFAULT_VALUES["mix_audio"],
                info=t.get("cb_mix_audio_info"),
            )

        # ③ 音声検出 (VAD) & マージ設定
        with gr.Column(elem_classes=["section-block"]):
            sec3_html = gr.HTML(f'<div class="section-title">{t.get("section_3", "")}</div>')
            with gr.Row():
                vad_threshold_slider = gr.Slider(
                    minimum=0.1,
                    maximum=0.9,
                    value=DEFAULT_VALUES["vad_threshold"],
                    step=0.05,
                    label=t.get("vad_threshold_label"),
                    info=t.get("vad_threshold_info"),
                )
                min_silence_slider = gr.Slider(
                    minimum=1.0,
                    maximum=10.0,
                    value=DEFAULT_VALUES["min_silence_sec"],
                    step=0.5,
                    label=t.get("min_silence_label"),
                    info=t.get("min_silence_info"),
                )
            with gr.Row():
                margin_pre_slider = gr.Slider(
                    minimum=0.0,
                    maximum=15.0,
                    value=DEFAULT_VALUES["margin_pre_sec"],
                    step=0.5,
                    label=t.get("margin_pre_label"),
                    info=t.get("margin_pre_info"),
                )
                margin_post_slider = gr.Slider(
                    minimum=0.0,
                    maximum=15.0,
                    value=DEFAULT_VALUES["margin_post_sec"],
                    step=0.5,
                    label=t.get("margin_post_label"),
                    info=t.get("margin_post_info"),
                )

        # ④ 文字起こし & スナップショット設定
        with gr.Column(elem_classes=["section-block"]):
            sec4_html = gr.HTML(f'<div class="section-title">{t.get("section_4", "")}</div>')
            with gr.Row():
                with gr.Column(scale=5):
                    cb_transcription = gr.Checkbox(
                        label=t.get("cb_transcription_label"),
                        value=DEFAULT_VALUES["enable_transcription"],
                    )
                    with gr.Row():
                        whisper_model_dd = gr.Dropdown(
                            label=t.get("whisper_model_label"),
                            choices=["tiny", "base", "small", "medium", "large-v3"],
                            value=DEFAULT_VALUES["whisper_model"],
                        )
                        whisper_lang_dd = gr.Dropdown(
                            label=t.get("whisper_lang_label"),
                            choices=[
                                "ja (日本語)",
                                "en (英語)",
                                "zh (中国語)",
                                "auto (自動検出)",
                            ],
                            value=DEFAULT_VALUES["whisper_language"],
                        )
                with gr.Column(scale=5):
                    cb_snapshots = gr.Checkbox(
                        label=t.get("cb_snapshots_label"),
                        value=DEFAULT_VALUES["enable_snapshots"],
                    )
                    snapshot_offset_slider = gr.Slider(
                        minimum=0.0,
                        maximum=2.0,
                        value=DEFAULT_VALUES["snapshot_offset_sec"],
                        step=0.05,
                        label=t.get("snapshot_offset_label"),
                        info=t.get("snapshot_offset_info"),
                    )

        # ⑤ 実行制御 & 開始ボタン
        with gr.Column(elem_classes=["section-block"]):
            sec5_html = gr.HTML(f'<div class="section-title">{t.get("section_5", "")}</div>')
            with gr.Row():
                cb_steps_1_to_3 = gr.Checkbox(
                    label=t.get("cb_steps_1_to_3_label"),
                    value=DEFAULT_VALUES["run_steps_1_to_3"],
                )
                cb_step_4 = gr.Checkbox(
                    label=t.get("cb_step_4_label"),
                    value=DEFAULT_VALUES["run_step_4"],
                )

            with gr.Row():
                run_btn = gr.Button(
                    t.get("run_btn"),
                    variant="primary",
                    elem_classes=["primary-btn"],
                    scale=8,
                )
                reset_btn = gr.Button(
                    t.get("reset_btn"),
                    variant="secondary",
                    elem_classes=["reset-btn"],
                    scale=2,
                )

        # ⑥ 実行ログ（ターミナル風ダーク表示）
        with gr.Column(elem_classes=["section-block"]):
            sec_log_html = gr.HTML(f'<div class="section-title">{t.get("section_log", "")}</div>')
            log_output = gr.Textbox(
                label="ログコンソール",
                show_label=False,
                lines=12,
                max_lines=25,
                interactive=False,
                autoscroll=True,
                elem_classes=["log-box"],
            )

        # ⑦ フッターバー (バージョン & GitHubリンク)
        gr.HTML(
            f"""
            <div class="footer-bar">
                <span>🐑 <strong>SheepBell</strong> v{__version__}</span>
                <span>•</span>
                <a href="https://github.com/sheep-works/SheepBell" target="_blank" rel="noopener noreferrer">
                    📦 GitHub Repository
                </a>
            </div>
            """
        )

        # 言語切り替えイベント
        lang_selector.change(
            fn=on_change_language,
            inputs=[lang_selector],
            outputs=[
                header_md,
                sec1_html,
                video_input,
                output_dir_input,
                file_prefix_input,
                id_start_index_input,
                sec2_html,
                game_track_input,
                mic_track_input,
                preview_btn,
                audio_preview,
                cb_mix_audio,
                sec3_html,
                vad_threshold_slider,
                min_silence_slider,
                margin_pre_slider,
                margin_post_slider,
                sec4_html,
                cb_transcription,
                whisper_model_dd,
                whisper_lang_dd,
                cb_snapshots,
                snapshot_offset_slider,
                sec5_html,
                cb_steps_1_to_3,
                cb_step_4,
                run_btn,
                reset_btn,
                sec_log_html,
                lang_selector,
            ],
        )

        # プレビュー試聴イベント
        preview_btn.click(
            fn=gradio_preview_audio,
            inputs=[video_input, mic_track_input, output_dir_input],
            outputs=[audio_preview],
        )

        # 実行イベント
        run_btn.click(
            fn=gradio_run,
            inputs=[
                video_input,
                game_track_input,
                mic_track_input,
                cb_mix_audio,
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

        # リセットイベント
        reset_btn.click(
            fn=reset_to_defaults,
            inputs=[],
            outputs=[
                video_input,
                game_track_input,
                mic_track_input,
                cb_mix_audio,
                output_dir_input,
                file_prefix_input,
                id_start_index_input,
                vad_threshold_slider,
                min_silence_slider,
                margin_pre_slider,
                margin_post_slider,
                cb_transcription,
                whisper_model_dd,
                whisper_lang_dd,
                cb_snapshots,
                snapshot_offset_slider,
                cb_steps_1_to_3,
                cb_step_4,
                audio_preview,
                log_output,
            ],
        )

    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SheepBell Gradio Web UI")
    parser.add_argument("--share", action="store_true", help="Create a publicly shareable Gradio link (for Colab)")
    parser.add_argument("--port", type=int, default=7860, help="Port to run the web server on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (e.g. 0.0.0.0 for containers)")
    parser.add_argument("--lang", type=str, default="ja", help="Initial language (ja, en, zh)")
    args = parser.parse_args()

    demo = create_app(initial_lang=args.lang)

    if args.share:
        # Colab mode: suppress confusing 0.0.0.0 URL and print clean share URL only
        _, _, share_url = demo.launch(
            server_name="0.0.0.0",
            server_port=args.port,
            share=True,
            quiet=True,
            prevent_thread_lock=True,
        )
        print("\n" + "=" * 60, flush=True)
        print(f"  🎉 SheepBell v{__version__} Web UI が起動しました！", flush=True)
        print("  以下のリンクをクリックしてブラウザで開いてください:", flush=True)
        print(f"  👉 {share_url}", flush=True)
        print("=" * 60 + "\n", flush=True)
        demo.block_thread()
    else:
        # Local mode
        demo.launch(
            server_name=args.host,
            server_port=args.port,
            share=False,
        )
