#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local Translation - Progressive Chunker Module V2
改良版段階的アプローチでテキストを意味的なまとまりに分割する機能
"""

import os
import sys
import requests
import json
import re
from pathlib import Path
from typing import Optional, List, Dict, Tuple


class ProgressiveChunkerV2:
    """改良版段階的アプローチによるテキスト分割クラス"""

    def __init__(self, server_url: str = os.getenv("LM_STUDIO_SERVER_URL", "http://127.0.0.1:1234"),
                 max_chunk_size: int = 1500, min_chunk_size: int = 500):
        """
        初期化
        
        Args:
            server_url: LM StudioサーバーのURL
            max_chunk_size: 最大チャンクサイズ（文字数）
            min_chunk_size: 最小チャンクサイズ（文字数）
        """
        self.server_url = server_url
        self.api_endpoint = f"{server_url}/v1/chat/completions"
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        
    def split_paragraphs(self, text: str) -> List[str]:
        """
        テキストを段落単位で分割する
        
        Args:
            text: 分割対象のテキスト
            
        Returns:
            段落のリスト
        """
        # 段落で分割（空行で区切られた部分）
        paragraphs = re.split(r'\n\s*\n', text.strip())
        
        # 空の段落を除去し、短すぎる段落を結合
        cleaned_paragraphs = []
        temp_paragraph = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # 短い段落（50文字未満）は結合
            if len(paragraph) < 50 and temp_paragraph:
                temp_paragraph += "\n\n" + paragraph
            else:
                if temp_paragraph:
                    cleaned_paragraphs.append(temp_paragraph)
                temp_paragraph = paragraph
        
        if temp_paragraph:
            cleaned_paragraphs.append(temp_paragraph)
        
        return cleaned_paragraphs
    
    def is_topic_boundary(self, text1: str, text2: str) -> bool:
        """
        LLMを使用して2つのテキスト間の話題の境界を判定する
        
        Args:
            text1: 最初のテキスト
            text2: 2番目のテキスト
            
        Returns:
            話題の境界がある場合はTrue
        """
        # 判定用のテキストを作成
        combined_text = f"テキスト1:\n{text1}\n\nテキスト2:\n{text2}"
        
        # 判定プロンプト
        prompt = f"""以下の2つのテキストを読んで、テキスト2がテキスト1と明らかに異なる話題を扱っているかどうかを判定してください。

{combined_text}

判定基準:
- テキスト2がテキスト1と明らかに異なる話題を扱っている場合: 新しい話題
- テキスト2がテキスト1の続きや関連する内容の場合: 同じ話題

回答は「新しい話題」または「同じ話題」のいずれかで答えてください。"""

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
                timeout=20  # 短いタイムアウト
            )
            response.raise_for_status()
            
            result = response.json()
            response_text = result['choices'][0]['message']['content'].strip().lower()
            
            # 回答を解析
            return "新しい話題" in response_text or "new topic" in response_text
            
        except requests.exceptions.RequestException as e:
            print(f"話題判定エラー: {e}")
            # エラーの場合は保守的にFalseを返す（分割しない）
            return False
    
    def progressive_chunk(self, text: str) -> List[str]:
        """
        段階的にテキストを分割する（改良版）
        
        Args:
            text: 分割対象のテキスト
            
        Returns:
            分割されたチャンクのリスト
        """
        # 段落に分割
        paragraphs = self.split_paragraphs(text)
        
        if not paragraphs:
            return []
        
        chunks = []
        current_chunk = ""
        
        for i, paragraph in enumerate(paragraphs):
            # 現在のチャンクに段落を追加した場合のサイズをチェック
            if current_chunk:
                combined_size = len(current_chunk) + len(paragraph) + 2  # +2 for "\n\n"
            else:
                combined_size = len(paragraph)
            
            # サイズ制限を超える場合の処理
            if combined_size > self.max_chunk_size:
                # 現在のチャンクが最小サイズ以上なら保存
                if len(current_chunk) >= self.min_chunk_size:
                    chunks.append(current_chunk.strip())
                    current_chunk = paragraph
                else:
                    # 最小サイズ未満なら強制的に追加（ただし最大サイズは超えない）
                    if len(current_chunk + "\n\n" + paragraph) <= self.max_chunk_size * 1.2:  # 20%の許容
                        current_chunk += "\n\n" + paragraph
                    else:
                        # それでも大きすぎる場合は分割
                        chunks.append(current_chunk.strip())
                        current_chunk = paragraph
            else:
                # サイズ制限内の場合
                if current_chunk:
                    # 話題の境界をチェック（最小サイズ以上の場合のみ）
                    if len(current_chunk) >= self.min_chunk_size:
                        if self.is_topic_boundary(current_chunk, paragraph):
                            # 話題が変わった場合は分割
                            chunks.append(current_chunk.strip())
                            current_chunk = paragraph
                        else:
                            # 同じ話題なら追加
                            current_chunk += "\n\n" + paragraph
                    else:
                        # 最小サイズ未満なら追加
                        current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # 最後のチャンクを追加
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def chunk_file(self, input_file: str, output_dir: Optional[str] = None) -> bool:
        """
        ファイルを段階的に分割する
        
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
            
            # 段階的分割実行
            print("段階的テキスト分割中...")
            chunks = self.progressive_chunk(content)
            
            print(f"分割完了: {len(chunks)}個のチャンクに分割")
            
            # 出力ディレクトリの決定
            if output_dir is None:
                input_path = Path(input_file)
                output_dir = str(input_path.parent / f"{input_path.stem}_progressive_v2_chunks")
            
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
                "method": "progressive_chunking_v2",
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
            
            print(f"段階的分割完了: {output_dir}")
            return True
            
        except Exception as e:
            print(f"ファイル処理エラー: {e}")
            return False


def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        print("使用方法: python progressive_chunker_v2.py <入力ファイル> [出力ディレクトリ]")
        print("例: python progressive_chunker_v2.py input.txt output_dir")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    # 段階的チャンカーを初期化
    chunker = ProgressiveChunkerV2()
    
    # 分割実行
    success = chunker.chunk_file(input_file, output_dir)
    
    if success:
        print("処理が正常に完了しました。")
    else:
        print("処理中にエラーが発生しました。")
        sys.exit(1)


if __name__ == "__main__":
    main() 