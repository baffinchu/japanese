#!/usr/bin/env python3
"""Validate fixed japanese_grammar.md against japanese_grammar_2.md.

Compares by extracting pure content (examples + explanations) from each entry,
stripping all structural formatting markers, and checking verbatim match.
"""

import re

V1_PATH = '/Users/able/Desktop/projects/japanese/japanese_grammar.md'
V2_PATH = '/Users/able/Desktop/projects/japanese/japanese_grammar_2.md'

CIRCLED = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳'

NORM_MAP = str.maketrans({
    '⮬': '自', 'ᩘ': '数', '尐': '少',
    'ᐇ': '実', 'ἣ': '態', 'ᅜ': '国',
    '⣖': '界', '⣡': '納', '◚': '破',
    'ᕫ': '己', '₎': '漢', '౫': '',
})

def norm_characters(text):
    return text.translate(NORM_MAP)

def extract_pure_content(text):
    """Extract pure text content from entry: examples + explanations, no structure."""
    # First, normalize the entire text
    text = norm_characters(text)
    
    lines = []
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.startswith('---'):
            continue
        if line.startswith('→'):
            continue
        
        # Remove all structural prefixes
        # ### headers
        line = re.sub(r'^#{1,5}\s*', '', line)
        # (n) example numbering  
        line = re.sub(r'^\(\d+\)\s*', '', line)
        # (正)/(誤) prefixes
        line = re.sub(r'^\([正誤]\)\s*', '', line)
        # subsection letter prefixes like "a " or "b "
        line = re.sub(r'^[a-d]\s+', '', line)
        
        # Remove section header patterns: "1 R－あがる＜上方向＞" or "1 R-あがる<上方向>"
        line = re.sub(
            r'^[\s\d' + CIRCLED + r']*[\w\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]*\s*'
            r'[－\-]\s*[\w\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]*\s*'
            r'[＜<][^＞>]*[＞>]\s*',
            '', line)
        
        # Remove leading text like "Nのあいだ" (pattern description before examples)
        # followed by a circled number or (n)
        line = re.sub(
            r'^[\s\d' + CIRCLED + r']*[\w\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff\u3000-\u303f]+'
            r'(?=[' + CIRCLED + r']|\(\d+\))',
            '', line)
        
        # Remove ● marker and anything after it (v2 explanation separator)
        line = re.sub(r'●.*$', '', line)
        # Remove trailing cross-references like →【うる】
        line = re.sub(r'→【[^】]+】.*$', '', line)
        
        # Remove ALL remaining circled numbers
        line = re.sub(r'[' + CIRCLED + r']', '', line)
        
        if line.strip():
            lines.append(line.strip())
    return '\n'.join(lines)

def read_entries(filepath):
    """Read entries from markdown file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Normalize entry names for comparison (②->2, ...->...)
    # First extract all entries
    lines = text.split('\n')
    entries = {}
    cur_name = None
    cur_lines = None
    
    for line in lines:
        m = re.match(r'^(?:##\s*)?(【[^】]+】)', line)
        if m:
            if cur_name is not None:
                entries[cur_name] = '\n'.join(cur_lines)
            cur_name = m.group(1)
            cur_lines = []
        elif cur_name is not None:
            cur_lines.append(line)
    if cur_name is not None:
        entries[cur_name] = '\n'.join(cur_lines)
    return entries

# Canonical entry name (normalize structural variants)
def canonical(name):
    # Strip 【】 for comparison
    inner = name.strip('【】')
    inner = re.sub(r'[' + CIRCLED + r']', '', inner)
    inner = inner.replace('\u00b7', '.').replace('\u2026', '...')
    inner = re.sub(r'\s+', '', inner)
    return inner

v1_entries = read_entries(V1_PATH)
v2_entries = read_entries(V2_PATH)

# Build canonical name mapping
v1_by_canon = {canonical(k): k for k in v1_entries}
v2_by_canon = {canonical(k): k for k in v2_entries}

all_canon = sorted(set(v1_by_canon) | set(v2_by_canon))

exact = 0
near = 0
mismatch = 0
no_v1 = 0
no_v2 = 0

details = []

for cname in all_canon:
    if cname not in v1_by_canon:
        no_v1 += 1
        continue
    if cname not in v2_by_canon:
        no_v2 += 1
        continue
    
    v1_name = v1_by_canon[cname]
    v2_name = v2_by_canon[cname]
    
    v1_content = extract_pure_content(v1_entries[v1_name])
    v2_content = extract_pure_content(v2_entries[v2_name])
    
    v1_clean = norm_characters(re.sub(r'\s+', '', v1_content))
    v2_clean = norm_characters(re.sub(r'\s+', '', v2_content))
    
    if v1_clean == v2_clean:
        exact += 1
    else:
        # Show diff
        common = 0
        for a, b in zip(v1_clean, v2_clean):
            if a == b:
                common += 1
            else:
                break
        total = max(len(v1_clean), len(v2_clean))
        ratio = common / total if total > 0 else 0
        
        if ratio >= 0.9:
            near += 1
        else:
            mismatch += 1
        
        if len(details) < 15:
            # Find first point of difference
            diff_idx = 0
            for a, b in zip(v1_clean, v2_clean):
                if a != b:
                    break
                diff_idx += 1
            details.append((v1_name, ratio, 
                          v1_clean[max(0,diff_idx-15):diff_idx+50],
                          v2_clean[max(0,diff_idx-15):diff_idx+50]))

total = exact + near + mismatch
print("=" * 70)
print("CONTENT VERBATIM COMPARISON (pure content, structure stripped)")
print("=" * 70)
print(f"\nEntries shared (matched by canonical name): {total}")
print(f"  Exact match:  {exact:>4} ({exact/total*100:5.1f}%)")
print(f"  Near match:   {near:>4} ({near/total*100:5.1f}%)")
print(f"  Mismatch:     {mismatch:>4} ({mismatch/total*100:5.1f}%)")
print(f"  Combined:     {exact+near:>4} ({(exact+near)/total*100:5.1f}%)")
print(f"\nEntries only in v1: {no_v1}")
print(f"Entries only in v2: {no_v2}")

if details:
    print(f"\n--- Sample mismatches (first {len(details)}) ---")
    for name, ratio, v1s, v2s in details:
        print(f"\n  【{name}】 (ratio: {ratio:.2f})")
        print(f"    v1: ...{v1s}...")
        print(f"    v2: ...{v2s}...")
