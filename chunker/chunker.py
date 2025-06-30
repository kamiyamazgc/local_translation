#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local Translation - Chunker Module
LM Studioを使用してテキストを意味的なまとまりで分割する機能
"""

import os
import sys
import requests
import json
import re
from pathlib import Path
from typing import Optional, List, Dict


class Chunker:
    """LM Studioを使用したローカルテキスト分割クラス"""

    def __init__(self, server_url: str = os.getenv("LM_STUDIO_SERVER_URL", "http://127.0.0.1:1234")):
        """
        初期化
        
        Args:
            server_url: LM StudioサーバーのURL
        """
        self.server_url = server_url
        self.api_endpoint = f"{server_url}/v1/chat/completions"
        
    def chunk_text(self, text: str, max_chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """
        テキストを意味的なまとまりで分割する
        
        Args:
            text: 分割対象のテキスト
            max_chunk_size: 各チャンクの最大文字数
            overlap: チャンク間の重複文字数
            
        Returns:
            分割されたテキストのリスト
        """
        # 基本的なテキスト前処理
        text = text.strip()
        if not text:
            return []
        
        # 段落で分割
        paragraphs = re.split(r'\n\s*\n', text)
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # 現在のチャンクに段落を追加した場合の長さをチェック
            if current_chunk and len(current_chunk + "\n\n" + paragraph) > max_chunk_size:
                # 現在のチャンクが最大サイズを超える場合、保存して新しいチャンクを開始
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    # 重複部分を保持
                    if overlap > 0 and len(current_chunk) > overlap:
                        current_chunk = current_chunk[-overlap:] + "\n\n" + paragraph
                    else:
                        current_chunk = paragraph
                else:
                    # 段落自体が最大サイズを超える場合、強制的に分割
                    if len(paragraph) > max_chunk_size:
                        # 文単位で分割
                        sentences = re.split(r'[.!?。！？]\s*', paragraph)
                        temp_chunk = ""
                        for sentence in sentences:
                            sentence = sentence.strip()
                            if not sentence:
                                continue
                            if len(temp_chunk + sentence + ". ") > max_chunk_size:
                                if temp_chunk:
                                    chunks.append(temp_chunk.strip())
                                    temp_chunk = sentence + ". "
                                else:
                                    # 文自体が長すぎる場合、文字数で分割
                                    for i in range(0, len(sentence), max_chunk_size):
                                        chunk = sentence[i:i + max_chunk_size]
                                        chunks.append(chunk)
                            else:
                                temp_chunk += sentence + ". "
                        if temp_chunk:
                            current_chunk = temp_chunk
                    else:
                        current_chunk = paragraph
            else:
                # 段落を現在のチャンクに追加
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # 最後のチャンクを追加
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def smart_chunk_text(self, text: str, max_chunk_size: int = 1000) -> List[str]:
        """
        LM Studioを使用してより賢いテキスト分割を行う
        
        Args:
            text: 分割対象のテキスト
            max_chunk_size: 各チャンクの最大文字数
            
        Returns:
            分割されたテキストのリスト
        """
        # テキストが短い場合はそのまま返す
        if len(text) <= max_chunk_size:
            return [text]
        
        # 分割プロンプトの作成
        prompt = f"""以下のテキストを意味的なまとまりで分割してください。各チャンクは{max_chunk_size}文字以内にしてください。
分割する際は、文や段落の境界を尊重し、意味の一貫性を保ってください。

テキスト:
{text}

分割されたチャンクを以下の形式で返してください：
CHUNK 1:
[チャンク1の内容]

CHUNK 2:
[チャンク2の内容]

..."""
        
        # LM Studio APIにリクエスト
        payload = {
            "model": "gemma-3n-e4b-it-text",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 4000
        }
        
        try:
            response = requests.post(
                self.api_endpoint,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            response_text = result['choices'][0]['message']['content'].strip()
            
            # レスポンスからチャンクを抽出
            chunks = self._parse_chunks_from_response(response_text)
            
            # パースに失敗した場合は基本的な分割を使用
            if not chunks:
                return self.chunk_text(text, max_chunk_size)
            
            return chunks
            
        except requests.exceptions.RequestException as e:
            print(f"分割エラー: {e}")
            # エラーの場合は基本的な分割を使用
            return self.chunk_text(text, max_chunk_size)
    
    def _parse_chunks_from_response(self, response_text: str) -> List[str]:
        """
        LM Studioのレスポンスからチャンクを抽出する
        
        Args:
            response_text: LM Studioからのレスポンステキスト
            
        Returns:
            抽出されたチャンクのリスト
        """
        chunks = []
        
        # "CHUNK X:" パターンで分割
        chunk_pattern = r'CHUNK\s+\d+:\s*\n(.*?)(?=CHUNK\s+\d+:\s*\n|$)'
        matches = re.findall(chunk_pattern, response_text, re.DOTALL)
        
        for match in matches:
            chunk = match.strip()
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    def chunk_file(self, input_file: str, output_dir: Optional[str] = None, 
                   max_chunk_size: int = 1000, use_smart_chunking: bool = True) -> bool:
        """
        ファイルを意味的なまとまりで分割する
        
        Args:
            input_file: 入力ファイルのパス
            output_dir: 出力ディレクトリのパス（Noneの場合は自動生成）
            max_chunk_size: 各チャンクの最大文字数
            use_smart_chunking: スマート分割を使用するかどうか
            
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
            
            # 分割実行
            print("テキスト分割中...")
            if use_smart_chunking:
                chunks = self.smart_chunk_text(content, max_chunk_size)
            else:
                chunks = self.chunk_text(content, max_chunk_size)
            
            print(f"分割完了: {len(chunks)}個のチャンクに分割")
            
            # 出力ディレクトリの決定
            if output_dir is None:
                input_path = Path(input_file)
                output_dir = str(input_path.parent / f"{input_path.stem}_chunks")
            
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
                "max_chunk_size": max_chunk_size,
                "use_smart_chunking": use_smart_chunking,
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
            
            print(f"分割完了: {output_dir}")
            return True
            
        except Exception as e:
            print(f"ファイル処理エラー: {e}")
            return False


def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        print("使用方法: python chunker.py <入力ファイル> [出力ディレクトリ] [最大チャンクサイズ] [スマート分割]")
        print("例: python chunker.py input.txt output_dir 1000 true")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = None
    max_chunk_size = 1000
    use_smart_chunking = True
    
    # 引数の解析
    if len(sys.argv) > 2:
        # 2番目の引数が数値かどうかチェック
        try:
            max_chunk_size = int(sys.argv[2])
            # 3番目の引数がスマート分割指定かチェック
            if len(sys.argv) > 3:
                use_smart_chunking = sys.argv[3].lower() == 'true'
        except ValueError:
            # 2番目の引数が出力ディレクトリ名の場合
            output_dir = sys.argv[2]
            # 3番目の引数が数値かどうかチェック
            if len(sys.argv) > 3:
                try:
                    max_chunk_size = int(sys.argv[3])
                    # 4番目の引数がスマート分割指定かチェック
                    if len(sys.argv) > 4:
                        use_smart_chunking = sys.argv[4].lower() == 'true'
                except ValueError:
                    print("エラー: 最大チャンクサイズは数値で指定してください。")
                    sys.exit(1)
    
    # チャンカーを初期化
    chunker = Chunker()
    
    # 分割実行
    success = chunker.chunk_file(input_file, output_dir, max_chunk_size, use_smart_chunking)
    
    if success:
        print("処理が正常に完了しました。")
    else:
        print("処理中にエラーが発生しました。")
        sys.exit(1)


if __name__ == "__main__":
    main() 