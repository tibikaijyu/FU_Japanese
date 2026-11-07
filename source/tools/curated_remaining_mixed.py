#!/usr/bin/env python3
"""Review the 0.1.1 display strings whose output was predominantly English."""
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
REVIEWED = r'''0	ミニノグ要塞を再訪する (6)
1	エルキウス採掘施設を再訪する (3)
2	ITDの公式ウィキページも参照してください：https://frackinuniverse.miraheze.org/wiki/ITD
4	ピースキーパー文書：ペグラシの起源
5	ビッグエイプ提供：エイペックスの起源
6	近衛兵が槍でデイヴを殺した！ デイヴを燃やそう！（誰かの夕食の写真）
7	フローランのっ槍は、フェネロックスのっ槍よりいい。見てろ！
8	推測。私たちには共通の祖先がいたのでしょうか？
10	商売敵はご勘弁。もう一人の邪魔者を追い払ってくれ。
11	俺くれえ酔っぱらったら、お前は二重に見えるのかぁ？ それとも三重か？
12	 ロアウォーカーの交易店
13	違法なノヴァキッドの小惑星鉱山を急襲した際に押収された、鉱石入りの箱。余剰分をもらえる。
14	^cyan;通常操作^reset;：テック製作\n^yellow;副操作^reset;：テックコンソール\n^green;Shift^reset;：研究メニュー
15	微小重力を兵器にしたもの。\n^yellow;通常攻撃：波動の連射^reset;\n副攻撃：^green;大きく吹き飛ばし、被ダメージを大幅に増加させる^reset;
16	敵を^yellow;鈍足^reset;・^blue;感電^reset;・^green;毒^reset;状態にできる。\n^cyan;フローラン^reset;
17	^orange;セットボーナス^reset;：\n^yellow;^reset; ハンマー／メイス／斧／大斧：ダメージ×^green;1.1^reset;
18	^orange;セットボーナス^reset;：\n^yellow;^reset; ハンマー／メイス／斧／大斧：ダメージ×^green;1.13^reset;
19	^orange;セットボーナス^reset;：\n^yellow;^reset; メイス／ハンマー／斧／大斧：習熟度+^green;19^reset;%\n^yellow;^reset; ^cyan;無効化^reset;：感電
20	^orange;セットボーナス^reset;：\n^yellow;^reset; メイス／ハンマー／斧／大斧：習熟度+^green;22^reset;%\n^yellow;^reset; ^cyan;無効化^reset;：感電
21	^orange;セットボーナス^reset;：\n^yellow;^reset; メイス／ハンマー／斧／大斧：習熟度+^green;25^reset;%\n^yellow;^reset; ^cyan;無効化^reset;：感電
22	ドクター・ホリブルのハイロトル用ゴーグル
23	^orange;セットボーナス^reset;：\n^yellow;^reset; 短剣の習熟度：+^green;15^reset;%\n^yellow;^reset; 短剣／小剣：クリティカルダメージ+^green;10^reset;／^green;20^reset;%\n^yellow;^reset; ^cyan;無効化^reset;：雪・冷気^reset;
24	^orange;セットボーナス^reset;：\n^yellow;^reset; 体力×^green;1.1^reset;\n^yellow;^reset; ショットガン／アサルトライフル：ダメージ×^green;1.15^reset;
25	^cyan;反射ダメージ^reset;\n^orange;セットボーナス^reset;：\n拳／斧：ダメージ×^green;1.25^reset;
26	^orange;セットボーナス^reset;：\n^yellow;^reset; 大鎌／生体武器：クリティカル率+^green;3^reset;%\n^yellow;^reset; ^cyan;無効化^reset;：発狂
27	宇宙属性を防ぐEPPモジュール。^green;宇宙属性耐性+30%^reset;と^cyan;エーテル無効化^reset;を付与する。
28	炎属性を防ぐEPPモジュール。^green;炎耐性+25%、炎上無効化^reset;を付与する。
29	^red;旧式のアイテム：抽出して資源を回収してください^reset;
30	^green;修理量^white;140%^green;のシールド耐久力を回復^reset;し、防御テック効率が+^cyan;42^reset;%（^white;30秒^reset;）
31	奇妙な岩。\n^orange;粉砕可能^reset;、^red;製錬可能^reset;。
32	今日はコーヒーの特売ですよ……まあ、毎日やっているんですけどね！
33	グリーンガード、フローランを助けて！
34	フローラン、いつも怒ってる！ ずっと怒ってる！ フローランを雇いたいのか？ お前、弱くてっ刺せないのか?!?!?!
35	今日も働いて小銭を稼ぐ。そして今日も、うっとうしいいたずらが一つ。
36	*はっ* いいいいい！ 史っ上最高のっ槍だ!!!
37	*はっ* いいいいい！ 史っ上最高の短剣だ!!!
38	*はっ* いいいいい！ 史っ上最高のハンマーだ!!!
39	*はっ* いいいいい！ 史っ上最高の剣だ!!!
40	英語で「公共情報端末」と書かれている。わかりやすいな。
41	ウサギの石棺（旧式）
42	突きっ刺すための、とがった棒。
43	フローラン、好きじゃない。キラキラしない……。
44	フローラン、フローラン、フローラン、やった！ 旗竿でっ刺す！
45	観察。この噴水は、一塊の大理石から彫り出されたもののようです。
46	満足。汚れひとつありません。
47	プロテクトレート学園の屋上換気口。
48	宇宙船用のアヴィアン式、四角い砲の装飾。
49	フローラン、ぷにぷにのSAILが好き！
50	キルホスのステーション用キーカードを、辺りで探すべきですね。
51	NOTゲートを組み込んだ、改造版のっ状態保持スイッチ。
52	^orange;青銅の闘技場ビーコン^reset;を使う。
53	^orange;闇の先駆者遺跡ビーコン^reset;を使う。
54	^red;*******ザザザザザザザザザザッ*****^reset;  ^orange;―接続終了―^reset;
55	レッチェル中毒（FUの食料・防具ガイド参照）
56	プロト毒（耐性：^green;毒^reset;）
57	炎の息を吐く！（^yellow;基本ガイド^reset;の^blue;特殊テック^reset;を参照）
58	低速落下^green;［下］^reset;、滑空^green;［上］^reset;。^green;[F]^reset;で発動
59	爪で斬りつける。（^yellow;基本ガイド^reset;の^blue;特殊テック^reset;を参照）
60	爪で掘る。（^yellow;基本ガイド^reset;の^blue;特殊テック^reset;を参照）
61	酸を吐く！（^yellow;基本ガイド^reset;の^blue;特殊テック^reset;を参照）'''


