# Local Translation - Translator Module

LM Studioを使用したローカル翻訳機能です。

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
# 基本的な使用方法
python translator.py input.txt

# 出力ファイル名を指定
python translator.py input.txt output.txt
```

### Pythonスクリプトから使用

```python
from translator import Translator

# 翻訳器の初期化
translator = Translator()

# ファイルを翻訳
success = translator.translate_file("input.txt", "output.txt")

# テキストを直接翻訳
translated_text = translator.translate_text("Hello, world!")
```

## 機能

- **言語検出**: 入力テキストの言語を自動検出
- **日本語スキップ**: 日本語テキストの場合は翻訳をスキップ
- **ローカル処理**: LM Studioを使用したローカル翻訳
- **ファイル対応**: .txt, .mdなどのテキストファイルに対応

## テスト

テストファイルが含まれています：

- `test_english.txt`: 英語テキストのテスト用
- `test_japanese.txt`: 日本語テキストのテスト用

```bash
# 英語テキストの翻訳テスト
python translator.py test_english.txt

# 日本語テキストのスキップテスト
python translator.py test_japanese.txt
``` 