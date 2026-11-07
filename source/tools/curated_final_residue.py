#!/usr/bin/env python3
"""Close the final English-clause/whole-field findings from the selected audit."""
import json
from pathlib import Path
from common import read_asset
from build import check_translation

PROJECT=Path(__file__).resolve().parents[1]
ROOT=PROJECT.parent


def build():
    # Read exact immutable originals from the pinned FU checkout.
    kevin=read_asset(ROOT/'fu-upstream/codex/documents/scienceoutpost_kevin.codex')['longContentPages'][5]
    kevin_ja=(
        '^#EDB347;1月3日^#FFFFFF; ― 研究設備や消耗品がなくなったという報告が届いている。特にCO2のボンベが多い。保管庫の警備を強化することにした。\n\n'
        '^#EDB347;1月5日^#FFFFFF; ― 下層で爆発が起きた。調べると、ケヴィンが冷蔵庫の予備部品とダクトテープで作ったCO2砲らしきもので、鋼の刃に丸太を撃ちつけていた。後になって、私の個人保管室に、スティーブ叔父さんの写真で飾った祭壇を作っていたこともわかった。どうやって写真を手に入れたのか、見当もつかない。片隅には削った木がいくつも積まれ、反対側には、割った丸太で作られた、怒れるウシガエルに乗る叔父の巨大な像が飾られていた。\n\n'
        '^#EDB347;1月9日^#FFFFFF; ― ケヴィンが大量の濃硫酸、硝酸、トルエンを盗んでいるところを捕まえた。部屋を調べると、側面にクレヨンで「エクエストリアに死を」と書きなぐった、釘の大箱が見つかった。\n\n'
        '^#EDB347;1月15日^#FFFFFF; ― ケヴィンは、今やほぼ失われた地球の……楽器……そう呼べるなら、だが……をたたえ、今週を「ブブゼラ感謝週間」と宣言した。約11秒後には、私たちは彼を殺したくなった。すでに七時間目だ。アンシブル・ネットワークで新しいライフルを買った。\n\n'
        '^#EDB347;1月24日^#FFFFFF; ― アンシブル・ネットワークから、例のブブゼラが約400 000本届いた。次回の大量購入に使える15%割引券も付いていた。その後、ケヴィンがブブゼラをたき火の燃料にして、ネズミを焼いているところが見つかった。\n\n'
        '^#EDB347;1月30日^#FFFFFF; ― ケヴィンは、ヒューマンが地球で飼っていた、エイペックスに似た、もっと大きく原始的な動物のために神殿を作った。「ハランバー」とかいう名前らしい。備蓄のバナナを何本も持ち去り続けている。つまり、食料保管庫のパスワードを……また変えなければならない。'
    )
    sbvn=read_asset(ROOT/'fu-upstream/interface/scripted/sbvn/games/pandorasboxmonsterfieldguide/pandorasboxmonsterfieldguide.sbvn')
    glitch=sbvn['scenes']['glitchtop4']['text']
    prefix,tail=glitch.split('product ',1)
    if set(tail.split())!={'of'}:
        raise ValueError('The Glitchtop corruption sequence changed')
    repeats=len(tail.split())
    glitch_ja=(
        '評判が広まり、目撃報告も寄せられたことから、この怪物には「グリッチトップ」というあだ名が付けられた。'
        '何かによって生み出された可能性があると推測されている。その何かとは、'
        + ' '.join(['の']*repeats)
    )
    manual={'Xaerolloux':'ザエロルー',kevin:kevin_ja,glitch:glitch_ja}
    # Preserve every other sentence in the long MT changelog. Only the four
    # independently located untouched clauses are manually replaced here.
    source=read_asset(ROOT/'fu-upstream/_FUversioning.config')['changelog']
    base=json.loads((ROOT/'translation-work/machine_translations.json').read_text(encoding='utf-8'))[source]
    if isinstance(base,dict):base=base.get('translation',base.get('ja'))
    edits={
        '* Touched up on mech fall damage scaling (it was scaling twice as hard as intended, and triggering per impact with tiles while falling, oops!). ': '* メカの落下ダメージ計算を調整（倍率が意図した二倍になり、落下中にタイルへ接触するたびにダメージが発生していた問題を修正）。 ',
        '* ion rifle now pierces, making it worth the energy cost per shot.': '* イオンライフルに貫通効果を追加し、一発あたりのエネルギー消費に見合う性能にした。',
        '* Crank Rifle, along with the Breach guns, have lower energy cost per shot, to make them more appealing.': '* クランクライフルとブリーチ系の銃の、一発あたりのエネルギー消費を減らし、使いやすくした。',
        'revised xi check in madnessdata.lua to check if the stat is positive.': 'madnessdata.lua内のシー種族判定を修正し、能力値が正かどうかを確認するようにした。'
    }
    for old,new in edits.items():
        if base.count(old)!=1:raise ValueError('Changelog residue changed: '+old)
        base=base.replace(old,new)
    partial={source:base}
    errors=[{'source_prefix':s[:150],'issues':check_translation(s,t)} for s,t in {**manual,**partial}.items() if check_translation(s,t)]
    if errors:raise ValueError(errors)
    (PROJECT/'source/manual_remaining_final.json').write_text(json.dumps(manual,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (PROJECT/'source/partial_remaining_changelog.json').write_text(json.dumps(partial,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    report={'full_source_reviews':3,'partial_source_reviews':1,'corrected_changelog_clauses':len(edits),
            'glitchtop_repetition_count_preserved':repeats,
            'glitchtop_note':'Original deliberately repeats of 2612 times; Japanese corruption repeats の the same number of times. This removes MT amplification while preserving the authored interruption.',
            'structural_errors':errors,'reviewer':'ChatGPT'}
    (PROJECT/'reports/final_residue_repairs.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':build()
