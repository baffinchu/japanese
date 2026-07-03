#!/usr/bin/env python3
"""
Conservative auto-correct: single-char bogus fixes + safe garbage deletions.
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

# Pass 1: Single-char bogus fixes
CHAR_FIXES = {
    '钆': 'が', '钇': 'い', '钊': 'か', '钋': 'け',
    '钌': 'こ', '钍': 'し', '钎': 'た', '钏': 'ば',
    '钐': 'ひ', '钒': 'み', '钛': 'よ',
}

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
print(f"Pass 1: {pass1} single-char fixes")

# Pass 2: Safe deletions + known 1-char kana fixes
def has_garbage(text):
    if not text: return False
    if re.search(r'[a-z][A-Z]', text): return True
    if re.search(r'[\u3000-\u9fff\uff00-\uffef][A-Z][\u3000-\u9fff\uff00-\uffef]', text): return True
    if re.search(r'[\u3040-\u309f][A-Z]', text): return True
    if re.search(r'[A-Z][\u3040-\u309f]', text): return True
    if re.search(r'[钆钇钊钋钌钍钎钏钐钒钛]', text): return True
    if '之' in text: return True
    return False

def is_structure(t):
    s = t.strip()
    return (s.startswith('#') or s.startswith('`') or
            s.startswith('*') or s.startswith('---') or not s)

pass2 = 0
for h in sorted(common):
    md_start, _, md_els = md_entries[h]
    pdf_start, _, pdf_els = pdf_entries[h]
    if md_start > MAX_LINE: continue
    pdf_texts = [pt for _, pt in pdf_els]
    if not pdf_texts: continue
    
    for md_lineno, md_line_text in md_els:
        if md_lineno > MAX_LINE: continue
        t = md_line_text.strip()
        if is_structure(t) or not has_garbage(t): continue
        if not re.search(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]', t): continue
        
        best_pdf = ''; best_lcs = 0
        for pt in pdf_texts:
            pt = pt.strip()
            if not pt: continue
            sm = SequenceMatcher(None, t, pt)
            lcs = sum(m.size for m in sm.get_matching_blocks() if m.size > 0)
            if lcs > best_lcs:
                best_lcs = lcs
                best_pdf = pt
        if not best_pdf or best_lcs < 15: continue
        
        sm = SequenceMatcher(None, t, best_pdf)
        new_text = t; changed = False
        
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == 'delete':
                old = t[i1:i2]
                if has_garbage(old) and len(old) >= 2 and not re.match(r'^[\d\s()（）]+$', old):
                    if old in new_text:
                        new_text = new_text.replace(old, '', 1)
                        changed = True
            elif op == 'replace' and i2-i1 == 1 and j2-j1 == 1:
                old = t[i1:i2]
                new = best_pdf[j1:j2]
                if has_garbage(old) and not has_garbage(new):
                    if old in new_text:
                        new_text = new_text.replace(old, new, 1)
                        changed = True
        
        if changed and new_text != t:
            ws = re.match(r'^(\s*)', md_line_text).group(1)
            md_lines[md_lineno] = ws + new_text + '\n'
            pass2 += 1

print(f"Pass 2: {pass2} surgical fixes")
print(f"Total: {pass1 + pass2}")

with open('japanese_grammar.md', 'w', encoding='utf-8') as f:
    f.writelines(md_lines)
print("Written to japanese_grammar.md")
