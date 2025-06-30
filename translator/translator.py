#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local Translation - Translator Module
LM Studioを使用してテキストファイルを日本語に翻訳する機能
"""

import os
import sys
import requests
import json
from pathlib import Path
from typing import Optional, Dict, Any

# ルートディレクトリをパスに追加して共通ユーティリティを参照
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.language_utils import detect_language


class Translator:
    """LM Studioを使用したローカル翻訳クラス"""
    
    def __init__(self, server_url: str = "http://127.0.0.1:1234"):
        """
        初期化
        
        Args:
            server_url: LM StudioサーバーのURL
        """
        self.server_url = server_url
        self.api_endpoint = f"{server_url}/v1/chat/completions"
        
    def detect_language(self, text: str) -> str:
        """テキストの言語を判別する"""
        return detect_language(text)
    
    def translate_text(self, text: str, target_language: str = "日本語") -> str:
        """
        テキストを翻訳する
        
        Args:
            text: 翻訳対象のテキスト
            target_language: 翻訳先言語
            
        Returns:
            翻訳されたテキスト
        """
        # 言語検出
        detected_lang = self.detect_language(text)
        
        # 日本語の場合は翻訳不要
        if detected_lang == 'ja':
            return text
        
        # 翻訳プロンプトの作成
        prompt = f"""以下のテキストを{target_language}に翻訳してください。原文の意味を正確に保ち、自然な{target_language}で翻訳してください。

原文:
{text}

翻訳:"""
        
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
            translated_text = result['choices'][0]['message']['content'].strip()
            
            return translated_text
            
        except requests.exceptions.RequestException as e:
            print(f"翻訳エラー: {e}")
            return text  # エラーの場合は原文を返す
    
    def translate_file(self, input_file: str, output_file: Optional[str] = None) -> bool:
        """
        ファイルを翻訳する
        
        Args:
            input_file: 入力ファイルのパス
            output_file: 出力ファイルのパス（Noneの場合は自動生成）
            
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
            
            # 言語検出
            detected_lang = self.detect_language(content)
            print(f"検出された言語: {detected_lang}")
            
            # 日本語の場合は翻訳不要
            if detected_lang == 'ja':
                print("日本語のテキストのため、翻訳をスキップします。")
                if output_file:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                return True
            
            # 翻訳実行
            print("翻訳中...")
            translated_content = self.translate_text(content)
            
            # 出力ファイル名の決定
            if output_file is None:
                input_path = Path(input_file)
                output_file = str(input_path.parent / f"{input_path.stem}_translated{input_path.suffix}")
            
            # 翻訳結果の保存
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(translated_content)
            
            print(f"翻訳完了: {output_file}")
            return True
            
        except Exception as e:
            print(f"ファイル処理エラー: {e}")
            return False


def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        print("使用方法: python translator.py <入力ファイル> [出力ファイル]")
        print("例: python translator.py input.txt output.txt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # 翻訳器の初期化
    translator = Translator()
    
    # 翻訳実行
    success = translator.translate_file(input_file, output_file)
    
    if success:
        print("処理が正常に完了しました。")
    else:
        print("処理中にエラーが発生しました。")
        sys.exit(1)


if __name__ == "__main__":
    main() 