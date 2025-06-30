# Local Translation - Chunker Module

LM Studioを使用したローカルテキスト分割機能です。

## 前提条件

1. LM Studioがインストールされていること
2. gemma-3n-e4b-it-textモデルがロードされていること
3. LM Studioサーバーが http://127.0.0.1:1234 で起動していること

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

### 文単位チャンカー（推奨）

意味論的に綺麗な分割が必要な場合に使用します。話題の境界で適切に分割されます。

```bash
# 基本的な使用方法
python sentence_based_chunker.py input.txt

# 出力ディレクトリを指定
python sentence_based_chunker.py input.txt output_dir
```

**特徴:**
- 文単位での逐次判定による話題分割
- LLMを使用した話題転換判定
- サイズ制限と最小サイズ制限の組み合わせ
- 保守的処理（LLMエラー時は分割せずに継続）

### シンプルチャンカー（安定版）

安定した分割が必要な場合に使用します。ルールベースで高速処理が可能です。

```bash
# 基本的な使用方法
python simple_chunker.py input.txt

# 出力ディレクトリを指定
python simple_chunker.py input.txt output_dir
```

**特徴:**
- 段落ベースのルールベース分割
- サイズ制限とオーバーラップ機能
- 高速処理
- 安定した動作

### 段階的チャンカー（実験版）

高度な話題境界検出が必要な場合に使用します。

```bash
# ProgressiveChunkerV2
python progressive_chunker_v2.py input.txt

# ProgressiveChunker
python progressive_chunker.py input.txt
```

**特徴:**
- スライディングウィンドウによる話題境界検出
- 段階的処理による高精度分割
- 大きなテキストでの処理に制限あり

### 基本チャンカー

```bash
# 基本的な使用方法（スマート分割）
python chunker.py input.txt

# 出力ディレクトリを指定
python chunker.py input.txt output_dir

# 最大チャンクサイズを指定
python chunker.py input.txt output_dir 800

# 基本的な分割を使用
python chunker.py input.txt output_dir 1000 false
```

### Pythonスクリプトから使用

```python
from sentence_based_chunker import SentenceBasedChunker
from simple_chunker import SimpleChunker

# 文単位チャンカー
chunker = SentenceBasedChunker()
success = chunker.chunk_file("input.txt", "output_dir")

# シンプルチャンカー
chunker = SimpleChunker()
success = chunker.chunk_file("input.txt", "output_dir")
```

## 機能比較

| チャンカー | 分割精度 | 処理速度 | 安定性 | 推奨用途 |
|-----------|---------|---------|--------|----------|
| 文単位チャンカー | 高 | 中 | 高 | 意味論的分割が必要 |
| シンプルチャンカー | 中 | 高 | 高 | 安定した分割が必要 |
| 段階的チャンカー | 高 | 低 | 中 | 高度な話題境界検出 |
| 基本チャンカー | 中 | 中 | 中 | 基本的な分割 |

## 機能

- **意味的分割**: 文や段落の境界を尊重した分割
- **話題境界検出**: LLMを使用した話題転換判定
- **スマート分割**: LM Studioを使用した高度な分割
- **基本分割**: ルールベースの分割（フォールバック）
- **メタデータ生成**: 分割情報のJSONファイル生成
- **重複制御**: チャンク間の重複文字数制御

## パラメータ

### 文単位チャンカー
- `max_chunk_size`: 最大チャンクサイズ（デフォルト: 2000文字）
- `min_chunk_size`: 最小チャンクサイズ（デフォルト: 300文字）
- `server_url`: LM StudioサーバーURL（デフォルト: http://127.0.0.1:1234）

### シンプルチャンカー
- `max_chunk_size`: 最大チャンクサイズ（デフォルト: 2000文字）
- `min_chunk_size`: 最小チャンクサイズ（デフォルト: 300文字）
- `overlap`: チャンク間の重複文字数（デフォルト: 200文字）

### 基本チャンカー
- `max_chunk_size`: 各チャンクの最大文字数（デフォルト: 1000）
- `use_smart_chunking`: スマート分割を使用するか（デフォルト: True）
- `overlap`: チャンク間の重複文字数（基本分割のみ）

## 出力

- `chunk_001.txt`, `chunk_002.txt`, ...: 分割されたテキストファイル
- `metadata.json`: 分割情報のメタデータファイル

## 分割方法

### 文単位分割（推奨）
- 文単位での逐次判定による話題分割
- LLMによる話題転換判定
- サイズ制限と最小サイズ制限の組み合わせ
- 保守的処理

### 段落分割
- 段落単位での分割
- サイズ制限とオーバーラップ機能
- 高速処理
- 安定した動作

### スマート分割
- LM Studioを使用して意味的なまとまりで分割
- 文や段落の境界を尊重
- より自然な分割結果

### 基本分割
- ルールベースの分割
- 段落単位での分割
- 長い段落は文単位で分割
- フォールバック機能として使用 