def build():
    rows = [json.loads(line) for line in (PROJECT/'reports/remaining_mixed_candidates.jsonl').read_text(encoding='utf-8').splitlines()]
    if len(rows) != 62:
        raise ValueError('Unexpected baseline inventory; review numeric keys before regeneration')
    targets = {}
    for line in REVIEWED.splitlines():
        key, value = line.split('\t', 1)
        targets[int(key)] = value.replace(r'\n', '\n')
    retained = {3, 9}
    if set(targets) | retained != set(range(len(rows))):
        raise ValueError('Unreviewed candidates')
    mapping = {rows[i]['source']:target for i,target in targets.items()}
    for i in retained:
        mapping[rows[i]['source']] = rows[i]['source']
    (PROJECT/'source/manual_remaining_mixed.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    from build import check_translation
    errors = [{'source':s,'translation':t,'issues':check_translation(s,t)} for s,t in mapping.items() if check_translation(s,t)]
    report = {'baseline_version':'0.1.1','reviewed_unique_sources':len(rows),'fully_translated_unique_sources':len(targets),
              'restored_fictional_language_unique_sources':len(retained),'structural_errors':errors,
              'restored_fictional_language':[rows[i] for i in sorted(retained)],
              'reviewer':'ChatGPT; individual full-source comparison'}
    (PROJECT/'reports/remaining_mixed_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='restored_fictional_language'},ensure_ascii=False,indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    build()
