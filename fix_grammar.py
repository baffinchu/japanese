#!/usr/bin/env python3
"""
Align corrupted content in japanese_grammar.md with clean text from japanese_grammar_2.md.
Preserves format and numbering of japanese_grammar.md.

For each v1 content line, normalize spaces, find best fuzzy match in v2,
and replace with the v2 version if it's clean.
"""

import re
import difflib

V1_PATH = '/Users/able/Desktop/projects/japanese/japanese_grammar.md'
V2_PATH = '/Users/able/Desktop/projects/japanese/japanese_grammar_2.md'
BACKUP_PATH = '/Users/able/Desktop/projects/japanese/japanese_grammar.md.bak'

with open(BACKUP_PATH, 'r', encoding='utf-8') as f:
    v1 = f.read()
with open(V2_PATH, 'r', encoding='utf-8') as f:
    v2 = f.read()

HEADER_RE = re.compile(r'^(?:##\s*)?【[^】]+】')
CIRCLED = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳'
SENTENCE_END = '。？！\n'

# OCR character normalization map
CHAR_NORM = str.maketrans({
    '⮬': '自', 'ᩘ': '数', '尐': '少',
    'ᐇ': '実', 'ἣ': '態', 'ᅜ': '国',
    '⣖': '界', '⣡': '納', '◚': '破',
    'ᕫ': '己', 'ᖍ': '席', 'ᢥ': '択',
    '⨩': '規', '⫶': '胃', 'ᗈ': '広',
    '⤡': '絡', 'ᗓ': '権', 'ᗏ': '底',
    '⏒': '莫', '㈺': '損',
    '౫': '', '₎': '漢',
})

def norm_chars(text):
    """Normalize OCR-corrupted characters."""
    return text.translate(CHAR_NORM)

def split_entries(text):
    lines = text.split('\n')
    entries = []
    i = 0
    while i < len(lines) and not HEADER_RE.match(lines[i]):
        i += 1
    front = '\n'.join(lines[:i])
    cur_h = None
    cur_l = []
    while i < len(lines):
        if HEADER_RE.match(lines[i]):
            if cur_h:
                entries.append((cur_h, '\n'.join(cur_l)))
            m = re.match(r'^(?:##\s*)?(【[^】]+】)', lines[i])
            cur_h = m.group(1) if m else lines[i]
            cur_l = []
        else:
            cur_l.append(lines[i])
        i += 1
    if cur_h:
        entries.append((cur_h, '\n'.join(cur_l)))
    return front, entries

def clean_text(text):
    """Remove v2 formatting artifacts from extracted text."""
    text = text.replace('\n', '')

    if '●' in text:
        parts = text.split('●')
        text = parts[1] if len(parts) > 1 and not parts[0] else parts[0]

    # Section header: 「～」 etc.
    text = re.sub(r'^[^。]*?[＜<][^＞>]*[＞>]\s*', '', text)
    # Pattern headers like "1 R－あがる＜上方向＞"
    text = re.sub(r'^[\s\d' + CIRCLED + r']*[\w\u3040-\u309f\u30a0-\u30ff]+\s*[－]\s*[\w\u3040-\u309f\u30a0-\u30ff]+\s*', '', text)
    # Letter prefixes like "a "
    text = re.sub(r'^[a-d]\s+', '', text)
    # Leading の
    text = re.sub(r'^の\s*', '', text)
    # Leading 中 + space (v2 section artifact)
    text = re.sub(r'^中\s+(?=[\d\(])', '', text)
    # Leading circled numbers and spaces
    text = re.sub(r'^[\s' + CIRCLED + r']+', '', text)
    # Note: mid-text circled numbers are kept (e.g., ⑤～⑧ is kept, not stripped to ～)

    # Strip leading lone digit before hiragana/katakana (v2 artifact like "1ステレオ")
    text = re.sub(r'^\d(?=[\u3040-\u309F\u30A0-\u30FF])', '', text, count=1)
    # Strip leading lone digit before kanji (v2 numbering artifact like "4注文", "1長い間")
    # Keep if it's a quantity like 4時, 5人, etc.
    KEEP_DIGIT_KANJI = '時日年月分秒回人個'
    text = re.sub(r'^\d(?![' + KEEP_DIGIT_KANJI + r'])(?=[\u4E00-\u9FFF])', '', text, count=1)

    # Normalize OCR characters
    text = norm_chars(text)

    return text.strip()

def map_norm_to_orig(norm_pos, orig_text):
    """Map position in space-free text back to original with spaces."""
    cnt = 0
    for i, ch in enumerate(orig_text):
        if ch.isspace():
            continue
        if cnt == norm_pos:
            return i
        cnt += 1
    return len(orig_text)

