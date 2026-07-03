#!/usr/bin/env python3
"""
Compare japanese_grammar.md (OCR-corrupted) with japanese_grammar_2.md (clean PDF)
to find OCR corruptions.
"""

import re
import difflib
import unicodedata

def normalize_text(s):
    """Normalize text for comparison - strip whitespace, normalize unicode."""
    s = unicodedata.normalize('NFKC', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def extract_headword(line):
    """Extract headword like 【あいだ】 from a line."""
    m = re.search(r'【[^】]+】', line)
    return m.group(0) if m else None

def parse_entries_v2(filepath):
    """
    Parse japanese_grammar_2.md (clean version).
    Returns dict: headword -> list of content lines
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    entries = {}
    current_headword = None
    current_lines = []

    # Skip first line if it's a title
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
    """
    Parse japanese_grammar.md (OCR-corrupted version).
    Headwords are like ## 【あいだ】
    Returns dict: headword -> list of (line_number, content) tuples
    """
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

def strip_numbering(s):
    """Remove numbering like ①②③, (1)(2)(3), ●, • etc."""
    s = re.sub(r'[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]', '', s)
    s = re.sub(r'\(\d+\)', '', s)
    s = re.sub(r'[●•・]', '', s)
    s = re.sub(r'[（（]', '', s)
    s = re.sub(r'[））]', '', s)
    s = re.sub(r'^[\s\d\.\-\*\+\#]+', '', s)
    return s.strip()

def normalize_for_compare(s):
    """Normalize text for semantic comparison."""
    s = normalize_text(s)
    s = strip_numbering(s)
    # Normalize common punctuation variations
    s = s.replace('＜', '<').replace('＞', '>')
    s = s.replace('「', '"').replace('」', '"')
    s = s.replace('『', "'").replace('』', "'")
    s = s.replace('・', '·')
    s = s.replace('—', '-').replace('―', '-').replace('─', '-').replace('━', '-')
    s = s.replace('╱', '/')
    s = s.replace('∼', '~').replace('〜', '~')
    # Normalize Japanese quotes
    s = s.replace('《', '<').replace('》', '>')
    return s

def calculate_similarity(s1, s2):
    """Calculate similarity ratio between two strings."""
    s1 = normalize_for_compare(s1)
    s2 = normalize_for_compare(s2)
    if not s1 and not s2:
        return 1.0
    return difflib.SequenceMatcher(None, s1, s2).ratio()

def find_ocr_corruptions(entries_v1, entries_v2):
    """Compare entries and find OCR corruptions."""
    corruptions = []

    for headword, v1_lines in entries_v1.items():
        if headword not in entries_v2:
            continue

        v2_lines = entries_v2[headword]
        v1_text = ''.join(content for _, content in v1_lines)
        v2_text = ''.join(v2_lines)

        # Remove formatting differences (markdown headers etc)
        v1_clean = re.sub(r'^#+\s*', '', v1_text, flags=re.MULTILINE)
        v1_clean = re.sub(r'```|`', '', v1_clean)
        v2_clean = re.sub(r'```|`', '', v2_text)

        # Split into lines for comparison
        v1_sentences = re.split(r'(?<=[。．！？])\s*', v1_clean)
        v2_sentences = re.split(r'(?<=[。．！？])\s*', v2_clean)

        # For each V2 sentence, find best match in V1 and report differences
        for v2_sent in v2_sentences:
            v2_sent = v2_sent.strip()
            if len(v2_sent) < 5:
                continue

            best_match_idx = -1
            best_ratio = 0
            for j, v1_sent in enumerate(v1_sentences):
                ratio = calculate_similarity(v2_sent, v1_sent)
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match_idx = j

            if best_ratio < 1.0 and best_ratio > 0.1 and best_match_idx >= 0:
                # Found possible corruption
                # Find which line in v1 this corresponds to
                matched_v1 = v1_sentences[best_match_idx].strip()
                # Skip if similarly matched elsewhere
                # Calculate char-level diff
                if best_ratio < 0.95 and len(v2_sent) > 10:
                    # Find the line number in the original file
                    char_idx = v1_clean.find(matched_v1[:30])
                    if char_idx >= 0:
                        # Map back to original line number
                        cum_len = 0
                        found_line_no = None
                        for ln, content in v1_lines:
                            cum_len += len(content)
                            if cum_len > char_idx:
                                found_line_no = ln
                                break
                        if found_line_no is None:
                            found_line_no = v1_lines[-1][0]

                        # Truncate long strings for display
                        v2_display = v2_sent[:120] + ('...' if len(v2_sent) > 120 else '')
                        v1_display = matched_v1[:120] + ('...' if len(matched_v1) > 120 else '')
                        similarity_pct = int(best_ratio * 100)

                        if similarity_pct < 95:
                            corruptions.append({
                                'headword': headword,
                                'line': found_line_no,
                                'similarity': similarity_pct,
                                'length': len(v2_sent),
                                'corrupted': v1_display,
                                'correct': v2_display
                            })

    # Remove duplicates
    seen = set()
    unique = []
    for c in corruptions:
        key = (c['line'], c['corrupted'][:60])
        if key not in seen:
            seen.add(key)
            unique.append(c)

    # Sort by similarity (most corrupted first), then by length
    unique.sort(key=lambda x: (x['similarity'], -x['length']))

    return unique[:100]


# --- Also do a line-by-line comparison for entries that match ---

def find_exact_line_corruptions(entries_v1, entries_v2):
    """For each headword, compare line by line more precisely."""
    results = []

    for headword, v1_lines in entries_v1.items():
        if headword not in entries_v2:
            continue

        v2_lines_text = entries_v2[headword]
        v2_full = ''.join(v2_lines_text)
        v1_full = ''.join(content for _, content in v1_lines)

        # Remove markdown headers
        v1_clean = re.sub(r'^#+\s*', '', v1_full, flags=re.MULTILINE)
        v2_clean = v2_full

        # Split by line
        v1_lines_split = v1_clean.split('\n')
        v2_lines_split = v2_clean.split('\n')

        # Compare each V2 line with best matching V1 line
        for v2_line in v2_lines_split:
            v2_line = v2_line.strip()
            if len(v2_line) < 8:
                continue
            v2_norm = normalize_for_compare(v2_line)

            best_idx = -1
            best_ratio = 0
            v1_candidates = []
            for j, v1_line in enumerate(v1_lines_split):
                v1_line = v1_line.strip()
                v1_candidates.append(v1_line)
                ratio = calculate_similarity(v2_line, v1_line)
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_idx = j

            if best_ratio < 0.90 and best_ratio > 0.2 and best_idx >= 0:
                matched_v1 = v1_candidates[best_idx]
                # Find line number
                char_idx = v1_clean.find(matched_v1[:40])
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
                    'similarity': int(best_ratio * 100),
                    'length': len(v2_line),
                    'corrupted': matched_v1[:150],
                    'correct': v2_line[:150]
                })

    # Remove duplicates
    seen = set()
    unique = []
    for r in results:
        key = (r['line'], r['correct'][:50])
        if key not in seen:
            seen.add(key)
            unique.append(r)

    unique.sort(key=lambda x: (x['similarity'], -x['length']))
    return unique[:100]


def main():
    file_v1 = '/Users/able/Desktop/projects/japanese/japanese_grammar.md'
    file_v2 = '/Users/able/Desktop/projects/japanese/japanese_grammar_2.md'

    print("=" * 70)
    print("OCR CORRUPTION ANALYSIS")
    print("Comparing japanese_grammar.md (corrupted) vs japanese_grammar_2.md (clean)")
    print("=" * 70)

    entries_v1 = parse_entries_v1(file_v1)
    entries_v2 = parse_entries_v2(file_v2)

    print(f"\nFound {len(entries_v1)} headwords in OCR file")
    print(f"Found {len(entries_v2)} headwords in clean file")

    common = set(entries_v1.keys()) & set(entries_v2.keys())
    print(f"Common headwords: {len(common)}")

    only_v1 = set(entries_v1.keys()) - set(entries_v2.keys())
    only_v2 = set(entries_v2.keys()) - set(entries_v1.keys())
    print(f"Only in OCR file: {len(only_v1)}")
    print(f"Only in clean file: {len(only_v2)}")

    # Method 1: Sentence-level corruption detection
    print("\n" + "=" * 70)
    print("TOP 100 SENTENCE-LEVEL CORRUPTIONS")
    print("=" * 70)

    corruptions = find_ocr_corruptions(entries_v1, entries_v2)

    for i, c in enumerate(corruptions, 1):
        print(f"\n{i}. [{c['headword']}] line {c['line']} | (similarity: {c['similarity']}%, len: {c['length']})")
        print(f"   OCR (WRONG):  {c['corrupted']}")
        print(f"   PDF (CORRECT): {c['correct']}")

    # Method 2: Line-by-line comparison
    print("\n" + "=" * 70)
    print("TOP 100 LINE-BY-LINE CORRUPTIONS")
    print("=" * 70)

    line_results = find_exact_line_corruptions(entries_v1, entries_v2)

    for i, r in enumerate(line_results, 1):
        print(f"\n{i}. [{r['headword']}] line {r['line']} | (similarity: {r['similarity']}%, len: {r['length']})")
        print(f"   OCR (WRONG):  {r['corrupted']}")
        print(f"   PDF (CORRECT): {r['correct']}")


if __name__ == '__main__':
    main()
