import wave
from pathlib import Path
from typing import Dict, List, Optional, Union
import numpy as np
import torch


_silero_model = None
_silero_get_timestamps = None


def load_audio_as_tensor(wav_path: Union[str, Path]) -> torch.Tensor:
    """Read a WAV file as a 1D float32 torch.Tensor normalized between [-1.0, 1.0].

    Uses standard library wave module to avoid torchaudio/torchcodec binary backend issues on Windows.
    """
    with wave.open(str(wav_path), "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        n_frames = wf.getnframes()
        data = wf.readframes(n_frames)

    if sampwidth == 2:  # 16-bit PCM
        audio_np = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
    elif sampwidth == 4:  # 32-bit PCM
        audio_np = np.frombuffer(data, dtype=np.int32).astype(np.float32) / 2147483648.0
    elif sampwidth == 1:  # 8-bit PCM
        audio_np = (np.frombuffer(data, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
    else:
        audio_np = np.frombuffer(data, dtype=np.float32)

    if n_channels > 1:
        audio_np = audio_np.reshape(-1, n_channels).mean(axis=1)

    return torch.from_numpy(audio_np)


def _get_silero_vad_model():
    """Load and cache the Silero VAD model."""
    global _silero_model, _silero_get_timestamps
    if _silero_model is None or _silero_get_timestamps is None:
        try:
            from silero_vad import load_silero_vad, get_speech_timestamps
            model = load_silero_vad()
            _silero_model = model
            _silero_get_timestamps = get_speech_timestamps
        except Exception:
            model, utils = torch.hub.load(
                repo_or_dir="snakers4/silero-vad",
                model="silero_vad",
                force_reload=False,
                trust_repo=True,
            )
            _silero_model = model
            _silero_get_timestamps = utils[0]
    return _silero_model, _silero_get_timestamps


def detect_speech_segments(
    wav_path: Union[str, Path],
    vad_threshold: float = 0.5,
    sampling_rate: int = 16000,
) -> List[Dict[str, float]]:
    """Step 2: Detect raw speech segments using Silero VAD.

    Args:
        wav_path: Path to the 16kHz mono WAV file.
        vad_threshold: Speech threshold for Silero VAD (0.0 - 1.0).
        sampling_rate: Audio sampling rate (default: 16000).

    Returns:
        List of dicts containing raw start and end timestamps in seconds:
        [{'start': 12.5, 'end': 18.2}, ...]

    Raises:
        FileNotFoundError: If wav_path does not exist.
        RuntimeError: If VAD processing fails.
    """
    wav_path = Path(wav_path).resolve()
    if not wav_path.exists():
        raise FileNotFoundError(f"WAV audio file not found: {wav_path}")

    model, get_speech_timestamps = _get_silero_vad_model()

    try:
        wav = load_audio_as_tensor(wav_path)
        raw_timestamps = get_speech_timestamps(
            wav,
            model,
            threshold=vad_threshold,
            sampling_rate=sampling_rate,
            return_seconds=True,
        )
    except Exception as e:
        raise RuntimeError(f"Silero VAD speech detection failed: {e}") from e

    segments = []
    for ts in raw_timestamps:
        segments.append({
            "start": round(float(ts["start"]), 2),
            "end": round(float(ts["end"]), 2),
        })

    return segments