def find_best_match(v1_line, v2_flat):
    """Find best matching clean text in v2_flat for v1_line."""
    if not v1_line or len(v1_line) < 5:
        return None, 0

    v1_norm = re.sub(r'\s+', '', v1_line)
    v2_norm = re.sub(r'\s+', '', v2_flat)

    matcher = difflib.SequenceMatcher(None, v1_norm, v2_norm, autojunk=False)
    match = matcher.find_longest_match(0, len(v1_norm), 0, len(v2_norm))

    if match.size < 8:
        return None, 0

    vs = map_norm_to_orig(match.b, v2_flat)
    ve_raw = map_norm_to_orig(match.b + match.size, v2_flat)
    if vs >= ve_raw:
        return None, 0

    # Adjust ve backward past trailing spaces
    ve = ve_raw
    while ve > vs and v2_flat[ve-1].isspace():
        ve -= 1

    exact = v2_flat[vs:ve]
    exact_ratio = difflib.SequenceMatcher(None, v1_line, exact, autojunk=False).ratio()

    # Expand backward to sentence start
    s = vs
    while s > 0 and v2_flat[s-1] not in SENTENCE_END:
        s -= 1
    # Skip leading spaces after backward expansion
    while s < len(v2_flat) and v2_flat[s].isspace():
        s += 1

    # Expand forward to sentence end
    if ve > 0 and v2_flat[ve-1] in SENTENCE_END:
        e = ve
    else:
        e = ve
        while e < len(v2_flat) and v2_flat[e] not in SENTENCE_END:
            e += 1
        if e < len(v2_flat):
            e += 1
    # Skip trailing spaces after forward expansion
    while e > s and v2_flat[e-1].isspace():
        e -= 1

    # Try different expansion widths
    best_clean = None
    best_ratio = 0

    for extra_s in [0, 10, 30]:
        for extra_e in [0, 5, 15]:
            st = max(s - extra_s, 0)
            et = min(len(v2_flat), e + extra_e)

            if extra_s > 0:
                while st > 0 and v2_flat[st-1] not in SENTENCE_END:
                    st -= 1
            if extra_e > 0 and et > e:
                while et < len(v2_flat) and v2_flat[et] not in SENTENCE_END:
                    et += 1
                if et < len(v2_flat):
                    et += 1

            cand = clean_text(v2_flat[st:et])
            if not cand or len(cand) < 5:
                continue
            r = difflib.SequenceMatcher(None, v1_line, cand, autojunk=False).ratio()
            if r > best_ratio:
                best_ratio = r
                best_clean = cand

    # Prefer sentence-expanded version over exact match
    # when the exact match is too close to corrupted v1
    if exact_ratio >= 0.8 and best_clean:
        best_clean_expanded = best_clean
        best_ratio_expanded = best_ratio
        exact_clean = clean_text(exact)
        exact_clean_ratio = difflib.SequenceMatcher(None, v1_line, exact_clean, autojunk=False).ratio()

        # Use expanded version if it contains the exact match as substring
        # (expansion adds missing text that v1 doesn't have)
        if exact_clean and exact_clean in best_clean_expanded:
            best_clean = best_clean_expanded
            best_ratio = best_ratio_expanded
        elif exact_clean and len(exact_clean) >= len(v1_line) * 0.4:
            best_clean = exact_clean
            best_ratio = exact_clean_ratio
        else:
            best_clean = best_clean_expanded
            best_ratio = best_ratio_expanded
    elif best_clean:
        # Exact match isn't great, use what we found
        pass
    else:
        exact_clean = clean_text(exact)
        if exact_clean and len(exact_clean) >= len(v1_line) * 0.4:
            best_clean = exact_clean
            best_ratio = exact_ratio

    if best_clean and best_ratio >= 0.5 and best_ratio < 1.0:
        return best_clean, best_ratio
    return None, best_ratio


front_matter, v1_entries = split_entries(v1)
_, v2_entries = split_entries(v2)
v2_dict = dict(v2_entries)

output = [front_matter]
fixed_count = 0

for header, v1_content in v1_entries:
    output.append(f'## {header}')

    if header not in v2_dict:
        output.append(v1_content)
        continue

    v2_content = v2_dict[header]
    v2_flat = v2_content.replace('\n', '')

    v1_lines = v1_content.split('\n')
    new_lines = []

    for line in v1_lines:
        stripped = line.strip()
        if not stripped:
            new_lines.append(line)
            continue

        if (stripped.startswith('`') or stripped.startswith('*') or
            stripped.startswith('---') or stripped.startswith('[') or
            stripped.startswith('#') or stripped.startswith('《') or
            stripped.startswith('→')):
            new_lines.append(line)
            continue

        # Handle lines containing ● (mixed example + explanation)
        if '●' in stripped:
            parts = stripped.split('●')
            first_part = parts[0].strip()
            rest = '●'.join(parts[1:])
            # Try to fix just the example part (before ●)
            m = re.match(r'^(\s*\(\d+\)\s*)(.*)$', first_part)
            if m:
                prefix = m.group(1)
                content = m.group(2)
                if content and len(content) >= 5:
                    c, r = find_best_match(content, v2_flat)
                    if c and r >= 0.5:
                        new_lines.append(f"{prefix}{c}●{rest}")
                        fixed_count += 1
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
            continue

        # Multi-example line: (1)...(2)...
        count_ex = len(re.findall(r'\(\d+\)', line))
        if count_ex > 1:
            parts = re.split(r'(\(\d+\))', line)
            result = []
            for p in parts:
                if re.match(r'^\(\d+\)$', p):
                    result.append(p)
                elif p.strip():
                    c, r = find_best_match(p.strip(), v2_flat)
                    if c:
                        result.append(c)
                        fixed_count += 1
                    else:
                        result.append(p)
                else:
                    result.append(p)
            new_lines.append(''.join(result))
            continue

        # Single example: (n) content
        m = re.match(r'^(\s*\(\d+\)\s*)(.*)$', line)
        if m:
            prefix = m.group(1)
            content = m.group(2)
            if content and len(content) >= 5:
                c, r = find_best_match(content, v2_flat)
                if c:
                    new_lines.append(f"{prefix}{c}")
                    fixed_count += 1
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
            continue

        # Non-example content line
        c, r = find_best_match(stripped, v2_flat)
        if c:
            indent = line[:len(line) - len(line.lstrip())]
            new_lines.append(f"{indent}{c}")
            fixed_count += 1
        else:
            new_lines.append(line)

    output.append('\n'.join(new_lines))

result_text = '\n'.join(output)

# Final normalization pass on the entire output
result_text = norm_chars(result_text)

with open(V1_PATH, 'w', encoding='utf-8') as f:
    f.write(result_text)

print(f"Done! Fixed {fixed_count} lines.")
