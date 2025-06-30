#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local Translation - Sentence-Based Chunker Module
文単位での逐次判定による話題分割機能
"""

import os
import sys
import requests
import json
import re
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import yaml


class SentenceBasedChunker:
    """文単位での逐次判定によるテキスト分割クラス"""
    
    def __init__(self, server_url: str = "http://127.0.0.1:1234", 
                 max_chunk_size: int = 2000, min_chunk_size: int = 300,
                 abbreviation_file: str = "common_abbreviations.yaml"):
        """
        初期化
        
        Args:
            server_url: LM StudioサーバーのURL
            max_chunk_size: 最大チャンクサイズ（文字数）
            min_chunk_size: 最小チャンクサイズ（文字数）
            abbreviation_file: 略語リストファイルのパス
        """
        self.server_url = server_url
        self.api_endpoint = f"{server_url}/v1/chat/completions"
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.abbreviation_file = abbreviation_file
        self.abbreviation_set = self.load_abbreviations()
        
    def load_abbreviations(self):
        """YAMLファイルから略語リストを読み込む"""
        try:
            with open(self.abbreviation_file, 'r', encoding='utf-8') as f:
                abbr_dict = yaml.safe_load(f)
            abbr_set = set()
            for v in abbr_dict.values():
                abbr_set.update(v)
            return abbr_set
        except Exception as e:
            print(f"略語リストの読み込みエラー: {e}")
            return set()

    def is_abbreviation(self, text: str) -> bool:
        """略語リストまたはパターンで略語判定"""
        if text in self.abbreviation_set:
            return True
        # パターンマッチング
        patterns = [
            r'^[A-Z]\.$',           # 単一大文字+ピリオド
            r'^[A-Z][a-z]+\.$',     # 大文字始まり+小文字+ピリオド
            r'^[a-z]+\.$',          # 小文字+ピリオド
        ]
        for pat in patterns:
            if re.match(pat, text):
                return True
        return False

    def protect_abbreviations(self, text: str) -> str:
        """略語を一時的に保護トークンに置換"""
        abbrs = sorted(self.abbreviation_set, key=len, reverse=True)
        for abbr in abbrs:
            safe_abbr = abbr.replace('.', '__PROTECTED_DOT__')
            text = text.replace(abbr, safe_abbr)
        # パターンマッチング分も保護
        text = re.sub(r'\b([A-Z]\.|[A-Z][a-z]+\.|[a-z]+\.)', lambda m: m.group(0).replace('.', '__PROTECTED_DOT__'), text)
        return text

    def restore_abbreviations(self, text: str) -> str:
        return text.replace('__PROTECTED_DOT__', '.')

    def detect_language(self, text: str) -> str:
        """
        テキストの言語を判別する
        
        Args:
            text: 判別対象のテキスト
            
        Returns:
            言語コード（'ja' または 'en'）
        """
        # 日本語文字（ひらがな、カタカナ、漢字）の割合を計算
        japanese_chars = re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', text)
        total_chars = len(re.findall(r'[a-zA-Z\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', text))
        
        if total_chars == 0:
            return 'en'  # デフォルトは英語
        
        japanese_ratio = len(japanese_chars) / total_chars
        
        # 日本語文字が30%以上含まれている場合は日本語と判定
        if japanese_ratio >= 0.3:
            return 'ja'
        else:
            return 'en'
    
    def get_topic_shift_prompt(self, current_text: str, new_sentence: str, language: str) -> str:
        """
        言語に応じた話題転換判定プロンプトを生成する
        
        Args:
            current_text: 現在までのテキスト
            new_sentence: 新しく追加される文
            language: 言語コード（'ja' または 'en'）
            
        Returns:
            プロンプト文字列
        """
        if language == 'ja':
            # 日本語プロンプト
            combined_text = f"現在のテキスト:\n{current_text}\n\n新しく追加される文:\n{new_sentence}"
            
            prompt = f"""以下のテキストを読んで、新しく追加される文が現在のテキストと明らかに異なる話題を扱っているかどうかを判定してください。

{combined_text}

判定基準:
- 新しい文が現在のテキストと明らかに異なる話題を扱っている場合: 話題転換
- 新しい文が現在のテキストの続きや関連する内容の場合: 同じ話題

回答は「話題転換」または「同じ話題」のいずれかで答えてください。"""
        else:
            # 英語プロンプト
            combined_text = f"Current text:\n{current_text}\n\nNew sentence to add:\n{new_sentence}"
            
            prompt = f"""Read the following text and determine if the new sentence deals with a clearly different topic from the current text.

{combined_text}

Criteria:
- If the new sentence deals with a clearly different topic from the current text: topic shift
- If the new sentence is a continuation or related content to the current text: same topic

