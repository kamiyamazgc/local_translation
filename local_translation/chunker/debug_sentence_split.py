#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from typing import List, Tuple

def debug_split_sentences(text: str) -> List[Tuple[str, str]]:
    """
    テキストを文単位で分割する（デバッグ版）
    """
    print("=== デバッグ: 文分割処理 ===")
    
    # 改行でテキストを分割して段落を保持
    paragraphs = text.split('\n')
    sentences_with_newlines = []
    
    for i, paragraph in enumerate(paragraphs):
        if not paragraph.strip():
            print(f"段落 {i}: 空行")
            sentences_with_newlines.append(('', '\n'))
            continue
        
        print(f"\n段落 {i}: {repr(paragraph)}")
        
        # 段落内で文を分割
        sentences = re.split(r'([.!?。！？](?![0-9A-Za-z]))\s*', paragraph.strip())
        print(f"正規表現分割結果: {sentences}")
        
        # 文と句読点を結合
        current_sentence = ""
        for j in range(0, len(sentences), 2):
            if j + 1 < len(sentences):
                sentence_part = sentences[j]
                punctuation = sentences[j + 1]
                if sentence_part.strip():
                    current_sentence += sentence_part + punctuation
                else:
                    current_sentence += punctuation
            else:
                current_sentence += sentences[j]
            
            print(f"  結合中: {repr(current_sentence)}")
            
            # 短い文（20文字未満）は結合
            if len(current_sentence.strip()) < 20 and sentences_with_newlines:
                prev_sentence, prev_newline = sentences_with_newlines[-1]
                if current_sentence.strip().endswith('.') and len(current_sentence.strip()) <= 3:
                    print(f"  短い略語として結合をスキップ: {repr(current_sentence)}")
                    continue
                sentences_with_newlines[-1] = (prev_sentence + current_sentence, prev_newline)
                print(f"  前の文に結合: {repr(prev_sentence + current_sentence)}")
            else:
                if current_sentence.strip():
                    sentences_with_newlines.append((current_sentence.strip(), ''))
                    print(f"  新しい文として追加: {repr(current_sentence.strip())}")
                current_sentence = ""
        
        # 段落の最後に改行を追加
        if sentences_with_newlines:
            last_sentence, last_newline = sentences_with_newlines[-1]
            sentences_with_newlines[-1] = (last_sentence, last_newline + '\n')
    
    # 略語が分離されている場合の後処理
    print("\n=== 後処理 ===")
    processed_sentences = []
    i = 0
    while i < len(sentences_with_newlines):
        sentence, newline = sentences_with_newlines[i]
        print(f"処理中 {i}: {repr(sentence)}")
        
        # 短い略語（3文字以下でピリオドで終わる）の場合
        if sentence.strip().endswith('.') and len(sentence.strip()) <= 3:
            print(f"  短い略語を検出: {repr(sentence)}")
            if i + 1 < len(sentences_with_newlines):
                next_sentence, next_newline = sentences_with_newlines[i + 1]
                combined_sentence = sentence + next_sentence
                processed_sentences.append((combined_sentence, next_newline))
                print(f"  次の文と結合: {repr(combined_sentence)}")
                i += 2
                continue
        
        processed_sentences.append((sentence, newline))
        i += 1
    
    print(f"\n=== 最終結果 ===")
    for i, (sentence, newline) in enumerate(processed_sentences):
        print(f"文 {i}: {repr(sentence)}")
    
    return processed_sentences

if __name__ == "__main__":
    # テスト用のテキスト
    test_text = """P. gerontoformicaeの形態的特徴は、現存するアリ寄生性オフィオコルディセプス種の特徴と一致しています。側面に付着した子実体とHirsutella系統に類似した無性生殖形質の組み合わせは、ミルメコフィルス（アリ寄生）ヒルステロイド系統とO. sphecocephala系統の両方の基底近くに位置すると示唆されました。"""
    
    result = debug_split_sentences(test_text) 