#!/usr/bin/env python3
"""Reviewed Japanese replacements for the v0.1.1 untranslated display inventory.

The numeric keys refer to the stable first-occurrence order in the bundled
retained_011_baseline.json, never to the current extractor's live ordering.
Fictional utterances are explicitly retained rather than assigned invented
meanings. Roman model numbers, placeholders, and familiar technical abbreviations
are preserved where they are part of an otherwise Japanese display string.
"""
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
BASELINE = PROJECT / 'reports/retained_011_baseline.json'

# Every entry below was individually compared with its English source and field.
# Literal \\n preserves the original number of display line breaks.
REVIEWED = r'''000	ブライン・スター (6+)
001	ブライン・スター (6+)（再訪）
002	レテイア施設 (8)
003	レテイア施設 (8)（再訪）
004	レテイア研究所 (6)
005	レテイア研究所 (6)（再訪）
006	エルキウス採掘施設 (3)
007	^#7fac66;デルタ・フレイヤ II^reset; (7+)
008	^#7fac66;デルタ・フレイヤ II^reset; (7+)（再訪）
009	天空の大通り (6+)
010	天空の大通り (6+)（再訪）
011	不落の塔 (6)
012	不落の塔 (6)（再訪）
013	緑に覆われた遺跡 (2)（再訪）
014	穴掘りバチのオス
015	^orange;高性能^reset;顕微鏡
016	プロト核
017	プロト惑星
018	デルタ・フレイヤ II
019	巣穴 (FU)
020	リンゴ園
021	シアンの大量死
022	イカシャ・ヒロチ
023	ケーの日誌
030	私に従わせた。そして、その過程でンガーを発見した。異教徒の神であり、炎を吐き、千の雷鳴のように吠える存在だ。私は恐怖を知った。〈この先には、まだ何百ページも続いている。読み進めるほどに、内容は狂気じみてくる。それでも何かが不安をかき立てる。とりわけ、この本が見つかった場所を考えると。〉
031	ウルカク・ビジカル
032	デトナトゥス・モンドゥス
033	キキクティク・シツァ
034	フレクスナール・ヴォルシュトク
035	エロプティクス 第I巻
036	エルドゥーカーの暮らし
037	ペグラシの物語歌
038	［残り400ページ］
039	第I巻
040	アヴィアンの暮らし 第I巻
041	グリーンフィンガーの覚書：フローランのグリーンフィンガーたち
042	ファリトゥの暮らし 第I部
043	ファリトゥの暮らし 第II部
044	ファリトゥの宇宙航行 第I部
045	ファリトゥの宇宙航行 第II部
046	ヘンドラート・イル
047	〈この本の記録は、何世紀にもわたるようだ。彼らが創造した名もなき種族についての記録は無数にあるが、役立ちそうな内容が現れるのは、最初の記録からおよそ824年後になってからだ。〉彼らは従順な性質を保つと考えられていた。初期の世代から、怒りや激怒を感じる能力を意図的に取り除いていたからだ。
048	シャサ・ウル・ヴェンディ
049	イテプ・クリ
050	ヴァパジ・フレクヴァイ
051	シアンの言語
052	テルシアンの暮らし 第1巻
053	テルシアンの暮らし 第2巻
054	テルシアンの暮らし 第3巻
055	テルシアンの暮らし 第4巻
056	テルシアンの暮らし 第5巻
057	テルシアンの暮らし 第6巻
058	シアンとのつながり
059	テルシアンの暮らし 第7巻
060	いやあああああああ!!!
061	ヴェヌシュにかけて！ 別の飲み仲間を探さなきゃな！
062	@#$@$#@ *!!!ヒック!!!*
063	*ゲェェェップ!!*
064	また一匹、この世界から怪物を一掃してやった！
065	ああああああああああああああああああああああ！
066	キィィィ！
072	このひどい有様を直せって言ったのに、何ひとつやってないじゃないか。
073	さあさあ、お立ち会い！ 皆さん、<selfname>の店でお買い物を！
074	*!!!ヒック!!!*
075	グオオオオオオ!!
076	*ヒック*
077	… *ゲップ*
078	ここにゃ、もう一人分の酒なんて足りねえんだよぉ！
079	12枠
080	16枠
081	24枠
082	32枠
083	40枠
084	48枠
085	56枠
086	9枠
087	3枠
088	128枠
089	移動
090	無害 (I)
091	攻略不能 (VIII)
092	^red;にゃあ。^reset;
093	不毛地 II
094	不毛地 III
095	肉塊
096	錆
097	 惑星情報 GPS
098	  Frackin' Universe 研究設備・製作案内
099	強化後： 
100	 会話画面
101	^white;ジャガーノート
102	^green;リナジャイザー
103	^red;デヴァステーター
104	^#FF2222;ウォーモンガー
105	惑星情報
106	テック製作
107	^yellow;膿
108	^#5B6177;タール
110	^#61be3f;連射数^reset;
111	^green;発射体数^reset;
112	^yellow;ヨープ^reset;
113	^#8d8d8d;男性
114	^#b9b5b2;遺物
115	レベル100
117	レシピ
118	^#b9b5b2;料理
119	^#b9b5b2;レシピ
120	ビーフジェフ
121	キルホスのハッカー雇用契約
122	ケーの幽霊ランタン
123	フックショット MkII ^red;^reset;
124	シアンの鉤付きツタ
125	エイペックスの設計図（エネルギー）
126	エイペックスの設計図（攻撃力）
127	エイペックスの設計図（体力）
128	ハイロトルの設計図（攻撃力）
129	^green;クリティカル率+3%、クリティカルダメージ+5^reset;
130	^green;体力再生+0.07%、防御力+5、ハチ刺され無効^reset;
131	^green;クリティカル率+3%^reset;
132	^green;体力再生+0.08%^reset;
133	クワイタスの盾
134	シアンの盾
135	^green;体力再生+0.5%、シールドバッシュの押し出し+6^reset;
136	^green;プロト毒・生体汚泥への耐性、シールドバッシュの押し出し+12、再生0.2^reset;
137	ロボットポッド
138	違法な研究ディスク
139	高品質の虫取り網
140	究極の虫取り網
141	究極を超えた虫取り網
142	奇怪な官能本
143	忌まわしい巻き貝
144	多鉱種探知機 MKVI ^red;^reset;
145	多鉱種探知機 MKVII ^red;^reset;
146	クワイタスのブーメラン
147	テレブリウムのブーメラン
148	ソラスの刀
149	ヴァリアントゥスの刀
150	三連射
151	ルナリ・スティンガー
152	クワイタスのクロスボウ
153	<elementalName>のオーラ
154	戦槍の連続攻撃
155	ノマドの斧
156	シアンの大剣
157	平和・愛・団結・敬意（PLUR）
158	シアンの短剣
159	二股の刃で、楽しさも二倍。
160	クワイタスの大斧
161	シアンの大斧
162	クワイタスのハンマー
163	虹色の刀
164	ケルの無欠の刀
165	クワイタスの刀
166	クワイタスのメイス
167	虹色のレイピア
168	クワイタスの短槍
169	トリタニウムの短槍
170	^#a5ff00;エルダーの刃^reset;
171	クワイタスの槍
172	シアンの槍
173	レイスヴェールの槍
174	NPC用対空砲
175	驚異のジップザップ
176	^#ffbe32;ギャラルホルン^reset;
177	^#bb39ce;イエティ^reset;
178	ヴェルー・ライトウィーバー
179	炎スライムの触手 II
180	球体ランチャー
181	胞子ランチャー
182	テスラブラスト
183	爆発キノコランチャー
184	アーコン・ブラスター
185	アーコン・ブラスター MkII
186	デウス・スマッシャー
187	ネコパルト
188	虹色のオーブランチャー
189	虹色のサブマシンガン
190	ファーサイト XR-20
191	放射線シュレッダー
192	ファーサイト XR-72
193	ヒャッハー、最高だぜ！
194	^red;フ^white;リーダ^blue;ム^reset;
195	ノマドの戦闘ライフル
196	ノマドのライフル
197	刺針銃
198	火葬バルカン
199	^cyan;キルホス・ブラスター II^reset; ^yellow;^reset;
200	アーコン・ロンギヌス
201	^cyan;ロンギヌス MkII^reset; ^yellow;^reset;
202	P-7採掘機 ^cyan;^reset;
203	A-7C採掘機 ^white;^reset;
204	クワイタスのリボルバー
205	クワイタスのアサルトライフル
206	クワイタスのピストル
207	クワイタスの狙撃銃
208	シアンのアームブラスター
209	シアンの放射線放射器
210	シアンの拡散バースト銃
211	Tk-4 ケテル
212	フェルショット・リボルバー
213	ポラリス
214	トゲムシランチャー
215	テスラガン
216	^cyan;マーシー^reset;
217	^cyan;破片ニードラー^reset;
218	^red;灼熱ニードラー^reset;
219	^#5aff00;麻酔ピストル^reset;
220	アーコン・ウォーデン
221	ジスリサイトのアサルトライフル
222	恋する雲
223	うんちの達人^yellow;^reset;
224	虹色のムチ
225	文書の記録帳
226	フレックスのマント
227	シアンのランタン球根
228	エイミー・ヘッジリープのマスク
229	クルーエクスの番兵のマスク
230	ソニック・ヘッジリープのマスク
231	裁定者の兜
232	キングスライクの帯
233	捕獲探検家のパック
234	目を守る日よけ効果も二倍！
235	ポリスレッドの上着
236	無比のシャツ
237	ノマドのローブ
238	シアンの革の胸当て
239	シアンの革の兜
240	シアンの装甲胸当て
241	シアンの装甲兜
242	ムタヴィスクの兜
243	ノーチラスのヘルメット
244	スチームパンクのスラックス
245	ラヴェジャーの甲殻鎧
246	ラヴェジャーのローブ
247	イレギュラーハンターの胸当て
248	イレギュラーハンターのレギンス
249	アーコンの鎧
250	アーコンの兜
251	リヴァイアサンのレギンス
252	ワープ採掘者のテックジャケット
253	ワープ採掘者のテックパンツ
254	レギオニーの兜
255	レギオニーのすね当て
256	オオカミのレギンス
257	レッチェルの胸当て
258	レッチェルの兜
259	アサシニーの鎧
260	アサシニーのフード
261	デンシニウム X7の兜
262	異形の肉の胴体
263	異形の肉の頭部
264	テックナイトの兜
265	マークVI防毒マスク
266	シーのキチン
267	闇耐性 I
268	弾薬ベルト I
269	宇宙属性オーラ I
270	宇宙属性オーラ II
271	電撃オーラ I
272	電撃オーラ III
273	炎オーラ I
274	炎オーラ III
275	炎オーラの首輪 III
276	氷オーラ I
277	氷オーラの首輪 I
278	……なんじゃこりゃ？
279	毒オーラ I
280	毒オーラの首輪 I
281	ウランオーラ I
282	闇オーラ I
283	エネルギー再生×^green;1.15^reset;\n^green;発光効果を付与^reset;
284	^cyan;ゼリーの塊^reset;
285	イクティデモナエの胴体
286	ステゴヴァプティの胴体
287	ステゴヴァプティの頭蓋骨
288	^#88e25b;ラソンブリウムの種^reset;
289	ヴェクスロイド
290	ワビーワビー
291	^#88e25b;エーテリウム合金^reset;
292	^#88e25b;トリタニウムインゴット^reset;
293	^#ffe50e;エルダーの核^reset;
294	^#ffe50e;偏方多面体^reset;
295	^#ffe50e;エルダーの胸像^reset;
296	^#ffe50e;ぼろぼろの魔導書^reset;
297	すりつぶしたリンゴ
298	ティアナッツバタークッキー
299	シアンのエール
300	カフェオレ
301	コード・ゼルケシウム
302	バナナのシュナップス
303	チェリーのシュナップス
304	シナモンのシュナップス
305	ブドウのシュナップス
306	タイムワインダーのシュナップス
307	リンゴとシナモンのパイ
308	スナーシュド・ガーフリップ
309	ソラスジャム
310	ティアナッツバターサンド
311	重力刺激剤
312	^#77acc3;コルヴェクスのパテ^reset;
313	^#77acc3;ヘルメスの錠剤^reset;
314	シーの遺物
315	超強力刺激剤
316	X刺激剤
317	防御フィールド I
318	防御フィールド II
319	防御フィールド III
320	防御フィールド V
321	^yellow;^reset;^cyan;無効化^reset;：プロト毒、^cyan;防御力+7^reset;：2分
322	^yellow;^reset;^cyan;体力+5^reset;、^cyan;エネルギー+6^reset;：3分
323	ブレックスサボテンの樹液
324	^yellow;^reset;^#7f2282;発光^reset;：5分
325	^yellow;^reset;^cyan;体力を40%回復^reset;：1分
326	^yellow;^reset;^cyan;吸収+100%^reset;：30秒
327	^yellow;^reset;^cyan;毒耐性+20%^reset;：2分
328	^yellow;^reset;^cyan;体力を70回復^reset;：2秒
329	^yellow;^reset;^cyan;体力+8^reset;、^cyan;エネルギー+12^reset;：3分
330	^yellow;^reset;^cyan;体力+8^reset;：3分
331	^yellow;^reset;^#b3b398;発光^reset;：2分
332	^yellow;^reset;^cyan;エネルギー+145^reset;：1分
333	^yellow;^reset;^cyan;体力を30回復^reset;：2秒
334	^yellow;^reset;^cyan;無効化^reset;：凍結・タール・泥：3分
335	^yellow;^reset;^cyan;闇の汚染を無効化、闇耐性+10%^reset;：2分
336	^yellow;^reset;^cyan;体力+12^reset;、^cyan;エネルギー+20^reset;：3分
337	^yellow;^reset;^cyan;体力+17^reset;、^cyan;エネルギー+40^reset;：2分
338	^yellow;^reset;^cyan;体力を244.7%回復^reset;：220秒
339	^yellow;^reset;^cyan;氷属性の反射ダメージ200%^reset;：1分
340	^yellow;^reset;^cyan;体力+21^reset;：3分
341	^yellow;^reset;^cyan;体力+21^reset;、^cyan;エネルギー+30^reset;、^cyan;体力を80%回復^reset;：2分
342	^yellow;^reset;^cyan;体力を10回復^reset;：2秒
343	ヴァシュタの爪
344	ヴェクスタングの雄しべ
345	^yellow;^reset;^cyan;宇宙属性耐性+30%^reset;：3分
346	^blue;ジョジャ^reset;コーラ
347	アエンの原木
348	雨雲の足場
349	ナイターのテックブロック
350	パイクリートの基礎ブロック
351	ティンセルブッシュの投げ矢
352	既視感を覚えている
353	この部族は、ずーっと昔からここに住んでる！
354	うちの料理は最高だぜ！
355	はい、了解でっす！
356	はい、了解でっす！
357	ハチだあああああああ！
358	パァァァァァァァァァァティー！
359	ウオオオオオオオオオオオオオオオオオ！
360	シアンの探検家
361	土壇場の<role>
362	ハクスヴェン IIもオミクロン・シータ IIIも、消息を絶ったそうだ。
363	さっせえええ！
364	情けをかけるな！
365	カテーテルバッグ一つに、ワッフルは何枚入るかな？
368	また串刺しにできそうなブタが来たみたいだな！
369	よし、これでまた何体かの死体が「埋葬」されたな……。
370	シアンのモデルの肖像画
371	^orange;アヴァリの調理器^reset;
372	こんな家具には、虫食いの本さえ置きたくありません。
373	^cyan;養蜂作業台^reset;
374	ボスの右側スポナー
375	^cyan;超能力収集器^reset;
376	^yellow;入居契約書 マークII^reset;
377	^yellow;入居契約書 マークII（極小）^reset;
378	^orange;武器庫^reset;
379	^orange;錬金術台^reset;
380	^orange;植物学ラボ^reset;
381	^cyan;ふるい機^reset;
382	^orange;自動組立機^reset;
383	捕獲ポッド画像再生成装置
384	^orange;超能力作業台^reset;
385	シアンの成形球根
386	^orange;発酵槽^reset;
387	シアンの井戸
388	ドゥームドアの飾り
389	プリズムドアの飾り
390	砂岩の両開きドアの飾り
391	リンゴのぬいぐるみ
392	アーヴィスとサークリス、二つの象徴を描いた旗。
393	破れたサークリスの旗
394	極小の水晶操作盤
395	この卵は、普通の卵の少なくとも二倍の大きさがある。
396	ムタヴィスク
397	ヴァシュタ
398	シアンのアルファ球根
399	プロテクトレートのもう一つの旗だ！
400	ボルト・オーズ
401	おっかし！
402	ぷるぷる、弾むっスライム！
403	お祭りの電飾
404	フローラン、このドアの仕組みはまだよくわからない。
405	収穫タレット v1
406	収穫タレット v2
407	収穫タレット v3
408	^red;出力1：^reset;一部充填 ^red;出力2：^reset;満杯
409	おっひさまの本！
410	おっひさまの丸椅子！
411	荒地マイクロフォーマー
412	カリーチェ地帯マイクロフォーマー
413	雲マイクロフォーマー
414	オアシスマイクロフォーマー
415	エルキウスマイクロフォーマー
416	^orange;拷問檻^reset;
417	巣の塊
418	電力ノード
419	^cyan;エルキウス変換器^reset;
420	^cyan;先駆者のメインフレーム^reset;
421	^cyan;先駆者の炉^reset;
422	ファーシャの茎
423	アカガサキノコ
424	リンゴの樽
425	ムーシのぬいぐるみ
426	文字「I」。
427	文字「I」
428	文字「Z」。
429	文字「Z」
431	こっわせ！
432	ペグラシの雪像の胴体
433	^orange;ムーシの子のスポナー^reset;
434	^orange;フィールド発生器^reset;
435	^cyan;太陽光パネル群^reset;
436	^cyan;太陽光発電塔^reset;
437	^cyan;高性能^reset;バッテリー
438	小麦粉と、砂糖を入れたボウルだな。
439	パン職人が少なくとも一日は商売を続けられそうな量の小麦粉だ。
440	っさっさ、っさっさ……。
442	エイペックスの音楽プレーヤー
443	ハイロトルの音楽プレーヤー
444	^orange;スーパーペット^reset;
445	^orange;ロアウォーカーの店^reset;
446	ヴィナのぬいぐるみ
447	^orange;シレーンの鉱物店^reset;
448	^orange;マンチーズの土^reset;
449	エイペックスの中型砲の装飾
450	エイペックスの足場 部品1
451	エイペックスの足場 部品2
452	エイペックスの縁飾り
453	エイペックスの装飾足場
454	アヴィアンの完全な宝石
455	アヴィアンの宝石の上部
456	^red;旧式^reset; 極小の船舶ブースター
457	ノヴァキッド船員用二段ベッド
458	エイペックス船員用壁掛けベッド
459	ノヴァキッド船員用壁掛けベッド
460	^yellow;船員契約書^reset;
461	FU自由建造船の能力値初期化装置
462	科学用S.A.I.L
463	^cyan;船舶エンジン^reset;
464	^yellow;船員契約書（極小）^reset;
465	^yellow;船員契約書（極小・不可視）^reset;
466	キルホスのテレポーター
467	マンティジの巨像
468	エイペックス船用二段ベッド
469	^orange;スカスの文書ビーコン^reset;
470	^orange;スカスの素朴な鍛冶炉^reset;
471	^orange;スカスのプラズマ鍛冶炉^reset;
472	^orange;スカスの素朴な作業台^reset;
473	^yellow;入居契約書（極小）^reset;
474	^yellow;入居契約書（極小・不可視）^reset;
475	原生林テラフォーマー
476	アトロポステラフォーマー
477	灼熱地獄テラフォーマー
478	半影テラフォーマー
479	プロトテラフォーマー
480	タブラ・ラサテラフォーマー
481	テルシアンのキチン質本棚
482	ウサギのぬいぐるみ
483	トリクシーのぬいぐるみ
484	ケチャップとマスタード
485	アジサイのあずまや
486	^blue;ジョジャ^reset;の箱
487	^blue;ジョジャ^reset;コーラの広告板
488	^blue;ジョジャ^reset;の看板
489	四角、四っ角、四角いソファ。
490	引き出しが二つ付いた戸棚だ。
491	ただの、ちっこい古時計さ。
492	アヴォライト結晶の二倍の明るさで輝く照明だ。
493	ああいう壺には、触らねえのが一番だ。
494	この水晶をぶっ壊したくて、たまらなくなってきたぜ。
495	爪とぎポール
496	一時間も座って授業を聞いてると、落ち着かなくなるんだ。
497	一つの殻にナットミッジは何匹入るのだろう。
498	錆びた案内看板
499	高機能ANDゲート（2入力・保持なし）
500	高機能ANDゲート（2入力）
501	高機能ANDゲート（3入力）
502	小型の壁スイッチ、状態保持スイッチ、NOTゲートを一つにまとめた装置！
503	この装置は、狭い範囲の重力を十倍にするらしい。
504	NORゲート（3入力）
505	NXORゲート（3入力・1～2入力オン）
506	NXORゲート（3入力・1入力オン）
507	NXORゲート（3入力・2入力オン）
508	XORゲート（3入力）
509	XORゲート（3入力・1～2入力オン）
510	XORゲート（3入力・1入力オン）
511	XORゲート（3入力・2入力オン）
512	星いっぱいの丸椅子！
513	書類を整理するための戸棚だな。
514	ウォーボット［ボス］
515	^green;レテイア艦隊、攻略完了！
516	^green;レテイア研究所
517	またまた、とびきりヤバい場所だ。もう勝手はわかってるだろ。
518	^green;^orange;闇のエルキウス結晶^reset;を^orange;闇のエルキウス採掘施設^reset;から回収する
519	羽ばたきジャンプ I
520	二段ジャンプを、さらに二倍にする方法を思いついたんだ！
525	捕獲ロボット
526	ティクナスート
527	ペグラシ
528	ヴェルーイッシュ
529	防御力＋
530	ジュークスの硬化
531	デジャヴュ
532	ハチ刺され無効
533	極高温防護
534	重力雨無効
535	激しい寒波（耐性：^#77f4ff;氷^reset;）
536	ガス無効
537	毒の雲
538	蛾の羽ばたき
539	激怒+100%
540	激怒+20%
541	激怒+30%
542	激怒+40%
543	激怒+50%
544	激怒+60%
545	激怒+75%
546	軽度再生 II
547	回避 III
548	位相スプリント III
549	瞬間ダッシュ II
550	^#77acc3;空中ダッシュ II^reset;
551	^#77acc3;装甲球体^reset;
552	^#77acc3;空中瞬間移動^reset;
553	^#77acc3;回避^reset;
554	^#77acc3;槍突進^reset;
555	^#77acc3;再生フィールド^reset;
556	^#77acc3;奇妙な球体^reset;
557	^#77acc3;羽ばたきジャンプ III^reset;
558	^#77acc3;音速バースト^reset;
559	^#77acc3;瞬間ダッシュ II^reset;
560	シアンの放射球根
561	^white;メイン^reset;
562	^white;サブ^reset;
563	カダヴァンの作物
564	更新履歴'''

