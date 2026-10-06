# SheepBell LQA Issues Editor (SPA)

SheepBell で生成された `lqa_issues.json`、動画クリップ、スナップショット画像をブラウザ上で一覧・プレビュー・編集・保存できる Vue 3 + Vuetify 3 製の SPA (Single Page Application) です。

## 🌟 主な特徴
- **File System Access API 連携**: フォルダ（`sample/issues` など）を選択するだけで、直接読み込みと上書き保存が可能。
- **軽量 Lazy ロード**: 大量の画像・動画があっても画面表示時にオンデマンドで読み込むため高速・省メモリ。
- **Vuetify DataTable 表組み**:
  - **ID / ツールチップ**: 開始・終了タイムスタンプや動画長をホバー表示
  - **スナップショット**: サムネイル表示＆クリックで拡大モーダル
  - **動画クリップ**: クリックで動画再生モーダル（再生・停止・タイムスタンプ確認）
  - **Description & Comment**: 行内で直接編集可能な自動リサイズテキストエリア
- **Ctrl + S ショートカット**: ブラウザの標準保存をフックし、`lqa_issues.json` に即時上書き保存。
- **CSV / JSON エクスポート**: Excel 互換の UTF-8 BOM 付き CSV ダウンロードに対応。
- **検索 & フィルタ**: キーワード検索、コメント有無、タグによる絞り込み。
- **ダークモード / ライトモード**: SheepBell の Teal テーマに準拠した切り替え可能な UI。

## 🚀 起動方法

```bash
# viewer ディレクトリに移動
cd viewer

# 依存関係のインストール (初回のみ)
yarn install

# 開発サーバーの起動
yarn dev
```

起動後、ブラウザで `http://localhost:5173` が自動で開きます。

## 📦 ビルド

```bash
yarn build
```
ビルド成果物は `viewer/dist` に出力され、静的Webサーバー（GitHub Pages、Vercel、S3、ローカルHTTPサーバー等）にそのままホスティング可能です。
