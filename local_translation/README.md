# Local Translation

ローカル環境でLM Studioを使用した翻訳・要約・チャンキングツール群

## 概要

このプロジェクトは、LM Studioで動作するローカルLLM（gemma-3n-e4b-it-text等）を使用して、以下の機能を提供します：

- **翻訳**: 英語から日本語への翻訳（言語検出機能付き）
- **要約**: 長文テキストの要約（日本語・英語対応）
- **チャンキング**: セマンティックなテキスト分割

## 構成

```
local_translation/
├── translator/          # 翻訳機能
├── summarizer/          # 要約機能  
├── chunker/            # チャンキング機能
├── sample/             # サンプルファイル
├── docs/               # ドキュメント
└── AGENTS.md           # 開発ガイドライン
```

## 前提条件

- Python 3.8以上
- LM Studio（ローカルLLMサーバー）
- gemma-3n-e4b-it-text等の多言語対応モデル

## セットアップ

### 1. LM Studioの設定

1. LM Studioを起動
2. gemma-3n-e4b-it-text等のモデルをダウンロード
3. ローカルサーバーを起動（デフォルト: http://localhost:1234/v1）。
   必要に応じて環境変数 `LM_STUDIO_SERVER_URL` でURLを指定できます

### 2. 各機能のセットアップ

各機能ディレクトリで個別にセットアップを行います：

```bash
# 翻訳機能
cd translator
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 要約機能
cd ../summarizer
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# チャンキング機能
cd ../chunker
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 使用方法

### 翻訳

```bash
cd translator
python translator.py input.txt output.txt
```

### 要約

```bash
cd summarizer
python summarizer.py input.txt --output output.txt --language ja
```

### チャンキング

```bash
cd chunker
python sentence_based_chunker.py input.txt output_dir/
```

## 特徴

- **言語検出**: 自動的に日本語テキストを検出し、翻訳をスキップ
- **セマンティックチャンキング**: 意味的な境界でテキストを分割
- **略語保護**: 略語リストを使用した正確な文分割
- **構造保持**: 元のテキストの段落構造と改行を保持

## 開発ガイドライン

開発時は `AGENTS.md` を参照してください。

## ライセンス

MIT License 