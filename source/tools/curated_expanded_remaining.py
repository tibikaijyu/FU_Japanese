#!/usr/bin/env python3
"""Reviewed names and UI text from the expanded FU extraction inventory."""
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
REVIEWED = r'''0	居住可能
14	ノヴァキッドの自由建造船
15	スカスの自由建造船
16	^#61be3f;弾薬^reset;
17	ジェムボット
18	リクスマー
19	フォックス
21	^green;質量^reset;：%.02fトン
22	^orange;速度^reset;：%d
23	^orange;俊敏性^reset;：%d
24	^orange;機動力＋^reset;：%d
25	「ひとりぼっちのタコくん、待っているだけじゃだめ。デートしたいなら、少しは努力しなくちゃ」
26	スルワーム
27	ティンティック
28	ボブフェイ
29	グロフェイ
30	クルーエクスの番兵
31	ゴスメット
32	スプーキット
33	スクイーム
34	アリープ
35	ボボット
36	ルンバ
37	アイバルブ
38	グリープ
39	クルーエクスのトーテム
40	ミアズモップ
41	マイムトップ
42	ナットミッジ
43	オーバイド
44	ペブリット
45	スナウント
46	ヴォルティップ
47	モンスター：クルーエクスのトーテム ― 系統：クルーエクスのトーテム ― バイオーム：砂漠
48	モンスター：スクイーム ― 系統：スクイーム ― バイオーム：各地
49	タウル
50	イス
51	ルビー
52	ギット
53	アルタイル II
54	ソル IX
55	オリオン I
56	アンテラス III
60	俊敏な 
61	ネクサス
62	サイ
63	S&Tダイナミクス 
64	スミシー＆ウェスタン 
65	念動の足場
66	^cyan;研究済みの晶洞石^reset;
67	フラッキン標準
68	ヴォルピン
69	アマゾンインコ
70	半影のトロイド
71	つかみ
72	踏みつけ
73	急降下
74	氷の瘴気
75	凶悪な噛みつき
80	膿の嘔吐
81	タール噴射
82	スクリプト制御の虫
83	深きもの
84	ベータ・グリープ
85	焼けただれたロッター
86	下位の同族と比べて、二倍も厄介だ。
87	コスカトル
88	エエカトル
89	エレウイア
90	アトラ
91	ヴリー
92	プリスク
93	アリ
94	イクストリ
95	カリプソ
96	フィズク
97	テイクイ
98	テピン
99	ジンクス
100	ルッパ
101	シリスペクト
102	コアトル
103	アトル
104	ジャスピティル
107	ケーのキラキラ宝物
108	 ^orange;錬金術台^reset;
109	 ^green;植物学ラボ^reset;
111	^shadow;パナシア製薬株式会社
113	^shadow;汚泥！
116	^shadow;再生＋
121	ザル
122	ザクス
123	ヴァ
124	テルヴァシュ
125	シラオ
126	-イル
127	ニプ
128	ニク
130	かっわいいいいいい
131	フィービー
132	セルマ
133	トリクシー
134	ヴェルーカ
135	ヴィヴェカ
136	ベオニカ
137	カラリーサ
138	カサンドラ
139	ジョーニー
140	ジューン
141	ジュネル
142	エイプリル
143	マーリー
144	メイ
145	ミネルヴァ
146	チャズ
147	ヤン
148	アルセニオ
149	ヴァルバトーゼ
150	ゼンタヴィアス
151	レヴァク 
152	モルフェプ 
153	オラクル 
154	フザイ 
155	プザイ 
156	サイ 
157	レドゥ 
158	スパイ 
159	ジップ 
160	サーティーン
161	ヴェクサヴィス
162	クローム
163	ラムダ
164	オラクル
165	アプ
166	ニェン
167	ジピー
168	 ピスクス
169	セクンドゥス
170	ヒピキー
171	ウィトゥス
172	 マルケルス
173	ヒヴ
174	アウグ
175	-ク
176	-ジト
177	-チ
179	マズルカ 
180	レントゲン 
181	ブレイエ 
182	マズルカ
183	レントゲン
184	ブレイエ
185	 アンコニュ
186	 エクリプス
187	アジュール
188	トゥッタナーカム
189	-ニア
190	-ルグ
191	-スヴァイク
192	-テルツ
193	-エス
194	-フモーヴ
195	シ
196	セヴ
197	ヴァトール
198	＋クリティカルダメージ＋
199	^red;-^reset;正気度
200	体力増強
201	キルポッドの超楽しいハッピータイム！
202	最大ダメージ低下
203	二郎神
205	ザズ
206	トルクラリス
209	ラレシーユ
211	ヴェックス
214	クリキット
215	ゼンタリオン
218	CYダラックス
223	ウィトゥス・ギガントゥス
225	ヴォルア
226	オムニメレヴォ
228	ラゴモルファ
230	ヴィクサリウス
231	ジニ
233	ヴィップ・ボルクル 
237	ヴェクサ
242	ジジヴァイウス
243	テスラ
246	カートゥール
248	ヴィックス
253	グルーミー
256	レディトロン
257	ゲブ
259	ゼルクサクス'''