Answer with either "topic shift" or "same topic"."""
        
        return prompt
    
    def split_sentences(self, text: str) -> List[Tuple[str, str]]:
        """略語保護→文分割→復元"""
        protected = self.protect_abbreviations(text)
        # 既存の分割ロジック
        paragraphs = protected.split('\n')
        sentences_with_newlines = []
        
        for i, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                sentences_with_newlines.append(('', '\n'))
                continue
            
            # 段落内で文を分割（句点、感嘆符、疑問符、ただし数値の小数点と略語のピリオドは除外）
            # 数値の小数点（例：2.89）と略語のピリオド（例：P.）を除外するため、前後に数字または大文字がある場合は分割しない
            # また、ピリオドの後に小文字が続く場合も略語として扱う
            sentences = re.split(r'([.!?。！？](?![0-9A-Za-z]))\s*', paragraph.strip())
            
            # 文と句読点を結合
            current_sentence = ""
            for j in range(0, len(sentences), 2):
                if j + 1 < len(sentences):
                    # 文と句読点が分かれている場合
                    sentence_part = sentences[j]
                    punctuation = sentences[j + 1]
                    if sentence_part.strip():
                        current_sentence += sentence_part + punctuation
                    else:
                        current_sentence += punctuation
                else:
                    # 最後の部分（句読点がない場合）
                    current_sentence += sentences[j]
                
                # 短い文（20文字未満）は結合
                if len(current_sentence.strip()) < 20 and sentences_with_newlines:
                    # 前の文に結合
                    prev_sentence, prev_newline = sentences_with_newlines[-1]
                    # 略語（例：P.）が分離されないように特別処理
                    if current_sentence.strip().endswith('.') and len(current_sentence.strip()) <= 3:
                        # 短い略語の場合は次の文と結合
                        continue
                    sentences_with_newlines[-1] = (prev_sentence + current_sentence, prev_newline)
                else:
                    if current_sentence.strip():
                        # 見出し（"Phones"など）の場合は特別処理
                        if current_sentence.strip() in ["Phones", "Updates", "Samsung", "One UI"]:
                            # 見出しの前の改行を保持
                            if sentences_with_newlines:
                                prev_sentence, prev_newline = sentences_with_newlines[-1]
                                if not prev_newline.endswith('\n\n'):
                                    sentences_with_newlines[-1] = (prev_sentence, prev_newline + '\n')
                        sentences_with_newlines.append((current_sentence.strip(), ''))
                    current_sentence = ""
            
            # 段落の最後に改行を追加
            if sentences_with_newlines:
                last_sentence, last_newline = sentences_with_newlines[-1]
                # 見出しの場合は追加の改行を入れる
                if last_sentence in ["Phones", "Updates", "Samsung", "One UI"]:
                    sentences_with_newlines[-1] = (last_sentence, last_newline + '\n\n')
                else:
                    sentences_with_newlines[-1] = (last_sentence, last_newline + '\n')
        
        # 復元
        restored = [(self.restore_abbreviations(s), n) for s, n in sentences_with_newlines]
        return restored
    
    def is_topic_shift(self, current_text: str, new_sentence: str) -> bool:
        """
        LLMを使用して新しい文が話題の転換かどうかを判定する
        
        Args:
            current_text: 現在までのテキスト
            new_sentence: 新しく追加される文
            
        Returns:
            話題が転換した場合はTrue
        """
        # 言語を判別
        language = self.detect_language(current_text + " " + new_sentence)
        
        # 言語に応じたプロンプトを生成
        prompt = self.get_topic_shift_prompt(current_text, new_sentence, language)
        
        # LM Studio APIにリクエスト
        payload = {
            "model": "gemma-3n-e4b-it-text",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "max_tokens": 50
        }
        
        try:
            response = requests.post(
                self.api_endpoint,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=15  # 短いタイムアウト
            )
            response.raise_for_status()
            
            result = response.json()
            response_text = result['choices'][0]['message']['content'].strip().lower()
            
            # 言語に応じた回答解析
            if language == 'ja':
                return "話題転換" in response_text
            else:
                return "topic shift" in response_text
            
        except requests.exceptions.RequestException as e:
            print(f"話題判定エラー: {e}")
            # エラーの場合は保守的にFalseを返す（分割しない）
            return False
    
    def sentence_based_chunk(self, text: str) -> List[str]:
        """
        文単位での逐次判定によりテキストを分割する（改行を保持）
        
        Args:
            text: 分割対象のテキスト
            
        Returns:
            分割されたチャンクのリスト
        """
        # 文に分割（改行情報を保持）
        sentences_with_newlines = self.split_sentences(text)
        
        if not sentences_with_newlines:
            return []
        
        chunks = []
        current_chunk = ""
        sentence_count = 0

        for sentence, newline in sentences_with_newlines:
            sentence_count += 1
            sentence_with_newline = sentence + newline
            # 1文がmax_chunk_sizeを超える場合は、その文だけで1チャンクにする
            if len(sentence_with_newline) > self.max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.rstrip())
                    current_chunk = ""
                    sentence_count = 0
                chunks.append(sentence_with_newline.rstrip())
                continue

            # 現在のチャンクに文を追加した場合のサイズをチェック
            if current_chunk:
                combined_size = len(current_chunk) + len(sentence_with_newline)
            else:
                combined_size = len(sentence_with_newline)

            # サイズ制限を超える場合の処理
            if combined_size > self.max_chunk_size:
                if len(current_chunk) >= self.min_chunk_size:
                    chunks.append(current_chunk.rstrip())
                    current_chunk = sentence_with_newline
                    sentence_count = 1
                else:
                    # 最小サイズ未満なら強制的に追加（ただし最大サイズは超えない）
                    if len(current_chunk + sentence_with_newline) <= self.max_chunk_size * 1.2:  # 20%の許容
                        current_chunk += sentence_with_newline
                    else:
                        # それでも大きすぎる場合は分割
                        chunks.append(current_chunk.rstrip())
                        current_chunk = sentence_with_newline
                        sentence_count = 1
            else:
                # サイズ制限内の場合
                if current_chunk:
                    # 話題の転換をチェック（最小サイズ以上の場合のみ）
                    if len(current_chunk) >= self.min_chunk_size and sentence_count >= 2:
                        if self.is_topic_shift(current_chunk, sentence):
                            chunks.append(current_chunk.rstrip())
                            current_chunk = sentence_with_newline
                            sentence_count = 1
                        else:
                            current_chunk += sentence_with_newline
                    else:
                        current_chunk += sentence_with_newline
                else:
                    current_chunk = sentence_with_newline

        # 最後のチャンクを追加
        if current_chunk:
            chunks.append(current_chunk.rstrip())

        return chunks
    
    def chunk_file(self, input_file: str, output_dir: Optional[str] = None) -> bool:
        """
        ファイルを文単位で分割する
        
        Args:
            input_file: 入力ファイルのパス
            output_dir: 出力ディレクトリのパス（Noneの場合は自動生成）
            
        Returns:
            成功した場合はTrue、失敗した場合はFalse
        """
        try:
            # 入力ファイルの存在確認
            if not os.path.exists(input_file):
                print(f"エラー: 入力ファイル '{input_file}' が見つかりません。")
                return False
            
            # ファイルの読み込み
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"ファイル読み込み完了: {len(content)}文字")
            
            # 文単位分割実行
            print("文単位テキスト分割中...")
            chunks = self.sentence_based_chunk(content)
            
            print(f"分割完了: {len(chunks)}個のチャンクに分割")
            
            # 出力ディレクトリの決定
            if output_dir is None:
                input_path = Path(input_file)
                output_dir = str(input_path.parent / f"{input_path.stem}_sentence_chunks")
            
            # 出力ディレクトリの作成
            os.makedirs(output_dir, exist_ok=True)
            
            # チャンクファイルの保存
            for i, chunk in enumerate(chunks, 1):
                chunk_filename = f"chunk_{i:03d}.txt"
                chunk_path = os.path.join(output_dir, chunk_filename)
                
                with open(chunk_path, 'w', encoding='utf-8') as f:
                    f.write(chunk)
                
                print(f"チャンク {i}: {len(chunk)}文字 -> {chunk_path}")
            
            # メタデータファイルの作成
            metadata = {
                "original_file": input_file,
                "total_chunks": len(chunks),
                "max_chunk_size": self.max_chunk_size,
                "min_chunk_size": self.min_chunk_size,
                "method": "sentence_based_chunking",
                "chunks": []
            }
            
            for i, chunk in enumerate(chunks, 1):
                metadata["chunks"].append({
                    "chunk_number": i,
                    "filename": f"chunk_{i:03d}.txt",
                    "character_count": len(chunk)
                })
            
            metadata_path = os.path.join(output_dir, "metadata.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            print(f"文単位分割完了: {output_dir}")
            return True
            
        except Exception as e:
            print(f"ファイル処理エラー: {e}")
            return False


def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        print("使用方法: python sentence_based_chunker.py <入力ファイル> [出力ディレクトリ]")
        print("例: python sentence_based_chunker.py input.txt output_dir")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    # 文単位チャンカーを初期化
    chunker = SentenceBasedChunker()
    
    # 分割実行
    success = chunker.chunk_file(input_file, output_dir)
    
    if success:
        print("処理が正常に完了しました。")
    else:
        print("処理中にエラーが発生しました。")
        sys.exit(1)


if __name__ == "__main__":
    main() 