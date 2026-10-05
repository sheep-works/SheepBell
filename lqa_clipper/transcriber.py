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
    """Load and cache faster-whisper model."""
    from faster_whisper import WhisperModel

    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    if compute_type is None:
        compute_type = "float16" if device == "cuda" else "int8"

    key = f"{model_size}_{device}_{compute_type}"
    if key not in _whisper_models:
        _whisper_models[key] = WhisperModel(
            model_size_or_path=model_size,
            device=device,
            compute_type=compute_type,
        )
    return _whisper_models[key]


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
    """Transcribe speech for each issue using Faster-Whisper and populate description.

    Args:
        wav_path: Path to the 16kHz mono WAV file (extracted microphone track).
        issues: List of issue dictionaries from Step 3.
        model_size: Faster-Whisper model size ('tiny', 'base', 'small', 'medium', 'large-v3').
        language: Language code ('ja', 'en', 'zh', or 'auto'/None for auto-detection).
        device: 'cpu', 'cuda', or None for auto-detection.

    Returns:
        Updated list of issue dictionaries with 'description' populated.
    """
    wav_path = Path(wav_path).resolve()
    if not wav_path.exists():
        raise FileNotFoundError(f"WAV audio file not found: {wav_path}")

    if not issues:
        return []

    model = _get_whisper_model(model_size=model_size, device=device)

    # Clean language code (e.g. 'auto', 'zh (中国語)' -> 'zh')
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

        segments_gen, info = model.transcribe(
            audio=audio_segment,
            language=target_lang,
            beam_size=5,
            vad_filter=False,
        )

        texts = [seg.text.strip() for seg in segments_gen if seg.text.strip()]
        transcription = " ".join(texts)

        issue["description"] = transcription

    return issues
