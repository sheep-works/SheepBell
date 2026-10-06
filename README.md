[English](README.md) | [日本語](README_ja.md) | [简体中文](README_zh.md)

# SheepBell - Automatic Video Clipping & Transcription Tool for Game LQA

An automated tool that detects the "tester's speech segments" from a specific microphone audio track in game play videos recorded with tools like OBS. It automatically generates **video clips preserving all audio tracks, snapshot images at the first 0.1s, transcripts using Faster-Whisper, and structured data in CSV/JSON format**.

## 🌟 Key Features
- **4-Step Loosely Coupled Design**:
  - **Step 1 (Microphone Audio Extraction)**: High-speed extraction of a 16kHz mono WAV from the specified track using FFmpeg.
  - **Step 2 (Voice Activity Detection)**: High-accuracy detection of speech timestamps using PyTorch Silero VAD.
  - **Step 3 (Merging, Transcription & Output)**:
    - Merges speech segments considering allowable silence duration and margins.
    - Automatically transcribes speech for each segment using **Faster-Whisper** (runs locally / no API key required, supports EN, JA, ZH, and auto-detection).
    - Simultaneously outputs `lqa_issues.json` and **Excel/Google Spreadsheet compatible `lqa_issues.csv` (UTF-8 BOM)**.
  - **Step 4 (Clip & Image Generation with All Tracks)**:
    - Clips videos in a few seconds **without re-encoding, preserving all audio tracks (game sound, microphone, etc.)** using FFmpeg `-map 0 -c copy`.
    - Automatically generates a snapshot image at the start + 0.1s for each issue (e.g., `issue_001.png`).
- **Intuitive Web UI (Gradio)**:
  - Specify file name prefixes (e.g., `stage1`, `bug`) and starting ID numbers (e.g., `10`).
  - Parameter adjustment, individual step execution, and real-time log display.

---

## Preparing Video Files

For SheepBell, it is recommended to record the tester's voice on a separate audio track from the game or desktop audio.
Using a separate audio track prevents the tester's voice from being masked by the game audio and avoids false positives when the game has its own voiceovers.

Below is an example setup using OBS:

1. Click the gear icon in the **Audio Mixer** pane and open **Advanced Audio Properties**.

![OBS Audio pane](./imgs/audio_pane.png)

2. Assign the microphone audio to Track 2 and the game audio to Track 1. Make sure the other tracks are unchecked for each source.

![OBS Audio tracks](./imgs/audio_tracks.png)

*Note: In this example, the desktop audio is muted, so its settings are not changed. Please adjust according to your environment.*

3. Click **Settings** in the **Controls** pane.

![OBS Control pane](./imgs/control_pane.png)

4. Go to the **Output** tab, open the **Recording** section, and ensure that all the tracks you want to output are checked in the Audio Track section.

![OBS Recording settings](./imgs/recording_settings.png)

Now, the created video file will contain all the specified audio tracks.

To check if it recorded correctly, you can view the info with MediaInfo or try selecting different audio tracks in VLC or other media players.

> [!NOTE]
> SheepBell allows a 30-second preview on the audio track selection screen.
> We recommend recording a short message before starting the test (e.g., "Today is [Date], starting test for [Feature]") as it makes track identification easier and serves as an index for the test.

## Running the Program

SheepBell can be run locally or on Google Colab.
To run locally, `uv` or `python` is required. If setting up a local environment is difficult, we recommend using Google Colab.

### 💻 Local Execution (Windows / Mac / Linux)

#### Prerequisites
- **Python 3.10+** (`uv` recommended)

#### Startup Instructions
```bash
# Install dependencies
uv sync

# Launch the Gradio UI
uv run python app.py
```
Open `http://127.0.0.1:7860` in your browser.

---

### ☁️ Execution on Google Colab (Free GPU supported)

Simply upload [`colab_sheepbell.ipynb`](colab_sheepbell.ipynb) from the root of the repository to Google Colab and run it to perform lightning-fast transcription & video clipping on a GPU (T4) environment.

1. Open `colab_sheepbell.ipynb` in Google Colab (Set Runtime type to "T4 GPU").
2. Mount Google Drive (Recommended for smooth transfer of video files).
3. Run the cells to launch `!python app.py --share`.
4. Open the generated `https://xxxx.gradio.live` URL to use the tool.

---

Alternatively, you can open the Google Colab notebook from the URL below, select **File** > **Save a copy in Drive**, and use it in your own drive.
[Open in Google Colab](https://colab.research.google.com/drive/1ecQ15UvafD5_uotnd15CYwU6WC7dPNND?usp=sharing)

### 🧪 Running Tests

```bash
uv run pytest
```

## Usage

### UI Overview

![SheepBell UI overview](./imgs/ui_overview.png)

### Steps

1. Enter the video file path (Absolute or relative path. Relative path is recommended when running on Colab).
2. (If you have multiple videos) Set the output directory, file naming rules, index start number, etc.
3. Confirm the audio track. Previewing it is the most reliable way.
4. Select the language if you want to transcribe.
5. Click "Start Processing".
6. Wait for the completion message in the log.

The following items will be created in the specified folder:

1. A file summarizing the issues (JSON and CSV. And a spreadsheet if run on Colab).
2. Screenshots and video clips of the issues.

> [!NOTE]
> The above settings will work with default values except for the specified fields.
> If you need higher accuracy, fine-tuning will be required. In that case, please repeat the test a few times to find the optimal values.
