#!/usr/bin/env python3
"""
Targeted surgical fixes for specific corrupted lines.
Each fix uses the PDF reference to replace only the garbled region.
"""
import re

with open('japanese_grammar.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixes = []

def fix_line(lineno, old_text, new_text):
    """Replace old_text with new_text on the given 1-indexed line."""
    i = lineno - 1
    t = lines[i]
    if old_text not in t:
        print(f"WARN: L{lineno}: '{old_text[:30]}...' not found!")
        return False
    lines[i] = t.replace(old_text, new_text, 1)
    fixes.append((lineno, old_text[:50], new_text[:50]))
    return True

# L407: ア力デ: しうじpL3 → アカデミー賞
fix_line(407, 'ア力デ: しうじpL3', 'アカデミー賞')

# L593: EhJ合いかは → をするとは (but keep context)
fix_line(593, 'EhJ合いかは、あいつは', 'をするとは、あいつは')

# L932: 老中く (leading garbage), eV?54 → garbage removal
fix_line(932, '老中く (2) ちょっと来客があったりするかもしれませんが、いずれにしろひじかんこの日なら時間が取れるので eV?54 大丈夫です。',
              '(2) ちょっと来客があったりするかもしれませんが、いずれにしろこの日なら時間が取れるので大丈夫です。')

# L1294: し、しこA?kE3 → remove garbage
fix_line(1294, 'し、しこA?kE3 (4) 昔は新婚旅行と言えばハワイい法だったが、今やトルコやエジ才 ずらも珍しくない。',
               '(4) 昔は新婚旅行と言えばハワイだったが、今やトルコやエジプトも珍しくない。')

# L1988: てvE → て、へんはV 変な) イズ → 変なノイズ
fix_line(1988, 'てvE の程度だが、このレコードにはへんはV 変な) イズ', 
               'ての程度だが、このレコードには変なノイズ')

# L3223: V shV → remove garbage
fix_line(3223, 'V shV (2) もんく言うんじゃないの。自分はできない<せに。',
               '(2) もんく言うんじゃないの。自分はできないくせに。')

# L3285: bN (とおなじ) <らいのN → N (とおなじ) くらいのN
fix_line(3285, 'bN (とおなじ) <らいのN', 'N (とおなじ) くらいのN')

# L4898: J → 」, [ → 「, vvI → は
fix_line(4898, '「何かをしても、それで充分だとはいえないJという意味。(1) は「注意すればするほどいい」、(2) は[早いほどvvI の意味。',
              '「何かをしても、それで充分だとはいえない」という意味。(1) は「注意すればするほどいい」、(2) は「早いほどいい」の意味。')

# L5125: しvD → こと, 必ょう要 → 必要
fix_line(5125, 'しvD ではない。心からの謝罪が必ょう要だ。',
               'ではない。心からの謝罪が必要だ。')

# L5146: VsvA v ら → すら, keep rest
fix_line(5146, 'です VsvA v ら病院', 'ですら病院')

# L7474: うyL上5 → 、, もらちょっとえる → もらえる
fix_line(7474, '故し地うyL上5 障したら、ただで修理してもらちょっとえる。',
               '故障したら、ただで修理してもらえる。')

# L10526: 三がう ? → remove, 続< → 続く, 思いん?あ nonLんきや → 思いきや, 雨 → 雨
fix_line(10526, '三がう ? (2) 今年の夏は猛暑が続<と思いん?あ nonLんきや、連日の雨で冷害の心配さえでてきた。',
               '(2) 今年の夏は猛暑が続くと思いきや、連日の雨で冷害の心配さえでてきた。')

# L14331: vV → て, V かん → かん→clean
fix_line(14331, '比べ vV なかまちなんばいて、田舍の町へ行くのは何倍も V かん時間がかかる。',
               '比べて、田舎の町へ行くのは何倍も時間がかかる。')

# L15520: あ意ひこ3宋名こ→正子さん朝日高,  LpoL→
fix_line(15520, 'あ意ひこ3宋名こはるこ正子：へえ、春子さんも朝日高 こうLpoLん校出身なの。',
               '正子：へえ、春子さんも朝日高校出身なの。')

# L17381: bE し V ても → ても, ほうおく → おく
fix_line(17381, 'おも B : たいしたことはないと思っ bE し V ても、一度医者に行ってほうおく方がいいよ。',
               'B : たいしたことはないと思っても、一度医者に行っておく方がいいよ。')

# L19154: ょて 6vL5 ん → ません
fix_line(19154, 'で B : いいえ、まだ出ていませょて 6vL5 ん。予定は来週です。',
               'B : いいえ、まだ出ていません。予定は来週です。')

print(f"Applied {len(fixes)} surgical fixes")
for lineno, old, new in fixes:
    print(f"  L{lineno}: {old}  →  {new}")

with open('japanese_grammar.md', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"\nWritten to japanese_grammar.md")