FICTIONAL = {1,2,3,4,5,6,7,8,9,10,11,12,13,59,105,106,110,112,117,118,119,120}
TOKENS = {58,114,115}
INTERNAL = {76,77,78,79}
FORMULAS = {129,178}
IDENTIFIERS = {20,57,204,207,208,210,212,213,216,217,219,220,221,222,224,227,229,232,234,235,236,238,239,240,241,244,245,247,249,250,251,252,254,255,258,260}


def build():
    rows = json.loads((PROJECT/'reports/expanded_retained_for_review.json').read_text(encoding='utf-8'))
    rows = rows['json'] + rows['appends']
    sources = json.loads((PROJECT/'reports/expanded_retained_source_order.json').read_text(encoding='utf-8'))
    targets = {}
    for line in REVIEWED.splitlines():
        key,value = line.split('\t',1)
        targets[int(key)] = value
    retained = FICTIONAL | TOKENS | INTERNAL | FORMULAS | IDENTIFIERS
    if set(targets) & retained or set(targets) | retained != set(range(len(sources))):
        raise ValueError(f'Unreviewed entries: {set(range(len(sources))) - set(targets) - retained}')
    mapping = {sources[i]:t for i,t in targets.items()}
    # Retained entries are recorded, but do not need another manual override for
    # fictional originals already supplied by the previous review files.
    for i in retained:
        mapping[sources[i]]=sources[i]
    from build import check_translation
    errors=[{'source':s,'translation':t,'issues':check_translation(s,t)} for s,t in mapping.items() if check_translation(s,t)]
    (PROJECT/'source/manual_remaining_expanded.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    categories={'fictional_language':FICTIONAL,'runtime_placeholder':TOKENS,'internal_selector_label':INTERNAL,
                'chemical_or_species_formula':FORMULAS,'catalog_designation_or_abbreviation':IDENTIFIERS}
    decisions=[]
    for category,indices in categories.items():
        for i in sorted(indices):
            decisions.append({'source':sources[i],'reason':category,'fields':[
                {k:r[k] for k in ('id','asset','path') if k in r} for r in rows if r['source']==sources[i]
            ]})
    report={'baseline_fields':len(rows),'baseline_unique_sources':len(sources),'fully_reviewed_translations':len(targets),
            'translated_fields':sum(r['source'] in {sources[i] for i in targets} for r in rows),
            'retained_unique_sources':len(retained),'retained_fields':sum(len(d['fields']) for d in decisions),
            'retained_decisions':decisions,'structural_errors':errors,
            'reviewer':'ChatGPT; English display text translated and proper names transliterated individually.'}
    (PROJECT/'reports/expanded_remaining_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='retained_decisions'},ensure_ascii=False,indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    build()
