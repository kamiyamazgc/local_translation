#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sentence_based_chunker import SentenceBasedChunker

def test_hybrid_abbreviations():
    """ハイブリッド方式の略語判定・保護機能をテスト"""
    
    # テスト用の文章（様々な略語を含む）
    test_text = """Dr. Smith visited Mr. Johnson at 123 Main St. on Jan. 15th at 3:30 p.m.

The meeting was scheduled for approx. 2 hours. The CEO of ABC Corp. Inc. was also present.

They discussed various topics including IT infrastructure, HR policies, and R&D projects.

The document referenced fig. 1 and ex. 2 from the previous report. See p. 45 for details.

Contact us at tel. 555-1234 or email us at info@example.com. Visit www.example.com for more info.

P.S. Don't forget the meeting on Mon. at 9:00 a.m. in the conference room.

The temperature was 72°F (22°C) and the speed limit was 35 mph on the road.

They used etc. and i.e. in their presentation, along with e.g. examples.

The file size was 2.5 GB and the download speed was 50 Mbps.

The coordinates were N. 40° and W. 74° for the location."""

    print("=== ハイブリッド方式略語判定・保護テスト ===")
    print(f"テスト文章（{len(test_text)}文字）:")
    print("-" * 50)
    print(test_text)
    print("-" * 50)
    
    # チャンカーを初期化
    chunker = SentenceBasedChunker()
    
    print(f"\n読み込まれた略語数: {len(chunker.abbreviation_set)}")
    print("略語リスト（一部）:", list(chunker.abbreviation_set)[:10])
    
    # 略語保護テスト
    print("\n=== 略語保護テスト ===")
    protected = chunker.protect_abbreviations(test_text)
    print("保護後:")
    print(protected)
    
    # 文分割テスト
    print("\n=== 文分割テスト ===")
    sentences = chunker.split_sentences(test_text)
    print(f"分割された文数: {len(sentences)}")
    
    for i, (sentence, newline) in enumerate(sentences):
        print(f"\n文 {i+1}: {repr(sentence)}")
        if newline:
            print(f"改行: {repr(newline)}")
    
    # 略語が正しく復元されているかチェック
    print("\n=== 略語復元チェック ===")
    restored_text = ""
    for sentence, newline in sentences:
        restored_text += sentence + newline
    
    # 元の略語が正しく復元されているかチェック
    original_abbreviations = ["Dr.", "Mr.", "St.", "Jan.", "p.m.", "approx.", "CEO", "Corp.", "Inc.", "IT", "HR", "R&D", "fig.", "ex.", "p.", "tel.", "www.", "P.S.", "Mon.", "a.m.", "°F", "°C", "mph", "etc.", "i.e.", "e.g.", "GB", "Mbps", "N.", "W."]
    
    missing_abbreviations = []
    for abbr in original_abbreviations:
        if abbr not in restored_text:
            missing_abbreviations.append(abbr)
    
    if missing_abbreviations:
        print(f"❌ 復元されていない略語: {missing_abbreviations}")
    else:
        print("✅ すべての略語が正しく復元されました")
    
    print(f"\n復元されたテキスト（{len(restored_text)}文字）:")
    print("-" * 50)
    print(restored_text)
    print("-" * 50)

if __name__ == "__main__":
    test_hybrid_abbreviations() 