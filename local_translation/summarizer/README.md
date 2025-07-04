# Local Translation - Summarizer Module

LM Studioを使用したローカル要約機能です。

## 前提条件

1. LM Studioがインストールされていること
2. gemma-3n-e4b-it-textモデルがロードされていること
3. LM Studioサーバーが起動していること（デフォルト: http://127.0.0.1:1234、
   環境変数 `LM_STUDIO_SERVER_URL` で変更可能）

## セットアップ

1. 仮想環境を作成してアクティベート：
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate  # Windows
```

2. 依存関係をインストール：
```bash
pip install -r requirements.txt
```

## 使用方法

### コマンドラインから実行

```bash
# 基本的な使用方法（日本語要約）
python summarizer.py input.txt

# 最大文字数を指定
python summarizer.py input.txt --max-length 500

# 英語で要約
python summarizer.py input.txt --max-length 500 --language 英語

# 出力ファイル名を指定
python summarizer.py input.txt --output output.txt --max-length 500 --language 日本語
```

### Pythonスクリプトから使用

```python
from summarizer import Summarizer

# 要約器の初期化
summarizer = Summarizer()

# ファイルを要約
success = summarizer.summarize_file("input.txt", "output.txt", 500, "日本語")

# テキストを直接要約
summarized_text = summarizer.summarize_text("Long text content...", 500, "英語")
```

## 機能

- **多言語対応**: 日本語・英語での要約に対応
- **文字数制御**: 要約の最大文字数を指定可能
- **ローカル処理**: LM Studioを使用したローカル要約
- **ファイル対応**: .txt, .mdなどのテキストファイルに対応
- **自動ファイル名生成**: 出力ファイル名を自動生成

## パラメータ

- `max_length`: 要約の最大文字数（デフォルト: 500）
- `language`: 要約言語（"日本語" または "英語"、デフォルト: "日本語"）

## 出力ファイル

- 日本語要約: `{filename}_summary.txt`
- 英語要約: `{filename}_summary_en.txt` 