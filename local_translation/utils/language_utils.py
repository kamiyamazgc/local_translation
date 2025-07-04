"""共通の言語判別ユーティリティ"""

import re


def detect_language(text: str) -> str:
    """テキストの言語を判別する

    Args:
        text: 判別対象のテキスト

    Returns:
        'ja' または 'en'
    """
    japanese_chars = re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', text)
    total_chars = len(re.findall(r'[a-zA-Z\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', text))

    if total_chars == 0:
        return 'en'

    japanese_ratio = len(japanese_chars) / total_chars
    return 'ja' if japanese_ratio >= 0.3 else 'en'
