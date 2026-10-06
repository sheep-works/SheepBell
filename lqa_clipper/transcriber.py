import os
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
import torch

_whisper_models: Dict[str, Any] = {}


def _get_whisper_model(
    model_size: str = "base",
    device: Optional[str] = None,
    compute_type: Optional[str] = None,
):
    """Load and cache faster-whisper model with graceful CPU fallback on CUDA errors."""
    from faster_whisper import WhisperModel

    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    if compute_type is None:
        compute_type = "float16" if device == "cuda" else "int8"

    key = f"{model_size}_{device}_{compute_type}"
    if key in _whisper_models:
        return _whisper_models[key]

    # Try loading on desired device (e.g. CUDA)
    try:
        model = WhisperModel(
            model_size_or_path=model_size,
            device=device,
            compute_type=compute_type,
        )
        _whisper_models[key] = model
        return model
    except Exception as e:
        # If CUDA library missing (e.g. libcublas.so.12 in Colab), fallback to CPU automatically
        if device == "cuda":
            print(f"⚠️ CUDAでのモデル読み込みに失敗しました ({e})。CPUモード (int8) に自動フォールバックします。")
            fallback_key = f"{model_size}_cpu_int8"
            if fallback_key not in _whisper_models:
                _whisper_models[fallback_key] = WhisperModel(
                    model_size_or_path=model_size,
                    device="cpu",
                    compute_type="int8",
                )
            return _whisper_models[fallback_key]
        raise e


def _read_wav_slice(
    wav_path: Union[str, Path],
    start_sec: float,
    end_sec: float,
) -> np.ndarray:
    """Read a specific time slice of a WAV file as a 1D float32 numpy array."""
    with wave.open(str(wav_path), "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()

        start_frame = max(0, int(start_sec * framerate))
        end_frame = int(end_sec * framerate)
        num_frames = max(0, end_frame - start_frame)

        wf.setpos(start_frame)
        data = wf.readframes(num_frames)

    if sampwidth == 2:
        audio_np = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
    elif sampwidth == 4:
        audio_np = np.frombuffer(data, dtype=np.int32).astype(np.float32) / 2147483648.0
    elif sampwidth == 1:
        audio_np = (np.frombuffer(data, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
    else:
        audio_np = np.frombuffer(data, dtype=np.float32)

    if n_channels > 1:
        audio_np = audio_np.reshape(-1, n_channels).mean(axis=1)

    return audio_np


def transcribe_issues(
    wav_path: Union[str, Path],
    issues: List[Dict[str, Any]],
    model_size: str = "base",
    language: Optional[str] = "ja",
    device: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Transcribe speech for each issue using Faster-Whisper and populate description."""
    wav_path = Path(wav_path).resolve()
    if not wav_path.exists():
        raise FileNotFoundError(f"WAV audio file not found: {wav_path}")

    if not issues:
        return []

    model = _get_whisper_model(model_size=model_size, device=device)

    # Clean language code
    target_lang = None
    if language:
        clean_lang = language.split()[0].lower().strip()
        if clean_lang not in ("auto", "none", ""):
            target_lang = clean_lang

    for issue in issues:
        start_ts = issue.get("timestamp_start", 0.0)
        end_ts = issue.get("timestamp_end", 0.0)

        if end_ts <= start_ts:
            continue

        audio_segment = _read_wav_slice(wav_path, start_ts, end_ts)
        if len(audio_segment) == 0:
            continue

        try:
            segments_gen, info = model.transcribe(
                audio=audio_segment,
                language=target_lang,
                beam_size=5,
                vad_filter=False,
            )
            texts = [seg.text.strip() for seg in segments_gen if seg.text.strip()]
            transcription = " ".join(texts)
        except Exception as e:
            # If transcription execution itself triggers CUDA error, fallback to CPU model
            print(f"⚠️ 文字起こし実行中にエラーが発生しました ({e})。CPUで再試行します。")
            cpu_model = _get_whisper_model(model_size=model_size, device="cpu", compute_type="int8")
            segments_gen, info = cpu_model.transcribe(
                audio=audio_segment,
                language=target_lang,
                beam_size=5,
                vad_filter=False,
            )
            texts = [seg.text.strip() for seg in segments_gen if seg.text.strip()]
            transcription = " ".join(texts)

        issue["description"] = transcription

    return issues
