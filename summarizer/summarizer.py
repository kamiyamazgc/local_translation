#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local Translation - Summarizer Module
LM Studioを使用してテキストを要約する機能
"""

import os
import sys
import requests
import json
from pathlib import Path
from typing import Optional


class Summarizer:
    """LM Studioを使用したローカル要約クラス"""
    
    def __init__(self, server_url: str = "http://127.0.0.1:1234"):
        """
        初期化
        
        Args:
            server_url: LM StudioサーバーのURL
        """
        self.server_url = server_url
        self.api_endpoint = f"{server_url}/v1/chat/completions"
        
    def summarize_text(self, text: str, max_length: int = 500, language: str = "日本語") -> str:
        """
        テキストを要約する
        
        Args:
            text: 要約対象のテキスト
            max_length: 要約の最大文字数
            language: 要約言語（"日本語" または "英語"）
            
        Returns:
            要約されたテキスト
        """
        # 言語に応じたプロンプトの作成
        if language == "英語":
            prompt = f"""Please summarize the following text in English. Focus on the key points and keep it concise within {max_length} characters.

Original text:
{text}

Summary:"""
        else:
            prompt = f"""以下のテキストを日本語で要約してください。重要なポイントを簡潔にまとめ、{max_length}文字以内で要約してください。

原文:
{text}

要約:"""
        
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
            "max_tokens": 2000
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
            summarized_text = result['choices'][0]['message']['content'].strip()
            
            return summarized_text
            
        except requests.exceptions.RequestException as e:
            print(f"要約エラー: {e}")
            return f"要約処理中にエラーが発生しました。" if language == "日本語" else "An error occurred during summarization."
    
    def summarize_file(self, input_file: str, output_file: Optional[str] = None, max_length: int = 500, language: str = "日本語") -> bool:
        """
        ファイルを要約する
        
        Args:
            input_file: 入力ファイルのパス
            output_file: 出力ファイルのパス（Noneの場合は自動生成）
            max_length: 要約の最大文字数
            language: 要約言語（"日本語" または "英語"）
            
        Returns:
            成功した場合はTrue、失敗した場合はFalse
        """
        try:
            # 入力ファイルの存在確認
            if not os.path.exists(input_file):
                print(f"エラー: 入力ファイル '{input_file}' が見つかりません。" if language == "日本語" else f"Error: Input file '{input_file}' not found.")
                return False
            
            # ファイルの読み込み
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"ファイル読み込み完了: {len(content)}文字" if language == "日本語" else f"File loaded: {len(content)} characters")
            
            # 要約実行
            print("要約中..." if language == "日本語" else "Summarizing...")
            summarized_content = self.summarize_text(content, max_length, language)
            
            # 出力ファイル名の決定
            if output_file is None:
                input_path = Path(input_file)
                lang_suffix = "_summary_en" if language == "英語" else "_summary"
                output_file = str(input_path.parent / f"{input_path.stem}{lang_suffix}{input_path.suffix}")
            
            # 要約結果の保存
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(summarized_content)
            
            print(f"要約完了: {output_file}" if language == "日本語" else f"Summary completed: {output_file}")
            print(f"要約文字数: {len(summarized_content)}文字" if language == "日本語" else f"Summary length: {len(summarized_content)} characters")
            return True
            
        except Exception as e:
            print(f"ファイル処理エラー: {e}" if language == "日本語" else f"File processing error: {e}")
            return False


def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        print("使用方法: python summarizer.py <入力ファイル> [出力ファイル] [最大文字数] [言語]")
        print("例: python summarizer.py input.txt output.txt 500 日本語")
        print("例: python summarizer.py input.txt output.txt 500 英語")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = None
    max_length = 500
    language = "日本語"
    
    # 引数の解析
    if len(sys.argv) > 2:
        # 2番目の引数が数値かどうかチェック
        try:
            max_length = int(sys.argv[2])
            # 3番目の引数が言語指定かチェック
            if len(sys.argv) > 3:
                language = sys.argv[3]
        except ValueError:
            # 2番目の引数が出力ファイル名の場合
            output_file = sys.argv[2]
            # 3番目の引数が数値かどうかチェック
            if len(sys.argv) > 3:
                try:
                    max_length = int(sys.argv[3])
                    # 4番目の引数が言語指定かチェック
                    if len(sys.argv) > 4:
                        language = sys.argv[4]
                except ValueError:
                    print("エラー: 最大文字数は数値で指定してください。")
                    sys.exit(1)
    
    # 言語の検証
    if language not in ["日本語", "英語"]:
        print("エラー: 言語は '日本語' または '英語' を指定してください。")
        sys.exit(1)
    
    # 要約器の初期化
    summarizer = Summarizer()
    
    # 要約実行
    success = summarizer.summarize_file(input_file, output_file, max_length, language)
    
    if success:
        print("処理が正常に完了しました。" if language == "日本語" else "Processing completed successfully.")
    else:
        print("処理中にエラーが発生しました。" if language == "日本語" else "An error occurred during processing.")
        sys.exit(1)


if __name__ == "__main__":
    main() 