import json
from pathlib import Path
import sys

# translator.pyのTranslatorクラスをimport
sys.path.append(str(Path(__file__).resolve().parent.parent.parent / "translator"))
from translator import Translator

INPUT_JSON = str(Path(__file__).resolve().parent / "sample/sample_2.json")
OUTPUT_JSON = str(Path(__file__).resolve().parent / "sample/sample_2_lines_translated.json")

def main():
    # 入力JSONを読み込む
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    translator = Translator()
    result = []

    for entry in data:
        line_num = entry["line"]
        text = entry["text"]
        print(f"Translating line {line_num}...")
        translated = translator.translate_text(text)
        result.append({"line": line_num, "text": translated})

    # 出力JSONに保存
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Done. Output: {OUTPUT_JSON}")

if __name__ == "__main__":
    main() 