#!/usr/bin/env python3
"""
Compare japanese_grammar.md (OCR-corrupted) with japanese_grammar_2.md (clean PDF).
Produces a clean report of OCR corruptions.
"""

import re
import difflib
import unicodedata

def normalize_text(s):
    s = unicodedata.normalize('NFKC', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def extract_headword(line):
    m = re.search(r'【[^】]+】', line)
    return m.group(0) if m else None

def parse_entries_v2(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    entries = {}
    current_headword = None
    current_lines = []
    start = 0
    if lines and '文型辞書' in lines[0]:
        start = 1
    for i, line in enumerate(lines[start:], start=start+1):
        headword = extract_headword(line)
        if headword and not line.strip().startswith(('→', '*', '#')):
            if current_headword:
                entries[current_headword] = current_lines
            current_headword = headword
            current_lines = [line]
        elif current_headword:
            current_lines.append(line)
    if current_headword:
        entries[current_headword] = current_lines
    return entries

def parse_entries_v1(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    entries = {}
    current_headword = None
    current_lines = []
    for i, line in enumerate(lines, start=1):
        headword = extract_headword(line)
        if headword and line.strip().startswith('#'):
            if current_headword:
                entries[current_headword] = current_lines
            current_headword = headword
            current_lines = [(i, line)]
        elif current_headword:
            current_lines.append((i, line))
    if current_headword:
        entries[current_headword] = current_lines
    return entries

def normalize_for_compare(s):
    s = normalize_text(s)
    s = re.sub(r'[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]', '', s)
    s = re.sub(r'\(\d+\)', '', s)
    s = re.sub(r'[●•・]', '', s)
    s = s.replace('＜', '<').replace('＞', '>')
    return s

def find_corruptions(entries_v1, entries_v2):
    results = []

    for headword, v1_lines in entries_v1.items():
        if headword not in entries_v2:
            continue

        v2_lines_text = entries_v2[headword]
        v2_full = ''.join(v2_lines_text)
        v1_full = ''.join(content for _, content in v1_lines)

        v1_clean = re.sub(r'^#+\s*', '', v1_full, flags=re.MULTILINE)
        v2_clean = v2_full

        # Split into sentences
        v1_sents = re.split(r'(?<=[。．！？])\s*', v1_clean)
        v2_sents = re.split(r'(?<=[。．！？])\s*', v2_clean)

        for v2_s in v2_sents:
            v2_s = v2_s.strip()
            if len(v2_s) < 8:
                continue

            best_idx = -1
            best_ratio = 0.0
            for j, v1_s in enumerate(v1_sents):
                v1_s = v1_s.strip()
                n1 = normalize_for_compare(v1_s)
                n2 = normalize_for_compare(v2_s)
                if n1 and n2:
                    ratio = difflib.SequenceMatcher(None, n1, n2).ratio()
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_idx = j

            if 0.2 < best_ratio < 0.92 and best_idx >= 0:
                matched = v1_sents[best_idx].strip()
                if len(matched) < 5:
                    continue

                # Map to line number
                char_idx = v1_clean.find(matched[:40])
                found_ln = None
                if char_idx >= 0:
                    cum = 0
                    for ln, content in v1_lines:
                        cum += len(content)
                        if cum > char_idx:
                            found_ln = ln
                            break
                if found_ln is None:
                    found_ln = v1_lines[0][0]

                results.append({
                    'headword': headword,
                    'line': found_ln,
                    'sim': int(best_ratio * 100),
                    'corrupted': matched[:200],
                    'correct': v2_s[:200]
                })

    # Deduplicate & sort
    seen = set()
    uniq = []
    for r in results:
        key = (r['headword'], r['correct'][:60])
        if key not in seen:
            seen.add(key)
            uniq.append(r)
    uniq.sort(key=lambda x: (x['sim'], -len(x['correct'])))
    return uniq[:100]


def main():
    entries_v1 = parse_entries_v1('/Users/able/Desktop/projects/japanese/japanese_grammar.md')
    entries_v2 = parse_entries_v2('/Users/able/Desktop/projects/japanese/japanese_grammar_2.md')

    common = set(entries_v1.keys()) & set(entries_v2.keys())
    print(f"Common headwords: {len(common)}")
    print()

    results = find_corruptions(entries_v1, entries_v2)

    for i, r in enumerate(results, 1):
        print(f"--- Corruption #{i} ---")
        print(f"  Headword: {r['headword']}")
        print(f"  Line (OCR file): {r['line']}")
        print(f"  Match score: {r['sim']}%")
        print(f"  OCR (WRONG):  {r['corrupted']}")
        print(f"  PDF (CORRECT): {r['correct']}")
        print()


if __name__ == '__main__':
    main()
