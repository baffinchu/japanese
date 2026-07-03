#!/usr/bin/env python3
"""
Improved comparison: match examples by content, then flag corruptions.
"""
import re
from difflib import SequenceMatcher

def parse_entries_md(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    entries = {}
    current_headword = None
    current_lines = []
    current_lineno = 1
    for i, line in enumerate(lines):
        m = re.match(r'^(?:## )?【(.+?)】', line)
        if m:
            if current_headword:
                entries[current_headword] = {
                    'start': current_lineno,
                    'end': i + 1,
                    'lines': current_lines
                }
            current_headword = m.group(1)
            current_lineno = i + 1
            current_lines = [line.rstrip('\n')]
        elif current_headword is not None:
            current_lines.append(line.rstrip('\n'))
    if current_headword:
        entries[current_headword] = {
            'start': current_lineno,
            'end': len(lines),
            'lines': current_lines
        }
    return entries

def parse_entries_pdf(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    entries = {}
    current_headword = None
    current_lines = []
    current_lineno = 1
    for i, line in enumerate(lines):
        m = re.match(r'^【(.+?)】', line)
        if m:
            if current_headword:
                entries[current_headword] = {
                    'start': current_lineno,
                    'end': i + 1,
                    'lines': current_lines
                }
            current_headword = m.group(1)
            current_lineno = i + 1
            current_lines = [line.rstrip('\n')]
        elif current_headword is not None:
            current_lines.append(line.rstrip('\n'))
    if current_headword:
        entries[current_headword] = {
            'start': current_lineno,
            'end': len(lines),
            'lines': current_lines
        }
    return entries

def extract_sentences(text):
    """Extract meaningful sentences from entry text."""
    # Remove pattern notation backtick lines
    text = re.sub(r'`[^`]+`', '', text)
    # Find lines that look like examples or explanations
    sentences = []
    for line in text.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if re.match(r'^[\(（]?\d+[)）]', line) or re.match(r'^[①②-⑩]', line):
            # Numbered example
            content = re.sub(r'^[\(（]?\d+[)）]\s*', '', line)
            content = re.sub(r'^[①②-⑩]\s*', '', content)
            if content:
                sentences.append(content)
        elif re.match(r'^[●•・]', line):
            content = re.sub(r'^[●•・]\s*', '', line)
            if content:
                sentences.append(content)
        elif len(line) > 10 and not line.startswith('`') and not line.startswith('*'):
            # General explanation sentence
            sentences.append(line)
    return sentences

def compare_text(a, b):
    """Return similarity ratio 0-1."""
    if not a or not b:
        return 0
    # Remove common OCR noise
    a = re.sub(r'[\s<>＜＞「」『』【】]', '', a)
    b = re.sub(r'[\s<>＜＞「」『』【】]', '', b)
    return SequenceMatcher(None, a, b).ratio()

# Load
md_entries = parse_entries_md('japanese_grammar.md')
pdf_entries = parse_entries_pdf('japanese_grammar_2.md')

common = set(md_entries.keys()) & set(pdf_entries.keys())
print(f"Common headwords: {len(common)}")

# Compare entries and find best matches
results = []
for headword in sorted(common):
    md = md_entries[headword]
    pdf = pdf_entries[headword]
    
    md_text = '\n'.join(md['lines'])
    pdf_text = '\n'.join(pdf['lines'])
    
    md_sentences = extract_sentences(md_text)
    pdf_sentences = extract_sentences(pdf_text)
    
    # Match each MD sentence to the best PDF sentence
    for md_s in md_sentences:
        best_sim = 0
        best_pdf = ''
        for pdf_s in pdf_sentences:
            sim = compare_text(md_s, pdf_s)
            if sim > best_sim:
                best_sim = sim
                best_pdf = pdf_s
        
        if best_sim < 0.50 and len(md_s) > 10:
            # Find line number for this md sentence
            for j, l in enumerate(md['lines']):
                if md_s in l:
                    lineno = md['start'] + j
                    break
            else:
                lineno = md['start']
            
            results.append({
                'headword': headword,
                'line': lineno,
                'md': md_s[:120],
                'pdf': best_pdf[:120] if best_pdf else '(no match)',
                'sim': best_sim
            })

results.sort(key=lambda x: x['sim'])

print(f"\n=== Top 80 Sentence-Level OCR Corruptions ===")
for r in results[:80]:
    print(f"\n【{r['headword']}】 L{r['line']} (sim={r['sim']:.2f})")
    print(f"  MD: {r['md']}")
    print(f"  PDF:{r['pdf']}")

with open('ocr_corruptions_report.txt', 'w', encoding='utf-8') as f:
    f.write(f"Total sentence-level corruptions: {len(results)}\n\n")
    for r in results[:300]:
        f.write(f"\n【{r['headword']}】 L{r['line']} (sim={r['sim']:.2f})\n")
        f.write(f"  MD: {r['md']}\n")
        f.write(f"  PDF:{r['pdf']}\n")

print(f"\nSaved to ocr_corruptions_report.txt ({len(results)} entries)")
