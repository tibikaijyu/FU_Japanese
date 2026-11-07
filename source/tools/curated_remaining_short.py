#!/usr/bin/env python3
"""Additional complete reviews of short strings with untranslated English."""
import json
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[1]
REVIEWED=r'''0	キルホスの文明化についての記録
1	キルホスの文明化を詳しく記した本
2	最初はピンクの*ヒック*……ゾウさん。今度はしゃべるイエティかよ*ゲップ*。次は何だぁ？
3	^green;散らかった部屋^white;テーマの家具一式。^green;25%もお得！^reset;
4	散らかった部屋セット
5	庶民のスカートとサンダル。体力再生+^green;0.3^reset;。
6	厚い手袋と、ほんの少しの布。ダメージ+^green;5^reset;%。
7	最低限の肌を隠す布と、歯を蹴り飛ばすには十分なサンダル。ダメージ+^green;5^reset;%。
8	威厳と名誉を、一つの素敵な装いに。闇耐性+^green;5^reset;%。
9	粋な装いで艦隊を率いよう。闇耐性+^green;5^reset;%。
10	^orange;セットボーナス^reset;：\n^yellow;^reset; ^#969600;発光^reset;\n^yellow;^reset; ^cyan;耐性^reset;：精神^green;20^reset;%\n^yellow;^reset; 生体／ブリスター武器：クリティカル率+^green;4^reset;%、ダメージ×^green;1.15^reset;^reset;\n^yellow;^reset; ^cyan;無効化^reset;：毒・プロト毒・膿・液体窒素
11	フローラン、さっしたい！
12	やあ、冒険者！ フローランも仲間に入って、悪党どもをっ刺していいか?!?!?
13	フローラン、さっすことと、切りっ裂くことしか知らない……。
14	重圧。バーガーフールへようこそ！ 私たちがバーガーを作り、あなたが決まりを作ります！
15	デジャヴュを感じたことはある？
16	ショートの卵！ フローラン、ショートと遊ぶの大好き！
17	ちっこいキラキラした明かりが、ずらりとつながってるな。
18	変なベッド。フローラン、気分が悪くなる！
19	変な本棚。フローラン、気分が悪くなる！
20	変な戸棚。フローラン、気分が悪くなる！
21	変な椅子。フローラン、気分が悪くなる！
22	変な箱。フローラン、気分が悪くなる！
23	変なソファ。フローラン、気分が悪くなる！
24	変な机。フローラン、気分が悪くなる！
25	変なランプ。フローラン、気分が悪くなる！
26	変な引き出し。フローラン、気分が悪くなる！
27	変なテーブル。フローラン、気分が悪くなる！
28	変な食べ物の箱。フローラン、気分が悪くなる！
29	変な浮かぶ明かり。フローラン、気分が悪くなる！
30	変な小さい食べ物の箱。フローラン、気分が悪くなる！
31	変なもの。フローラン、気分が悪くなる！
32	変な丸椅子。フローラン、気分が悪くなる！
33	華麗な壺。シリでは珍しい高級品だ。
34	フローラン、地図を使っていろんな場所へ行く。
35	好奇。デジャヴュを感じたことはありますか？ さっき接客したはずなのに……またここにいらっしゃる。
36	トングとトレイのスタンド
37	バーガーフールの創業者に愛されたペットで、会社のマスコットでもあるトリクシーのぬいぐるみ。
38	バーガーフールを象徴する帽子の、壁用ステッカー。
39	散らかったクローゼット
40	散らかったサイドテーブル
41	貝殻、壊せる！ 中に何がある？
42	リボンの絹を見ると、フローラン、イグゾリングの糸を思い出す
43	リボンの絹を見ると、フローラン、イグゾリングの糸を思い出す。
44	普通のANDゲートと大差はないけれど、内蔵のNOTゲートが便利だ。
45	満足。普通のANDゲートと大差はありませんが、内蔵のNOTゲートが便利です。
46	普通のORゲートと大差はないけれど、内蔵のNOTゲートが便利だ。
47	普通のORゲートとあまり変わらない。でも、中のNOTゲートが便利だ。
48	満足。普通のORゲートと大差はありませんが、内蔵のNOTゲートが便利です。
49	作動するたびに、2秒間、信号をっ止める。
50	作動するたびに、3秒間、信号をっ止める。
51	作動するたびに、4秒間、信号をっ止める。
52	作動するたびに、5秒間、信号をっ止める。
53	次は^orange;水耕栽培トレイ^reset;を作ろう。^orange;電力作業台^reset;で製作でき、^green;植物を素早く育てる^reset;ことができる。
54	^orange;水耕栽培トレイ^reset;を届ける。
55	職員の飲み会で、ケヴィンが私の^orange;水耕栽培トレイ^reset;に小便をかけて壊してしまった！ 作り直そうにも^orange;電力作業台^reset;を持っていないんだ……代わりのトレイを持ってきてくれないか？
56	この技術があれば、^orange;空中ダッシュ^reset;のテックを強化できそうだ！ 新しい^orange;高性能ダッシュ^reset;で、性能が大きく向上するはず！
57	この装置のおかげで、同じ原理を^orange;瞬間ダッシュ^reset;のテックにも応用できる！ ^orange;空中瞬間移動^reset;があれば、今よりうまく飛び回れそうだ！
58	高度な古代技術を使うと、^orange;五段ジャンプ^reset;の設計図が姿を現した。一度や二度だけでなく、^orange;5回ジャンプできる^reset;はずだ！
59	^orange;ティア3.5^reset;\n\n気味は悪いが役に立つ、ブリスターポッドの栽培を習得した。生体発光する植物で、武器や防具の製作だけでなく、拠点を飾る照明にも使える。'''

def build():
    rows=json.loads((PROJECT/'reports/residual_short_review_candidates.json').read_text(encoding='utf-8'))
    target={}
    for line in REVIEWED.splitlines():
        i,t=line.split('\t',1);target[int(i)]=t.replace(r'\n','\n')
    if set(target)!=set(range(len(rows))):raise ValueError('Missing reviewed candidate')
    mapping={rows[i]['source']:t for i,t in target.items()}
    from build import check_translation
    errors=[{'source':s,'translation':t,'issues':check_translation(s,t)} for s,t in mapping.items() if check_translation(s,t)]
    (PROJECT/'source/manual_remaining_short.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    report={'reviewed_unique_sources':len(mapping),'structural_errors':errors,'reviewer':'ChatGPT; full-source review'}
    (PROJECT/'reports/remaining_short_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if errors:raise SystemExit(1)

if __name__=='__main__':build()
