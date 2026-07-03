#!/usr/bin/env python3
"""Add furigana (ruby) to kanji in example sentences in japanese_grammar.html"""

import re
import html as htmlmod
import pykakasi

kks = pykakasi.Kakasi()

def add_ruby_to_text(text):
    if not text or not re.search(r'[\u4e00-\u9fff]', text):
        return text

    result = kks.convert(text)
    out_parts = []
    for item in result:
        orig = item['orig']
        hira = item['hira']

        kanji_start = -1
        kanji_end = -1
        for i, c in enumerate(orig):
            if '\u4e00' <= c <= '\u9fff':
                if kanji_start == -1:
                    kanji_start = i
                kanji_end = i + 1

        if kanji_start == -1:
            out_parts.append(htmlmod.escape(orig))
            continue

        prefix = orig[:kanji_start]
        kanji_part = orig[kanji_start:kanji_end]
        suffix = orig[kanji_end:]

        kanji_reading = hira
        if suffix and kanji_reading.endswith(suffix):
            kanji_reading = kanji_reading[:-len(suffix)]
        elif suffix and kanji_reading.endswith(''): pass
        if prefix and kanji_reading.startswith(prefix):
            kanji_reading = kanji_reading[len(prefix):]

        if kanji_reading:
            out_parts.append(f'{htmlmod.escape(prefix)}<ruby>{htmlmod.escape(kanji_part)}<rt>{htmlmod.escape(kanji_reading)}</rt></ruby>{htmlmod.escape(suffix)}')
        else:
            out_parts.append(htmlmod.escape(orig))

    return ''.join(out_parts)

def process_text_span(m):
    inner = m.group(1)
    raw = htmlmod.unescape(inner)
    processed = add_ruby_to_text(raw)
    return f'<span class="text">{processed}</span>'

with open('japanese_grammar.html', 'r', encoding='utf-8') as f:
    html = f.read()

count_before = len(re.findall(r'<span class="text">(.*?)</span>', html, re.DOTALL))

html = re.sub(
    r'<span class="text">(.*?)</span>',
    process_text_span,
    html,
    flags=re.DOTALL
)

count_after = len(re.findall(r'<ruby>', html))
count_texts = len(re.findall(r'<span class="text">(.*?)</span>', html, re.DOTALL))

with open('japanese_grammar.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Text spans: {count_before}")
print(f"Ruby tags added: {count_after}")
print(f"Text spans after: {count_texts}")