RETAINED = {
    24: 'Fictional Elder-language incantation; no English meaning supplied by FU.',
    25: 'Fictional Elder-language incantation; no English meaning supplied by FU.',
    26: 'Fictional Elder-language incantation; no English meaning supplied by FU.',
    27: 'Fictional Elder-language incantation; no English meaning supplied by FU.',
    28: 'Fictional Elder-language incantation; no English meaning supplied by FU.',
    29: 'Fictional Elder-language incantation; no English meaning supplied by FU.',
    67: 'Fictional Elder-language merchant dialogue; preserve in-world language.',
    68: 'Fictional Elder-language merchant dialogue; preserve in-world language.',
    69: 'Fictional Elder-language merchant dialogue; preserve in-world language.',
    70: 'Fictional Elder-language merchant dialogue; preserve in-world language.',
    71: 'Fictional Elder-language merchant dialogue; preserve in-world language.',
    109: 'Runtime replacement token %stardate%; must not be translated.',
    116: 'Fictional Shadow-language shop name; no English words or supplied meaning.',
    366: 'Fictional Thelusian chirping; preserve in-world utterance.',
    367: 'Fictional Thelusian chirping with color markup; preserve in-world utterance.',
    430: 'Ritual utterance in a fictional language; preserve the incantation itself.',
    441: 'Fictional Thelusian utterance; no supplied English meaning.',
    521: 'Fictional Elder-language ritual utterance; preserve original incantation.',
    522: 'Fictional Elder-language ritual utterance; preserve original incantation.',
    523: 'Fictional Elder-language ritual utterance; preserve original incantation.',
    524: 'Fictional Elder-language ritual utterance; preserve original incantation.',
}


