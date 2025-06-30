#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local Translation - Simple Chunker Module
シンプルで確実なルールベースのテキスト分割機能
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Optional, List, Dict


class SimpleChunker:
    """シンプルなルールベースのテキスト分割クラス"""
    
    def __init__(self, max_chunk_size: int = 1500, overlap: int = 200):
        """
        初期化
        
        Args:
            max_chunk_size: 最大チャンクサイズ（文字数）
            overlap: チャンク間の重複文字数
        """
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        
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
        
        # 空の段落を除去
        cleaned_paragraphs = []
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph:
                cleaned_paragraphs.append(paragraph)
        
        return cleaned_paragraphs
    
    def simple_chunk(self, text: str) -> List[str]:
        """
        シンプルなルールベースでテキストを分割する
        
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
        
        for paragraph in paragraphs:
            # 現在のチャンクに段落を追加した場合のサイズをチェック
            if current_chunk:
                combined_size = len(current_chunk) + len(paragraph) + 2  # +2 for "\n\n"
            else:
                combined_size = len(paragraph)
            
            # サイズ制限を超える場合
            if combined_size > self.max_chunk_size:
                # 現在のチャンクを保存
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    
                    # 重複部分を保持
                    if self.overlap > 0 and len(current_chunk) > self.overlap:
                        # 最後の部分を重複として保持
                        overlap_text = current_chunk[-self.overlap:]
                        # 段落の境界で切る
                        last_paragraph_end = overlap_text.rfind('\n\n')
                        if last_paragraph_end > 0:
                            overlap_text = overlap_text[last_paragraph_end + 2:]
                        current_chunk = overlap_text + "\n\n" + paragraph
                    else:
                        current_chunk = paragraph
                else:
                    # 段落自体が大きすぎる場合、強制的に分割
                    if len(paragraph) > self.max_chunk_size:
                        # 文単位で分割
                        sentences = re.split(r'[.!?。！？]\s*', paragraph)
                        temp_chunk = ""
                        for sentence in sentences:
                            sentence = sentence.strip()
                            if not sentence:
                                continue
                            if len(temp_chunk + sentence + ". ") > self.max_chunk_size:
                                if temp_chunk:
                                    chunks.append(temp_chunk.strip())
                                    temp_chunk = sentence + ". "
                                else:
                                    # 文自体が長すぎる場合、文字数で分割
                                    for i in range(0, len(sentence), self.max_chunk_size):
                                        chunk = sentence[i:i + self.max_chunk_size]
                                        chunks.append(chunk)
                            else:
                                temp_chunk += sentence + ". "
                        if temp_chunk:
                            current_chunk = temp_chunk
                    else:
                        current_chunk = paragraph
            else:
                # サイズ制限内の場合、段落を追加
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # 最後のチャンクを追加
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def chunk_file(self, input_file: str, output_dir: Optional[str] = None) -> bool:
        """
        ファイルをシンプルに分割する
        
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
            
            # シンプル分割実行
            print("シンプルテキスト分割中...")
            chunks = self.simple_chunk(content)
            
            print(f"分割完了: {len(chunks)}個のチャンクに分割")
            
            # 出力ディレクトリの決定
            if output_dir is None:
                input_path = Path(input_file)
                output_dir = str(input_path.parent / f"{input_path.stem}_simple_chunks")
            
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
                "overlap": self.overlap,
                "method": "simple_chunking",
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
            
            print(f"シンプル分割完了: {output_dir}")
            return True
            
        except Exception as e:
            print(f"ファイル処理エラー: {e}")
            return False


def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        print("使用方法: python simple_chunker.py <入力ファイル> [出力ディレクトリ] [最大チャンクサイズ]")
        print("例: python simple_chunker.py input.txt output_dir 1500")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    max_chunk_size = int(sys.argv[3]) if len(sys.argv) > 3 else 1500
    
    # シンプルチャンカーを初期化
    chunker = SimpleChunker(max_chunk_size=max_chunk_size)
    
    # 分割実行
    success = chunker.chunk_file(input_file, output_dir)
    
    if success:
        print("処理が正常に完了しました。")
    else:
        print("処理中にエラーが発生しました。")
        sys.exit(1)


if __name__ == "__main__":
    main() 