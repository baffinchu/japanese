#!/usr/bin/env python3
"""Convert japanese_grammar.md → japanese_grammar.html (language learning website)"""

import re
import html

with open('japanese_grammar.md', 'r', encoding='utf-8') as f:
    md = f.read()

md = md.replace('\r\n', '\n')

def esc(s):
    return html.escape(s)

def fmt_inline(s):
    s = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    s = re.sub(r'`\[([^`]+?)\]`', r'<code class="pat">[\1]</code>', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', s)
    s = re.sub(r'→', r'→', s)
    return s

lines = md.split('\n')
out = []
entry_count = 0
section_links = []

out.append('''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>日本語文型辞典</title>
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg: #f8f9fa;
  --surface: #fff;
  --text: #1a1a2e;
  --text2: #555;
  --accent: #c44536;
  --accent2: #2d6a4f;
  --accent3: #1b4965;
  --border: #dee2e6;
  --code-bg: #f0f4f8;
  --example-bg: #faf9f7;
  --hover: #f1f3f5;
  --sidebar-w: 280px;
  --header-h: 56px;
}
html { scroll-behavior: smooth; }
body {
  font-family: "Noto Sans JP", "Hiragino Kaku Gothic ProN", "Hiragino Sans", Meiryo, sans-serif;
  background: var(--bg); color: var(--text); line-height: 1.8; font-size: 15px;
}
a { color: var(--accent3); text-decoration: none; }
a:hover { text-decoration: underline; }
code {
  font-family: "Noto Sans Mono", "Hiragino Kaku Gothic ProN", Meiryo, monospace;
  background: var(--code-bg); padding: 1px 5px; border-radius: 3px; font-size: .92em;
  word-break: break-all;
}
code.pat {
  background: #e8f0fe; color: #1a56db; font-weight: 600;
}

/* Header */
.header {
  position: fixed; top: 0; left: 0; right: 0; height: var(--header-h);
  background: var(--accent3); color: #fff; z-index: 100;
  display: flex; align-items: center; padding: 0 16px; gap: 12px;
}
.header h1 { font-size: 18px; font-weight: 700; letter-spacing: .5px; }
.header .sub { font-size: 12px; opacity: .8; margin-left: auto; }
.menu-btn {
  display: none; background: none; border: none; color: #fff;
  font-size: 24px; cursor: pointer; padding: 4px 8px;
}
.header input {
  flex: 1; max-width: 400px; margin-left: 16px;
  padding: 6px 12px; border: none; border-radius: 6px;
  font-size: 14px; background: rgba(255,255,255,.15); color: #fff;
  outline: none; transition: background .2s;
}
.header input::placeholder { color: rgba(255,255,255,.5); }
.header input:focus { background: rgba(255,255,255,.25); }

/* Sidebar */
.sidebar {
  position: fixed; top: var(--header-h); left: 0; bottom: 0; width: var(--sidebar-w);
  background: var(--surface); border-right: 1px solid var(--border);
  overflow-y: auto; z-index: 50; transition: transform .25s;
}
.sidebar::-webkit-scrollbar { width: 5px; }
.sidebar::-webkit-scrollbar-thumb { background: #ccc; border-radius: 3px; }
.sidebar a {
  display: block; padding: 5px 16px; font-size: 13px;
  color: var(--text); border-bottom: 1px solid var(--border);
  transition: background .15s; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.sidebar a:hover { background: var(--hover); text-decoration: none; color: var(--accent3); }
.sidebar .count {
  padding: 8px 16px; font-size: 11px; color: var(--text2);
  background: var(--bg); border-bottom: 1px solid var(--border);
}

/* Main */
.main {
  margin-top: var(--header-h); margin-left: var(--sidebar-w);
  padding: 24px 32px; max-width: 900px;
}

/* Entry */
.entry { margin-bottom: 32px; scroll-margin-top: calc(var(--header-h) + 16px); }
.entry-header {
  display: flex; align-items: baseline; gap: 12px;
  margin-bottom: 12px; padding-bottom: 8px;
  border-bottom: 2px solid var(--accent);
}
.entry-header h2 {
  font-size: 22px; font-weight: 700; color: var(--accent);
}
.entry-header .anchor {
  font-size: 13px; color: var(--text2); opacity: .5;
}
.entry-header .anchor:hover { opacity: 1; text-decoration: none; }

.subsection {
  margin: 16px 0 8px; padding: 4px 0 4px 12px;
  border-left: 3px solid var(--accent2);
}
.subsection h3 { font-size: 16px; font-weight: 600; color: var(--accent2); }
.sub-subsection {
  margin: 10px 0 6px; padding-left: 12px;
}
.sub-subsection h4 { font-size: 14px; font-weight: 600; color: var(--text2); }

.pattern-line {
  margin: 6px 0; padding: 4px 12px;
  font-size: 14px;
}

.examples {
  margin: 8px 0 8px 16px;
}
.example {
  display: flex; gap: 8px; margin: 6px 0; padding: 4px 8px 4px 4px;
  border-radius: 4px; transition: background .15s;
  align-items: baseline;
}
.example:hover { background: var(--example-bg); }
.example .num {
  flex-shrink: 0; min-width: 28px; font-weight: 700; font-size: 12px;
  color: var(--accent); font-family: "Noto Sans Mono", monospace;
}
.example .text { flex: 1; }

.explanation {
  margin: 8px 0 8px 16px; padding: 8px 12px;
  background: var(--example-bg); border-radius: 6px;
  font-size: 14px; line-height: 1.9;
}
.marker {
  display: inline-block; padding: 0 6px; font-weight: 600;
  font-size: 12px; color: var(--accent2);
}

hr { border: none; border-top: 1px solid var(--border); margin: 8px 0; }

/* Highlight in search */
.highlight { background: #fff3cd; padding: 0 1px; border-radius: 2px; }

/* Mobile */
@media (max-width: 860px) {
  .sidebar {
    transform: translateX(-100%);
  }
  .sidebar.open { transform: translateX(0); }
  .menu-btn { display: block; }
  .main { margin-left: 0; padding: 16px; }
  .header input { max-width: none; }
  .entry-header h2 { font-size: 19px; }
  .examples { margin-left: 8px; }
  .explanation { margin-left: 8px; }
}

/* No results */
.no-results {
  text-align: center; padding: 60px 20px; color: var(--text2);
  font-size: 16px;
}
</style>
</head>
<body>

<div class="header">
  <button class="menu-btn" onclick="document.querySelector('.sidebar').classList.toggle('open')">☰</button>
  <h1>日本語文型辞典</h1>
  <input type="text" id="search" placeholder="検索…" oninput="doSearch(this.value)">
  <span class="sub">1083 entries</span>
</div>

<nav class="sidebar" id="sidebar">
<div class="count" id="result-count">1083 entries</div>
''')

# First pass: collect section links
for line in lines:
    m = re.match(r'^##\s+(.+)$', line)
    if m:
        title = m.group(1).strip()
        name = title.strip('【】')
        slug = re.sub(r'[^\w\s-]', '', name).strip().lower().replace(' ', '-')
        section_links.append((name, slug, title))

for name, slug, title in section_links:
    out.append(f'<a href="#{slug}" onclick="closeSidebar()">{esc(name)}</a>')

out.append('''
</nav>

<div class="main" id="main">
''')

# Second pass: render content
current_name = ''
current_slug = ''
first = True

i = 0
while i < len(lines):
    line = lines[i]

    # Entry header
    m = re.match(r'^##\s+(.+)$', line)
    if m:
        if not first:
            out.append('</div>')
        first = False
        title = m.group(1).strip()
        name = title.strip('【】')
        slug = re.sub(r'[^\w\s-]', '', name).strip().lower().replace(' ', '-')
        current_name = name
        current_slug = slug
        out.append(f'<div class="entry" id="{slug}">')
        out.append(f'<div class="entry-header"><h2>{esc(title)}</h2><a class="anchor" href="#{slug}">#</a></div>')
        entry_count += 1
        i += 1
        continue

    # Separator
    if line.strip() == '---':
        i += 1
        continue

    # Empty line
    if not line.strip():
        i += 1
        continue

    # Skip title line (already in header)
    if line.startswith('# ') and not line.startswith('## '):
        i += 1
        continue

    # Blockquote
    if line.startswith('> '):
        out.append(f'<blockquote>{fmt_inline(line[2:])}</blockquote>')
        i += 1
        continue

    # #### sub-subsection
    m = re.match(r'^####\s+(.+)$', line)
    if m:
        out.append(f'<div class="sub-subsection"><h4>{fmt_inline(m.group(1))}</h4></div>')
        i += 1
        continue

    # ### subsection
    m = re.match(r'^###\s+(.+)$', line)
    if m:
        out.append(f'<div class="subsection"><h3>{fmt_inline(m.group(1))}</h3></div>')
        i += 1
        continue

    # Bullet list
    if line.startswith(' *') or line.startswith('*'):
        text = line.lstrip(' *')
        if text:
            out.append(f'<div class="pattern-line">{fmt_inline(text)}</div>')
        i += 1
        continue

    # (誤), (正), (例) markers at line start
    m = re.match(r'^(\([誤正例]\))\s*(.*)$', line)
    if m:
        out.append(f'<div class="explanation"><span class="marker">{esc(m.group(1))}</span> {fmt_inline(m.group(2))}</div>')
        i += 1
        continue

    # Numbered example: (1)... 
    m = re.match(r'^(\(\d+\))(.*)$', line)
    if m:
        num = m.group(1)
        rest = m.group(2)
        out.append(f'<div class="example"><span class="num">{esc(num)}</span><span class="text">{fmt_inline(rest)}</span></div>')
        i += 1
        continue

    # Everything else → explanation paragraph
    stripped = line.strip()
    if stripped:
        out.append(f'<div class="explanation">{fmt_inline(stripped)}</div>')
    i += 1

if not first:
    out.append('</div>')

out.append('''
</div>

<script>
let navItems = [];
document.querySelectorAll('.sidebar a').forEach((a, i) => {
  navItems.push({ el: a, text: a.textContent.toLowerCase() });
});

function doSearch(val) {
  const q = val.toLowerCase().trim();
  let visible = 0;
  navItems.forEach(item => {
    const match = !q || item.text.includes(q);
    item.el.style.display = match ? 'block' : 'none';
    if (match) visible++;
  });
  document.getElementById('result-count').textContent =
    q ? visible + ' entries match' : '1083 entries';

  // Show/hide entries in main
  document.querySelectorAll('.entry').forEach(entry => {
    const id = entry.id;
    const match = !q || id.includes(q.replace(/[^\\w\\s-]/g, '').replace(/\\s+/g, '-'));
    entry.style.display = match ? 'block' : 'none';
  });

  // Highlight in entry text
  if (q) {
    document.querySelectorAll('.entry .text, .entry .explanation, .entry h3, .entry h4, .entry .pattern-line').forEach(el => {
      const html = el.getAttribute('data-orig') || el.innerHTML;
      el.setAttribute('data-orig', html);
      const re = new RegExp('(' + val.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&') + ')', 'gi');
      el.innerHTML = html.replace(re, '<span class="highlight">$1</span>');
    });
  } else {
    document.querySelectorAll('[data-orig]').forEach(el => {
      el.innerHTML = el.getAttribute('data-orig');
      el.removeAttribute('data-orig');
    });
  }
}

function closeSidebar() {
  if (window.innerWidth <= 860) {
    document.querySelector('.sidebar').classList.remove('open');
  }
}
</script>
</body>
</html>''')

with open('japanese_grammar.html', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))

print(f"Generated japanese_grammar.html")
print(f"  Entries: {entry_count}")
print(f"  Links in sidebar: {len(section_links)}")
import os
size = os.path.getsize('japanese_grammar.html')
print(f"  Size: {size:,} bytes")
