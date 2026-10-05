# SheepBell - ゲームLQA用 自動動画クリップ & 文字起こしツール

OBS等で録画されたゲームプレイ動画の特定マイク音声トラックから「テスターの発話区間」を自動検知し、**全音声トラック保持動画クリップ・開始0.1秒スナップショット画像・Faster-Whisper文字起こし・CSV/JSON構造化データ**を自動生成するツールです。

## 🌟 主な機能
- **4ステップ疎結合設計**:
  - **Step 1 (マイク音声抽出)**: FFmpegを用いて指定トラックから16kHzモノラルWAVを高速抽出
  - **Step 2 (発話区間検出)**: PyTorch Silero VADにより高精度に発話タイムスタンプを検出
  - **Step 3 (マージ & 文字起こし & 出力)**:
    - 無音許容時間・前後マージンを考慮して発話を統合
    - **Faster-Whisper**（ローカル実行 / APIキー不要）により各区間の発話を自動テキスト化（日・英・中・自動検出）
    - `lqa_issues.json` および **Excel/Googleスプレッドシート互換の `lqa_issues.csv` (UTF-8 BOM)** を同時出力
  - **Step 4 (全トラック保持クリップ & 静止画生成)**:
    - FFmpeg `-map 0 -c copy` により、ゲーム音・マイク音など**全音声トラックを保持したまま再エンコードなしで数秒で切り出し**
    - 各Issueの開始+0.1秒のスナップショット画像（`issue_001.png`）を自動生成
- **直感的なWeb UI (Gradio)**:
  - ファイル名Prefix（例: `stage1`, `bug`）や開始ID番号（例: `10`）を指定可能
  - パラメータ調整、ステップ個別実行、リアルタイム実行ログ表示

---

## 💻 ローカル環境での実行 (Windows / Mac / Linux)

### 前提条件
- **Python 3.10+** (uv 推奨)

### 起動方法
```bash
# 依存関係のインストール
uv sync

# Gradio UI の起動
uv run python app.py
```
ブラウザで `http://127.0.0.1:7860` を開いてください。

---

## ☁️ Google Colab での実行 (GPU無料枠対応)

リポジトリ直下の [`colab_sheepbell.ipynb`](colab_sheepbell.ipynb) を Google Colab にアップロードして実行するだけで、GPU（T4）環境上で爆速文字起こし＆動画切り出しが可能です。

1. Google Colab で `colab_sheepbell.ipynb` を開く（ランタイムのタイプを「T4 GPU」に設定）。
2. Google Drive をマウント（動画ファイルの受け渡しがスムーズになります）。
3. セルを実行して `!python app.py --share` を起動。
4. 発行された `https://xxxx.gradio.live` のURLを開いて利用。

---

## 🧪 テスト実行

```bash
uv run pytest
```
