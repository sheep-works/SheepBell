[English](README.md) | [日本語](README_ja.md) | [简体中文](README_zh.md)

# SheepBell - 游戏LQA用 自动视频剪辑与语音转写工具

这是一款自动化工具，用于从使用OBS等工具录制的游戏演示视频中，通过特定的麦克风音频轨道自动检测“测试人员的发言片段”，并**自动生成保留所有音轨的视频剪辑、起始0.1秒的截图、基于Faster-Whisper的语音转写，以及CSV/JSON格式的结构化数据**。

## 🌟 主要功能
- **4步松耦合设计**:
  - **步骤 1 (提取麦克风音频)**: 使用 FFmpeg 高速提取指定轨道的 16kHz 单声道 WAV。
  - **步骤 2 (语音活动检测)**: 使用 PyTorch Silero VAD 高精度检测发言时间戳。
  - **步骤 3 (合并、转写与输出)**:
    - 结合允许的静音时间和前后冗余时间合并发言片段。
    - 使用 **Faster-Whisper**（本地运行 / 无需API密钥）自动将各片段的语音转换为文本（支持日/英/中/自动检测）。
    - 同时输出 `lqa_issues.json` 和 **兼容 Excel/Google 表格的 `lqa_issues.csv` (UTF-8 BOM)**。
  - **步骤 4 (保留所有音轨的剪辑与截图生成)**:
    - 使用 FFmpeg `-map 0 -c copy`，**保留所有音轨（游戏声音、麦克风声音等），且无需重新编码，几秒内即可完成视频剪辑**。
    - 为每个Issue自动生成起始+0.1秒的截图（如：`issue_001.png`）。
- **直观的 Web UI (Gradio)**:
  - 可指定文件名前缀（例：`stage1`, `bug`）和起始编号（例：`10`）。
  - 支持参数调整、单独执行每个步骤以及实时查看执行日志。

---

## 准备视频文件

在 SheepBell 中，建议将测试人员的声音记录在与游戏或桌面音频不同的独立音轨上。
使用独立音轨可以防止测试人员的声音被游戏音频掩盖，同时也能避免当游戏本身包含语音时产生的误检。

以下是使用 OBS 的设置示例：

1. 在 **混音器** 面板中点击齿轮图标，打开 **高级音频属性**。

![OBS Audio pane](./imgs/audio_pane.png)

2. 将麦克风音频分配给轨道 2，将游戏音频分配给轨道 1。请确保每个音源未勾选其他轨道。

![OBS Audio tracks](./imgs/audio_tracks.png)

※ 在此示例中，桌面音频已静音，因此未对其设置进行更改。请根据您的环境进行适当调整。

3. 点击 **控件** 面板中的 **设置**。

![OBS Control pane](./imgs/control_pane.png)

4. 进入 **输出** 选项卡，打开 **录像** 部分，并确保在“音频轨道”中勾选了所有想要输出的轨道。

![OBS Recording settings](./imgs/recording_settings.png)

现在，生成的视频文件将包含所有指定的音轨。

若要检查录制是否正常，可以使用 MediaInfo 查看信息，或在 VLC 等媒体播放器中尝试选择不同的音轨进行确认。

> [!NOTE]
> SheepBell 在音轨选择界面支持 30 秒的预览功能。
> 建议在开始测试前录制一段简短说明（如：“今天是某月某日，现在开始进行某项测试”），这样不仅便于分辨音轨，还能作为测试的索引。

## 运行程序

SheepBell 可以在本地环境或 Google Colab 上运行。
本地运行需要 `uv` 或 `python`。如果本地环境配置较为困难，建议使用 Google Colab 运行。

### 💻 本地运行 (Windows / Mac / Linux)

#### 前提条件
- **Python 3.10+** (推荐使用 `uv`)

#### 启动方法
```bash
# 安装依赖
uv sync

# 启动 Gradio UI
uv run python app.py
```
在浏览器中打开 `http://127.0.0.1:7860`。

---

### ☁️ 在 Google Colab 上运行 (支持免费 GPU)

只需将仓库根目录下的 [`colab_sheepbell_zh.ipynb`](colab_sheepbell_zh.ipynb) 上传至 Google Colab 并运行，即可在 GPU (T4) 环境下实现极速的语音转写和视频剪辑。

1. 在 Google Colab 中打开 `colab_sheepbell_zh.ipynb`（将运行时类型设置为“T4 GPU”）。
2. 挂载 Google Drive（便于顺畅地传输视频文件）。
3. 运行单元格启动 `!python app.py --share`。
4. 打开生成的 `https://xxxx.gradio.live` URL 即可使用。

---

或者，您也可以通过下方链接打开 Google Colab 笔记本，选择 **文件** > **在云端硬盘中保存一份副本**，然后在自己的云端硬盘中使用。
[在 Google Colab 中打开](https://colab.research.google.com/drive/1iQmeyp9ctm4HLiS57mXDZO1_nLc8vLnz?usp=sharing)

### 🧪 运行测试

```bash
uv run pytest
```

## 使用方法

### 界面概览

![SheepBell UI overview](./imgs/ui_overview.png)

### 操作步骤

1. 输入视频文件路径（绝对路径或相对路径均可。在 Colab 上运行时推荐使用相对路径）。
2. （如有多个视频）设置输出目录、命名规则、索引起始编号等。
3. 确认音轨。最可靠的方法是直接试听。
4. 如需转写文本，请选择对应语言。
5. 点击“开始处理”。
6. 等待日志中显示完成。

处理完成后，将在指定的文件夹中生成以下内容：

1. 汇总问题的记录文件（JSON 和 CSV。如果在 Colab 上运行，还会生成电子表格）。
2. 问题片段的截图和视频。

> [!NOTE]
> 除了以上需要指定的选项，其它设置项在默认参数下均可正常工作。
> 若需要更高的精度，可能需要进行微调。此时，请多次重复测试以找到最佳参数。
