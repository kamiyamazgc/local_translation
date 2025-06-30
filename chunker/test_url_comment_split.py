#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

def test_url_comment_split():
    """URLやコメントでの改行テスト"""
    
    test_texts = [
        # URLの途中での改行
        "Visit https://example.com/very-long-url-path for more information.",
        
        # コメントの途中での改行
        "// This is a very long comment that should not be split",
        
        # パスの途中での改行
        "File path: C:\\Users\\username\\Documents\\file.txt",
        
        # 複数行URL
        "Visit https://example.com/\nvery-long-url-path for more information.",
        
        # 複数行コメント
        "// This is a very long comment\n// that spans multiple lines",
    ]
    
    for i, text in enumerate(test_texts):
        print(f"\n=== テスト {i+1} ===")
        print(f"元のテキスト: {repr(text)}")
        
        # 現在の正規表現で分割
        sentences = re.split(r'([.!?。！？](?![0-9A-Za-z]))\s*', text)
        print(f"分割結果: {sentences}")
        
        # URLやコメントを保護した場合
        protected_text = text.replace('https://', 'https__PROTECTED__')
        protected_text = protected_text.replace('//', '__PROTECTED_COMMENT__')
        sentences_protected = re.split(r'([.!?。！？](?![0-9A-Za-z]))\s*', protected_text)
        print(f"保護後分割: {sentences_protected}")

if __name__ == "__main__":
    test_url_comment_split() 