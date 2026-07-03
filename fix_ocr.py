#!/usr/bin/env python3
"""
Fix known OCR corruption lines in japanese_grammar.md using japanese_grammar_2.md as reference.
Two-pass approach:
  Pass 1: Fix single-character corruption (钆→が, 钇→い, etc.)
  Pass 2: For remaining garbled lines (mixed-case Latin, spaced Latin), 
           find best PDF match and do whole-line replacement with strict safety checks.
"""
import re
from difflib import SequenceMatcher

MAX_LINE = 21000

with open('japanese_grammar.md', 'r', encoding='utf-8') as f:
    md_lines = f.readlines()

with open('japanese_grammar_2.md', 'r', encoding='utf-8') as f:
    pdf_lines = f.readlines()

def parse_entries(lines, md_mode=True):
    entries = {}
    cur = None; cstart = 1; clines = []
    for i, line in enumerate(lines):
        pat = r'^(?:## )?【(.+?)】' if md_mode else r'^【(.+?)】'
        m = re.match(pat, line)
        if m:
            if cur:
                entries[cur] = (cstart, i, clines)
            cur = m.group(1)
            cstart = i
            clines = [(i, line.rstrip('\n'))]
        elif cur:
            clines.append((i, line.rstrip('\n')))
    if cur:
        entries[cur] = (cstart, len(lines), clines)
    return entries

md_entries = parse_entries(md_lines, True)
pdf_entries = parse_entries(pdf_lines, False)
common = set(md_entries.keys()) & set(pdf_entries.keys())

# Known single-character OCR misreads
CHAR_FIXES = {
    '钆': 'が', '钇': 'い', '钊': 'か', '钋': 'け',
    '钌': 'こ', '钍': 'し', '钎': 'た', '钏': 'ば',
    '钐': 'ひ', '钒': 'み', '钛': 'よ',
}

# Pass 1: Single-character fixes
pass1 = 0
for i, line in enumerate(md_lines[:MAX_LINE]):
    changed = False
    chars = list(line)
    for j, c in enumerate(chars):
        if c in CHAR_FIXES:
            chars[j] = CHAR_FIXES[c]
            changed = True
    if changed:
        md_lines[i] = ''.join(chars)
        pass1 += 1

print(f"Pass 1: Fixed {pass1} lines (single-char corruption)")

# Pass 2: Lines with Latin mixed-case or spaced-Latin corruption
def has_ocr_noise(t):
    """Check for clear OCR corruption patterns."""
    if re.search(r'[a-z][A-Z]', t):
        return True
    if re.search(r'(?:^|[^a-zA-Z])[a-zA-Z] [a-zA-Z] [a-zA-Z]', t):
        return True
    return False

def is_fragment(t):
    t = t.strip()
    if not t: return True
    if re.match(r'^[らりるれろわをん]」', t): return True
    return False

pass2 = []
for h in sorted(common):
    md_start, _, md_els = md_entries[h]
    pdf_start, _, pdf_els = pdf_entries[h]
    
    if md_start > MAX_LINE:
        continue
    
    pdf_texts = [pt for _, pt in pdf_els]
    
    for md_lineno, md_text in md_els:
        if md_lineno > MAX_LINE:
            continue
        t = md_text.strip()
        if not t or not has_ocr_noise(t):
            continue
        if not re.search(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]', t):
            continue
        
        # Find best PDF line by LCS
        best_pdf = None
        best_lcs = 0
        for pt in pdf_texts:
            matcher = SequenceMatcher(None, t, pt)
            lcs_len = sum(m.size for m in matcher.get_matching_blocks() if m.size > 0)
            if lcs_len > best_lcs:
                best_lcs = lcs_len
                best_pdf = pt
        
        if not best_pdf or best_lcs < 20:
            continue
        if is_fragment(best_pdf):
            continue
        # PDF should not have extra numbered items (check for ②③④ etc.)
        md_numbered = len(re.findall(r'[①②③④⑤⑥⑦⑧⑨⑩]', t))
        pdf_numbered = len(re.findall(r'[①②③④⑤⑥⑦⑧⑨⑩]', t))
        if pdf_numbered > md_numbered + 1:
            continue
        if pdf_numbered > 0 and pdf_numbered > md_numbered:
            continue
        # Length check
        if abs(len(best_pdf) - len(t)) / max(len(t), 1) > 0.5:
            continue
        
        ws = re.match(r'^(\s*)', md_text).group(1)
        new_line = ws + best_pdf
        pass2.append((md_lineno, h, md_text, new_line, best_lcs))

print(f"Pass 2: Found {len(pass2)} lines with OCR noise and PDF match")
for lineno, h, old, new, lcs in pass2:
    print(f"\nL{lineno+1} 【{h}】 (LCS={lcs})")
    print(f"  OLD: {old[:130]}")
    print(f"  NEW: {new[:130]}")

# Only apply pass2 fixes after manual review
print(f"\nTotal: {pass1} single-char + {len(pass2)} whole-line fixes proposed")
print("Pass 2 fixes NOT applied yet — review first.")