def build():
    rows = json.loads(BASELINE.read_text(encoding='utf-8'))
    sources = list(dict.fromkeys(r['source'] for r in rows))
    targets = {}
    for line in REVIEWED.splitlines():
        number, value = line.split('\t', 1)
        number = int(number)
        if number in targets:
            raise ValueError(f'Duplicate reviewed entry {number}')
        targets[number] = value.replace(r'\n', '\n')
    if set(targets) & set(RETAINED):
        raise ValueError('An entry cannot be both translated and intentionally retained')
    if set(targets) | set(RETAINED) != set(range(len(sources))):
        raise ValueError('The baseline has unreviewed entries')
    mapping = {sources[i]: targets[i] for i in sorted(targets)}
    # Force deliberate retention even if another input later supplies a spurious MT.
    for i in RETAINED:
        mapping[sources[i]] = sources[i]
    path = PROJECT / 'source/manual_remaining.json'
    path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    decisions = []
    for i, reason in RETAINED.items():
        source = sources[i]
        matches = [r for r in rows if r['source'] == source]
        decisions.append({'source': source, 'reason': reason,
                          'fields': [{k:r[k] for k in ('id','asset','path')} for r in matches]})
    report = {
        'baseline_version': '0.1.1', 'baseline_display_fields': len(rows),
        'baseline_unique_sources': len(sources),
        'individually_translated_unique_sources': len(targets),
        'individually_translated_fields': sum(r['source'] in {sources[i] for i in targets} for r in rows),
        'intentionally_retained_unique_sources': len(RETAINED),
        'intentionally_retained_fields': sum(len(d['fields']) for d in decisions),
        'retained_decisions': decisions,
        'prose_angle_bracket_exceptions': [sources[30], sources[47]],
        'reviewer': 'ChatGPT; individual source/field comparison, not a human-translator certification',
        'scope': 'The 0.1.1 retained-field inventory only; not a whole-mod semantic proof.'
    }
    (PROJECT / 'reports/remaining_review.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in {'retained_decisions','prose_angle_bracket_exceptions'}},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    build()
