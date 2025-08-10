import re
from sudachipy import Dictionary, Tokenizer

def parse_info_text(text_block, tokenizer):
    """
    Parses a block of text, correctly separating On-yomi and Kun-yomi.
    """
    # Use regex to find English words for the meaning first
    meaning = " ".join(re.findall(r'[a-zA-Z]+', text_block))
    
    on_yomi_list = []
    kun_yomi_list = []
    
    # Find all Japanese vocabulary words with their readings in parentheses
    vocab_list = re.findall(r'([\u3000-\u9faf\u3040-\u309f]+)\(([\u3040-\u309f]+)\)', text_block)

    for word, reading_hira in vocab_list:
        # Count the number of Kanji characters in the word
        kanji_count = len(re.findall(r'[\u4e00-\u9faf]', word))

        # RULE: If a word has 2 or more Kanji, it's a compound word (jukugo),
        # so its reading is On-yomi.
        if kanji_count >= 2:
            # Convert the Hiragana reading back to Katakana for On-yomi
            reading_kata = "".join([chr(ord(c) + 96) for c in reading_hira])
            on_yomi_list.append(f"{word}({reading_kata})")
        # RULE: Otherwise, it's a native word, so its reading is Kun-yomi.
        else:
            kun_yomi_list.append(f"{word}({reading_hira})")

    on_yomi = " ".join(dict.fromkeys(on_yomi_list))
    kun_yomi = " ".join(dict.fromkeys(kun_yomi_list))
    example = " ".join(text_block.split())

    return meaning, on_yomi, kun_yomi, example

# --- Our Test ---
tokenizer_obj = Dictionary().create()
sample_text = "住む(すむ) to live 住所(じゅうしょ) address 移住する(いじゅうする) to immigrate"

meaning, on_yomi, kun_yomi, example = parse_info_text(sample_text, tokenizer_obj)

print("--- Parser Output ---")
print(f"  Meaning: {meaning}")
print(f"  On-yomi: {on_yomi}")
print(f"  Kun-yomi: {kun_yomi}")
print(f"  Example: {example}")