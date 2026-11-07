"""Reviewed field-scoped Japanese for FU species information (v0.2.2)."""

DESCRIPTIONS = {
'c2c2a686ec2596502bac': '''高度な知性を持つ霊長類の種族。科学に精通し、どの種族よりもテックを効率よく使いこなす。

  ^orange;食性^reset;：雑食

^orange;特性^reset;：
  マターマニピュレーター：採掘範囲 +^green;1^reset;
  体力 x^green;1.08^reset;、エネルギー x^green;1.06^reset;
  ^green;耐性^reset;：冷気 +^cyan;14^reset;%、電気 +^cyan;12^reset;%、宇宙 +^cyan;7^reset;%、物理 +^cyan;4^reset;%
  ^cyan;すべてのテックの効率が向上^reset;
  ^cyan;無効^reset;：密林・泥による移動妨害

^orange;環境^reset;：
  ^green;密林・^green;原生林^reset;・^green;森林^reset;・^green;熱帯雨林^reset;・^green;雪原^reset;：防御力 x^green;1.15^reset;、体力 x^green;1.1^reset;
  ^red;砂漠^reset;・^red;赤い砂漠^reset;：防御力 x^red;0.85^reset;、体力 x^red;0.85^reset;

^orange;武器^reset;：
  なし

^red;弱点^reset;：
  最大満腹度 x^red;0.9^reset;
  ^red;耐性^reset;：炎・毒 -^red;12^reset;%、放射線 -^red;5^reset;%''',
'01f398fd487b5f4ed507': '''強い信仰を持ち、宇宙と深く調和するエイビアン。杖の扱いに優れ、非常に身軽な種族。

  ^orange;食性^reset;：雑食

^orange;特性^reset;：
  ダメージ x^green;1.05^reset;
  エネルギー x^green;1.15^reset;
  ジャンプ高度 +^green;15^reset;%、落下ダメージ x^green;0.5^reset;
  ^green;耐性^reset;：電気 +^cyan;25^reset;%
  テック：^green;エイビアンの緩降下^reset;
  無効：^green;帯電^reset;

^orange;環境^reset;：
  空中：ダメージ x^green;1.12^reset;
  弱風～中程度の風：空中での移動性能が向上
  弱風：体力 x^green;1.15^reset;、防御力 x^green;1.1^reset;
  ^red;放射線汚染地^reset;・^red;焦土^reset;・^red;潮水^reset;：防御力 x^red;0.8^reset;
^orange;武器^reset;：
  ワンド／スタッフ：ダメージ x^green;1.2^reset;、装備属性の耐性 +^green;15^reset;%
  ワンド＋短剣：宇宙弾を発射可能（^green;エネルギー/16^reset; ダメージ）
  棒術の熟練度：+^green;25^reset;%

^red;弱点^reset;：
  体力 x^red;0.85^reset;
  ^red;耐性^reset;：物理 -^red;5^reset;%、炎 -^red;15^reset;%、放射線 -^red;10^reset;%''',
'85d00efa394d6133813a': '''禁欲的で穏やかな、謎多きエルドゥーカー。職人や哲学者の道を好み、発見と悟りを追い求める。

  ^orange;食性^reset;：ほぼ何でも食べられる

^orange;特性^reset;：
  最大体力 x^green;1.05^reset;、落下ダメージ x^green;0.75^reset;
  ^green;耐性^reset;：炎・氷 +^cyan;15^reset;%、物理 +^cyan;5^reset;%、影 +^cyan;4^reset;%
  ^cyan;体力が50%になると、敵を減速させる氷雲を放出する。^reset;
  テック：^green;クリスタルブレス^reset;、^green;エルドゥーカーの飛行^reset;

^orange;環境^reset;：
  ^green;エーテルの海・水晶・クロマティック・赤い砂漠^reset;：体力 x^green;1.25^reset;、クリティカルダメージ +^green;10^reset;%
  ^green;高温^reset;の環境：防御力 x^green;1.15^reset;、体力 x^red;0.75^reset;
  ^red;低温^reset;の環境：防御力 x^red;0.85^reset;、体力 x^green;1.25^reset;

^orange;武器^reset;：
  クリスタル／ルナリ：最大体力・防御力 +^green;12^reset;%

^red;弱点^reset;：
  ^red;高い代謝^reset;：満腹度の消費速度 +^red;15^reset;%
  クリスタルブレスと飛行は^red;満腹度を多く消費^reset;する。
  ^red;耐性^reset;：毒 -^red;20^reset;%、電気 -^red;10^reset;%''',
'3ab68b1710ddc8837000': '''フェネロックスは銀河社会に加わってまだ日が浅い。技術水準はおおむね低く、狩猟採集の暮らしを離れた者はわずかだが、狩りの腕前は見事なものだ。

  ^orange;食性^reset;：肉食

^orange;特性^reset;：
  移動速度・ジャンプ +^green;12^reset;%、ダメージ x^green;1.05^reset;、カリスマ +^green;5^reset;%
  ^green;暗視^reset;
  ^green;十分に満腹なら、夜間に体力が再生する。^reset;
  ^green;耐性^reset;：電気 +^cyan;20^reset;%、宇宙 +^cyan;15^reset;%、毒・影 +^cyan;5^reset;%、炎 +^cyan;2^reset;%
  テック：^green;狩人の爪^reset;
  ^green;無効^reset;：帯電

^orange;環境^reset;：
  ^green;サバンナ^reset;：ダメージ x^green;1.15^reset;
  夜間かつ満腹時：物理耐性 +^green;15^reset;%、防御力 +^green;2^reset;
  ^red;硫黄・スライム・タールの環境^reset;：防御力 x^red;0.8^reset;

^orange;武器^reset;：
  槍の熟練度 +^green;25^reset;%
  ^green;現在の移動速度/4を近接ダメージに加算。^reset;
  ^red;槍による攻撃は満腹度を消費する。^reset;

^red;弱点^reset;：
  体力 x^red;0.9^reset;
  ^red;耐性^reset;：氷 -^red;18^reset;%、物理 -^red;15^reset;%''',
'248e4a8e00656418cbf7': '''フローランは、攻撃的な狩人として宇宙中に知られている。今も栄養の一部を日光から得ており、光を直接浴びると体力が再生する。日光がないと徐々に飢えていく。

  ^orange;食性^reset;：肉食

^orange;特性^reset;：
  体力 x^green;1.15^reset;
  ^green;耐性^reset;：精神・毒 +^cyan;20^reset;%、電気 +^cyan;15^reset;%
  日中は体力が^green;再生^reset;する。体力・満腹度が最大なら、^green;エネルギー再生^reset;も向上。

^orange;環境^reset;：
  ^green;森林系^reset;の環境：エネルギー x^green;1.15^reset;
  ^red;不毛・腐食・極寒^reset;の環境：防御力 x^red;0.8^reset;

^orange;武器^reset;：
  弓の熟練度 +^green;20^reset;%
  槍の熟練度 +^green;15^reset;%。確率で毒攻撃が発生。
  ニードラー／フローラン武器／投擲武器：クリティカル率 +^green;2^reset;%

^red;弱点^reset;：
  ^red;夜間^reset;：体力 x^red;0.9^reset;、エネルギー x^red;0.8^reset;、満腹度の消費が増加
  ^red;耐性^reset;：炎 -^red;30^reset;%、影 -^red;5^reset;%''',
'c49afa8d84d01047e884': '''アノダインはノヴァキッドに似た、謎多き「星間ガス生命体」の種族。居住地の記録も、書き残された歴史もない。気まぐれで、過去にとらわれない存在だ。何でできているのか、ましてやどこから来たのか、誰も知らない。''',
'187354f5a00f94523f3c': '''社会の中心となる巨大な方舟船で宇宙を渡り歩き、交易商として名を馳せてきた種族。経済と探検に精通した、宇宙を旅するげっ歯類だ。

  ^orange;食性^reset;：雑食

^orange;特性^reset;：
  移動速度 +^green;10^reset;%
  ^green;耐性^reset;：電気 +^cyan;15^reset;%、放射線・氷 +^cyan;10^reset;%、精神 +^cyan;7^reset;%
  優れた交易商：カリスマ +^green;25^reset;%、初期所持金 +1000
  最大満腹度 +^green;72^reset;

^orange;武器^reset;：
  信頼できるサイドアームを所持して開始
  エネルギー武器の熟練度：+^green;15^reset;%
  ストライカーの熟練度：+^green;15^reset;%

^red;弱点^reset;：
  ^red;耐性^reset;：毒 -^red;20^reset;%、炎 -^red;10^reset;%、物理 -^red;5^reset;%''',
'835d8d1f5f96f7787fa4': '''硬いキチン質の外殻を持つ、甲虫に似た二足歩行の雑食種族。にぎやかで華やかなものを好む。

  ^orange;食性^reset;：雑食

^orange;特性^reset;：
  体力 +^green;20^reset;、防御力 +^green;5^reset;、最大満腹度 x^green;1.5^reset;
  ^green;耐性^reset;：物理 +^cyan;15^reset;%、炎・毒・電気 +^cyan;10^reset;%、放射線 +^cyan;5^reset;%

^orange;環境^reset;：
  ^green;密林・砂漠・硫黄^reset;の環境：エネルギー x^green;1.1^reset;、防御力 x^green;1.1^reset;

^orange;武器^reset;：
  短槍の熟練度：+^green;25^reset;%
  弓の熟練度：+^green;5^reset;%
  盾：シールドバッシュ +^green;2^reset;%、押し出す距離 +^green;2^reset;
  パーフェクトブロックで^green;体力と^green;盾スタミナ20^reset;%を回復^reset;

^red;弱点^reset;：
  交易が苦手（カリスマ -^red;5^reset;%）
  ^red;耐性^reset;：氷 -^red;15^reset;%、宇宙 -^red;12^reset;%、影 -^red;10^reset;%''',
'7e84c3f03bafb8bbff59': '''遥かな過去に起源を持つ、謎に包まれた種族。寒冷地に暮らす、頑健な雑食の生物だ。

  ^orange;食性^reset;：雑食

^orange;特性^reset;：
  体力 x^green;1.15^reset;、エネルギー x^green;1.12^reset;
  ^green;耐性^reset;：氷 +^cyan;30^reset;%、放射線 +^cyan;5^reset;%
  ジャンプ高度 +^green;8^reset;%、落下ダメージ x^cyan;0.8^reset;
  ^cyan;無効^reset;：液体窒素・凍結・氷での滑り

^orange;環境^reset;：
  ^green;低温^reset;の環境：体力・エネルギー x^green;1.15^reset;
  ^red;高温^reset;の環境：体力・エネルギー x^red;0.8^reset;

^orange;武器^reset;：
  すべての銃：ダメージ x^green;1.1^reset;、クリティカルダメージ +^green;5^reset;%
  斧の熟練度：+^green;15^reset;%
  マシンピストルの熟練度：+^green;15^reset;%

^red;弱点^reset;：
  ^red;耐性^reset;：炎 -^red;30^reset;%''',
'c3e5f2ef6f863cc2d55e': '''入国管理の場面では、一部の役人はスライムの姿が見えていないらしい。^green;体力再生、^cyan;無効^reset;：スライム・毒状態・帯電。^reset; ^orange;^green;耐性^reset;：炎。^reset; ^red;^green;耐性^reset;：氷^reset;''',
'951229a8706f6a18129b': '''誰が彼らを造ったのかは、歴史の闇に埋もれている。素朴な暮らしを好む彼らにとって、それは問題ではない。中世風の文化のもと、盾・ハンマー・弓の鍛錬に励む。

  ^orange;食性^reset;：ロボット食／雑食

^orange;特性^reset;：
  防御力 x^green;1.06^reset;
  ^green;耐性^reset;：物理・毒・ノックバック +^cyan;20^reset;%、炎 +^cyan;14^reset;%、放射線 +^cyan;5^reset;%
  ^cyan;無効^reset;：毒状態・蜂刺され

^orange;環境^reset;：
  ^green;油・液体プロトサイト・エルキウス^reset;：体力・エネルギー再生、エネルギー x^green;1.25^reset;
  ^red;山岳^reset;の環境：防御力 x^red;0.8^reset;

^orange;武器^reset;：
  ハンマーの熟練度：+^green;25^reset;%
  弓の熟練度：+^green;10^reset;%
  片手武器（1h）の連続攻撃で防御力 +^green;2^reset;
  盾を構えている間：防御力 +^green;3^reset;
  パーフェクトブロックで^green;ダメージが増加^reset;（重複する）
  シールドバッシュで^green;体力が回復^reset;

^red;弱点^reset;：
  帯電中：攻撃力・エネルギー -^red;50^reset;%
  ^red;耐性^reset;：電気 -^red;30^reset;%''',
'2982304df329893e06bf': '''ヒューマンは万能で、ほぼどんな場所でも生き延びる恐るべき適応力を持つ。会ったことはあるだろうか？ 奇妙な連中だ。近づかないことを勧める。

  ^orange;食性^reset;：雑食

^orange;特性^reset;：
  エネルギー x^green;1.05^reset;
  ジャンプ高度 +^green;2^reset;%、最大満腹度 +^green;15^reset;%
  カリスマ +^green;10^reset;%
  ^green;耐性^reset;：電気 +^cyan;11^reset;%、炎・氷・毒・宇宙 +^cyan;10^reset;%

^orange;環境^reset;：
  なし

^orange;武器^reset;：
  弾薬の熟練度：^green;25^reset;%
  ショートソードの熟練度：^green;15^reset;%
  盾：パーフェクトブロックで^green;防御力が増加^reset;（重複する）

^red;弱点^reset;：
  ^red;耐性^reset;：放射線・影 -^red;15^reset;%''',
'ada1fd1ce44b0f2c9d77': '''平和を好むハイロトルは、先祖伝来のしきたりを重んじ、芸術に深い安らぎを見いだす。暴力を好みはしないが、武術に長けており、侮ってはいけない。

  ^orange;食性^reset;：雑食

^orange;特性^reset;：
  液体採取を解放した状態で開始。
  カリスマ：+^green;5^reset;%
  ^green;耐性^reset;：氷 +^cyan;20^reset;%、放射線 +^cyan;12^reset;%、毒 +^cyan;8^reset;%、精神 +^cyan;15^reset;%

^orange;環境^reset;：
  水中：酸素 +^green;1500^reset;、物理耐性 +^green;8^reset;%、体力 x^green;1.12^reset;
  ^cyan;水泳強化1^reset;
  ^red;砂漠^reset;・^red;赤い砂漠^reset;：防御力 x^red;0.8^reset;、体力 x^red;0.8^reset;

^orange;武器^reset;：
  剣：体力が^green;75^reset;%を超えているとき、クリティカル率 +^green;2^reset;%
  刀の熟練度：+^green;25^reset;%

^red;弱点^reset;：
  ^red;耐性^reset;：電気 -^red;20^reset;%、影 -^red;10^reset;%''',
'580b702caf056076294f': '''薄暗い世界の深部で進化したナイターは、光を強く嫌う。優秀な戦士であり、諜報活動にも長けている。

  ^orange;食性^reset;：雑食

^orange;特性^reset;：
  テック：^green;コンシャク^reset;（光のオーラ・モンスター探知・ダメージ耐性。^red;チャージ7秒^reset;）
  ^green;耐性^reset;：影 +^cyan;15^reset;%、毒 +^cyan;10^reset;%、氷 +^cyan;5^reset;%
  ^cyan;無効^reset;：毒状態

^orange;環境^reset;：
  ^green;暗闇^reset;：^green;物理耐性^reset;と^green;ダメージ^reset;が増加。攻撃に吸収効果が付く。
  ^red;光^reset;：^red;エネルギー・体力・物理耐性・ダメージ^reset;が低下。攻撃の^red;吸収効果^reset;が失われる。

^orange;武器^reset;：
  すべての剣：暗闇では^green;3^reset;%の確率でシャドウバースト（^green;5ダメージ^reset;）が発生。
  ブロードソードの熟練度：^green;25^reset;%
  ショートソードの熟練度：^green;25^reset;%
  ロングソードの熟練度：^green;25^reset;%
  盾：ノックバック耐性 +^green;25^reset;%

^red;弱点^reset;：
  ^red;耐性^reset;：宇宙 -^red;20^reset;%、電気 -^red;15^reset;%''',
'8f2c7a994d021fe96fb4': '''ノヴァキッドは「星間ガス生命体」とも呼ばれる謎の種族。知られている居住地は少なく、書き残された歴史もない。

  ^orange;食性^reset;：何でも食べられる

^orange;特性^reset;：
  暗闇で発光する
  エネルギー x^green;1.1^reset;
  ^green;耐性^reset;：放射線 +^cyan;35^reset;%、炎 +^cyan;20^reset;%
  ^cyan;無効^reset;：炎上・放射線やけど

^orange;環境^reset;：
  ^green;放射線^reset;環境：体力 x^green;1.15^reset;
  日光下：満腹なら体力が^green;再生^reset;し、エネルギー再生 +^green;20^reset;%
  夜間：体力再生が^red;満腹度を消費^reset;し、エネルギー x^red;0.75^reset;

^orange;武器^reset;：
  ピストル x 2：移動速度 +^green;8^reset;%
  ピストルの熟練度 +^green;15^reset;%
  スナイパーライフルの熟練度 +^green;15^reset;%
  ショットガンの熟練度 +^green;15^reset;%

^red;弱点^reset;：
  体力 x^red;0.9^reset;、最大満腹度 -^red;10^reset;%
  ^red;耐性^reset;：氷・影 -^red;20^reset;%、電気 -^red;5^reset;%''',
'b973d64c930839a4aebf': '''起源について諸説ある、内気な放射性生命体。^red;空腹の管理を中心に設計された^reset;種族で、^red;難度は高い^reset;。

  ^orange;食性^reset;：調理済みの同位体を含め、何でも食べられる

^orange;特性^reset;：
  体力 x^green;1.1^reset;、エネルギー x^green;1.2^reset;。^red;空腹で効果が低下^reset;。防御力 x^green;1.03^reset;
  ^green;耐性^reset;：放射線 +^green;35^reset;%、毒 +^green;10^reset;%、宇宙 +^green;5^reset;%、^green;満腹なら最大2x^reset;。精神 +^green;5^reset;%
  テック：シードバルブ
  ^cyan;無効^reset;：放射線やけど

^orange;環境^reset;：
  ^green;放射線^reset;環境：ダメージ x^green;1.15^reset;、エネルギー再生 +^green;15^reset;%、満腹度の消費 -^green;5^reset;%
  ^red;高温^reset;の環境：防御力 x^red;0.85^reset;、満腹度の消費 +^red;35^reset;%
  ^green;時間とともに防御力が上昇^reset;
  ^cyan;種族専用テックの活用が生存の鍵^reset;
  ^green;遺伝子を自動生成^reset;

^orange;武器^reset;：
  ザイ武器：クリティカル率 +^green;1.5^reset;%、防御力 x^green;1.15^reset;

^red;弱点^reset;：
  満腹度の消費 +^red;25^reset;%
  ^red;耐性^reset;：炎・氷・電気 -^red;20^reset;%、^red;空腹なら最大1.5x^reset;
  回復アイテムは^red;使用不可^reset;。種族専用の回復手段が必要。''',
'8de2427d8304299946ff': '''宇宙の謎に包まれた、つかみどころのないシャドウたち。彼らは同族との会話を好む。他の種族には、その言語を聞き取ることすらできないのだから当然だ。

  ^orange;食性^reset;：何でも食べられる

^orange;特性^reset;：
  エネルギー x^green;1.12^reset;、満腹度の消費が^green;15%^reset;減少
  ^green;耐性^reset;：影・氷 +^cyan;20^reset;%、毒 +^cyan;15^reset;%、放射線 +^cyan;10^reset;%
  ^cyan;無効^reset;：酸素不足・暗闇・影の汚染
  テック：^green;シャドウバースト^reset;

^orange;環境^reset;：
  ^green;暗い^reset;環境：クリティカル率 +^green;2^reset;、エネルギー x^green;1.15^reset;
  暗闇で発光する
  暗闇では攻撃力と防御力が上がり、光の下では低下する。
  ^red;クロマティック^reset;環境：防御力 x^red;0.8^reset;、体力 x^red;0.75^reset;

^orange;武器^reset;：
  大鎌の熟練度：+^green;25^reset;%
  スタッフ／ワンド：体力 x^green;1.25^reset;
  マグノーブ：防御力 x^green;1.25^reset;

^red;弱点^reset;：
  体力 x^red;0.85^reset;
  ^red;耐性^reset;：電気・宇宙 -^red;15^reset;%、炎 -^red;10^reset;%''',
'2d8ec58cc1ec9fac7587': '''異星勢力に侵略された過去から軍備と防衛に力を注ぎ、卓越した戦士となった種族。水棲の起源を持ち、特に水中では恐るべき戦闘力を発揮する。

  ^orange;食性^reset;：雑食

^orange;特性^reset;：
  エネルギー x^green;1.05^reset;、防御力 +^green;5^reset;、呼吸量 +^green;500^reset;
  ^green;耐性^reset;：氷 +^cyan;20^reset;%、放射線 +^cyan;10^reset;%
  ^cyan;水泳強化2^reset;

^orange;環境^reset;：
  海洋：体力 x^green;1.25^reset;、防御力 +^green;6^reset;
  高温：エネルギー x^red;0.7^reset;、体力 x^red;0.7^reset;、移動速度 x^red;0.8^reset;
  回復水・汚水・沼の水：体力再生 +^green;0.1^reset;%

^orange;武器^reset;：
  エネルギー武器の熟練度：+^green;15^reset;%
  アサルトライフルの熟練度：+^green;25^reset;%

^red;弱点^reset;：
  ^red;耐性^reset;：電気 -^red;20^reset;%''',
'6cf17f2fbe9010043ad9': '''肉食のテルシアンは、硬いキチン質の外殻と、極めて危険な戦闘能力で知られる。どんな戦況にも適応できる種族だ。

  ^orange;食性^reset;：肉食

^orange;特性^reset;：
  体力 x^green;1.25^reset;、防御力 +^green;8^reset;、落下ダメージ x^green;0.4^reset;
  ^green;耐性^reset;：精神 +^cyan;30^reset;%、物理 +^cyan;15^reset;%、放射線 +^cyan;20^reset;%
  ^cyan;無効^reset;：狂気
  テック：^green;戦士の本能^reset;

^orange;環境^reset;：
  ^green;高温^reset;の環境：体力 x^green;1.1^reset;
  地面をつかむ力が強く、滑りにくい

^orange;武器^reset;：
  大鎌の熟練度：+^green;15^reset;%
  ブロードソードの熟練度：+^green;15^reset;%
  斧の熟練度：+^green;10^reset;%
  盾：防御力 x^green;1.1^reset;
  パーフェクトブロック：^green;シールドバッシュ^reset;の発生率が上昇

^red;弱点^reset;：
  エネルギー x^red;0.75^reset;、カリスマ -^red;25^reset;%
  ^red;耐性^reset;：炎 -^red;30^reset;%、氷 -^red;15^reset;%''',
'15cde42a0b8bc037147f': '''知性を持つ猫の種族だが、価値観は大きく分かれている。半数は平和を愛する自由な思想家で、残りは戦争を求める怪物だ。

  ^orange;食性^reset;：雑食。生肉も食べられる

^orange;特性^reset;：
  体力 x^green;1.05^reset;、ダメージ x^green;1.05^reset;
  ジャンプ +^green;13^reset;%、走行速度 +^green;6^reset;%^reset;、落下ダメージ x^green;0.8^reset;
  ^green;耐性^reset;：氷 +^cyan;15^reset;%、電気 +^cyan;5^reset;%
  ^cyan;暗視^reset;
  テック：^green;鋭い爪^reset;
  ^green;無効^reset;：密林・泥による移動妨害

^orange;環境^reset;：
  ^green;密林・原生林・森林・熱帯雨林・砂漠^reset;：体力 x^green;1.1^reset;、エネルギー x^green;1.1^reset;
  ^green;不毛・硫黄・インファーナス^reset;：体力 x^red;0.8^reset;、エネルギー x^red;0.8^reset;

^orange;武器^reset;：
  拳武器の熟練度：+^green;20^reset;%
  短剣の熟練度：^green;15^reset;%
  アームキャノンの熟練度：+^green;15^reset;%

^red;弱点^reset;：
  ^red;耐性^reset;：炎・毒・放射線 -^red;10^reset;%、物理 -^red;5^reset;%''',
}

# The alternate upstream Nightar wording has the same effects and colour runs.
DESCRIPTIONS['4ac714bd5fce017f67cf'] = DESCRIPTIONS['580b702caf056076294f']

DESCRIPTIONS.update({
'17c3d596df44379f0b51': '''ヴェルーイッシュによって知性を与えられた種族。念話と念動力を持ち、文化や技術の使い方も彼らにならっている。ひどい猫の駄じゃれが大好き。

  ^orange;食性^reset;：肉食

^orange;特性^reset;：
  非常に身軽。ジャンプ +^green;20^reset;%、走行速度 +^green;8^reset;%^reset;、落下ダメージ x^green;0.2^reset;
  ^green;耐性^reset;：冷気 +^green;20^reset;%
  暗視
  テック：^green;鋭い爪^reset;
  ^cyan;無効^reset;：密林の土・泥による移動妨害

^orange;環境^reset;：
  ^green;密林・原生林・森林・熱帯雨林・砂漠^reset;：
    体力 x^green;1.1^reset;、エネルギー x^green;1.15^reset;

^orange;武器^reset;：
  拳武器・短剣・ショートソード：クリティカル率 +^green;1^reset;%
  投擲武器／手榴弾：ダメージ x^green;1.25^reset;
  マグノーブ：クリティカル率 +^green;2^reset;%
  アームキャノン：防御力・ダメージ x^green;1.15^reset;

^red;弱点^reset;：
  ^red;耐性^reset;：宇宙・電気 -^red;20^reset;%''',
'89aff3b27eabc62e90b1': '''しばしば「忌まわしきもの」と呼ばれるミフィス。非常に強い免疫機能を持ち、暗闇を好む。''',
'865b432961261d22f6ed': '''ほとんど何の達人でもないイズクは、もっぱら幸運によって発展してきた。''',
'05cca594fbd1c171a976': '''生産的で頑丈なマンティスだが、驚くほど分別に欠け、好かれにくい。''',
'da94b956e8a4488c88d3': '''なんてかわいい、ふわふわ！''',
'a1659462813aad510fab': '''超能力を持つ、珍しい極限環境生物の種族。意志の力だけで強力な精神波動を生み出せる。

  ^orange;食性^reset;：何でも食べられる（調理済みの同位体を含む）

^orange;特性^reset;：
  エネルギー x^green;1.1^reset;
  ^green;耐性^reset;：精神 +^cyan;30^reset;%、炎・電気 +^cyan;20^reset;%、宇宙・放射線 +^cyan;15^reset;%
  ^cyan;無効^reset;：炎上
  テック：^green;サイオニックウェーブ^reset;

^orange;環境^reset;：
  ^green;帯電・水晶^reset;の環境：^green;移動速度 +5%^reset;
  ^red;低温^reset;の環境：防御力 x^red;0.9^reset;

^orange;武器^reset;：
  予知能力：^cyan;8%^reset;を^green;すべて^reset;のダメージに加算
  サイオニックイジェクター：ダメージ x^green;1.2^reset;
  マグノーブの熟練度：+^green;20^reset;%

^red;弱点^reset;：
  体力 x^red;0.88^reset;
  ^red;耐性^reset;：物理 -^red;12^reset;%、毒 -^red;20^reset;%、氷 -^red;5^reset;%
  カリスマ -^red;10^reset;%''',
'096c04285c3963c3f5e8': '''冷酷で狡猾。''',
'fa2339ef8e318bfae75a': '''起源不明の異星生物。''',
'b0941c53f2a87084816d': '''かつては人間だったが、ナノトラセンの前哨基地での勤務中に変異した。''',
'c2658c0c5c560f272682': '''死者から生まれた、知性ある共生生物。自らの起源を受け入れようと苦闘する、風変わりだが頑健な種族。

  ^orange;食性^reset;：雑食

^orange;特性^reset;：
  落下ダメージ x^green;0.5^reset;
  ^green;耐性^reset;：毒 +^cyan;30^reset;%、放射線 +^cyan;10^reset;%、電気 +^cyan;4^reset;%、宇宙 +^cyan;3^reset;%
  体力再生 +^green;1^reset;%（常時）
  テック：^green;粘着ボール・壁つかまり^reset;
  ^cyan;無効^reset;：スライムの反発・粘着・毒状態・クモの巣

^orange;環境^reset;：
  ゼラチン質・湿原・沼地：体力 x^green;1.25^reset;、移動速度 +^green;15^reset;%
  低温の環境：体力 x^red;0.75^reset;
  液体スライムの中で呼吸できる

^orange;武器^reset;：
  鞭の熟練度：x^green;15^reset;%
  生体武器：ダメージ x^green;1.15^reset;、クリティカルダメージ +^green;20^reset;%^reset;

^red;弱点^reset;：
  ^red;耐性^reset;：炎・氷 -^red;20^reset;%
  満腹度の消費 +^red;25^reset;%''',
'7b177eab6cbb1d99fca5': '''見るからに危険そうなロボット。''',
})
DESCRIPTIONS['9531e392fa781d3a3b0c'] = DESCRIPTIONS['17c3d596df44379f0b51'].replace('^reset;：\n    体力', '^reset;：体力')

NAMES = {
    'Apex':'エイペックス', 'Avian':'エイビアン', 'Floran':'フローラン',
    'Glitch':'グリッチ', 'Human':'ヒューマン', 'Hylotl':'ハイロトル',
    'Novakid':'ノヴァキッド', "Eld'uukhar":'エルドゥーカー', 'Elduukhar':'エルドゥーカー',
    'Anodyne':'アノダイン', 'Fenerox':'フェネロックス', 'Kirhos':'キルホス',
    'Mantizi':'マンティジ', 'Nightar':'ナイター', 'Radien':'ラディエン',
    'Skath':'スカース', 'Thelusian':'テルシアン', "Vel'uuish":'ヴェルーイッシュ',
    'Peglaci':'ペグラシ', 'Slime':'スライム', 'Shadow':'シャドウ',
    "Tiknass'uut":'ティクナスート', 'Pharitu':'ファリトゥ', 'Izku':'イズク',
    'Myphis':'ミフィス', 'Mantis':'マンティス', 'Precursor':'先駆者',
    'spiderdroid':'スパイダードロイド', 'fuphotonpoptop':'フォトンポップトップ',
}

LABELS = {
    'ANTENNAE':'触角', 'BODY COLOR':'体の色', 'BRAND':'刻印',
    'Belly Colour':'腹の色', 'Body colour':'体の色', 'Brand':'刻印',
    'CAMOUFLAGE':'迷彩', 'CORONA':'コロナ', 'Carapace':'甲殻',
    'Core Colour':'核の色', 'Crest':'とさか', 'DARK IZKU':'ダーク・イズク',
    'DEPOSITS COLOR':'付着物の色', 'Detail':'細部', 'Detail colour':'細部の色',
    "ELD'UUKHAR":'エルドゥーカー', 'EYE COLOR':'目の色', 'Ears':'耳',
    'Eye Color':'目の色', 'Eye colour':'目の色', 'Eyes, Accessories':'目・装飾品',
    'FENEROX':'フェネロックス', 'FINS':'ひれ', 'FINS COLOR':'ひれの色',
    'Feather Colour':'羽毛の色', 'Fin Color':'ひれの色', 'Fin Colour':'ひれの色',
    'Fur Color 1':'毛の色1', 'Fur Color 2':'毛の色2', 'Fur colour':'毛の色',
    'Gem':'宝石', 'Gem colour':'宝石の色', 'HAIR COLOR':'髪の色',
    'HAIR STYLE':'髪型', 'HUMAN':'ヒューマン', 'Hair':'髪', 'Hair Colour':'髪の色',
    'Hair colour':'髪の色', 'Hair style':'髪型', 'Hide colour':'皮膚の色',
    'Horn style':'角の形', 'Horns':'角', 'IZKU':'イズク', 'KIRHOS':'キルホス',
    'Legwear':'ボトムス', 'Legwear Color':'ボトムスの色', 'Legwear Colour':'ボトムスの色',
    'Legwear colour':'ボトムスの色', 'MANDIBLES':'大顎', 'MANTIS':'マンティス',
    'MANTIZI':'マンティジ', 'Marking Colour':'模様の色', 'Marking colour':'模様の色',
    'Markings':'模様', 'NIGHTAR':'ナイター', 'NOVAKID':'ノヴァキッド',
    'PANTS':'ズボン', 'PANTS COLOR':'ズボンの色', 'PEGLACI':'ペグラシ',
    'PERSONALITY':'性格', 'PHARITU':'ファリトゥ', 'PLASMA COLOR':'プラズマの色',
    'Personality':'性格', 'Plate colour':'外板の色', 'SHELL COLOR':'殻の色',
    'SHIRT':'シャツ', 'SHIRT COLOR':'シャツの色', 'SKATH':'スカース',
    'SKIN COLOR':'肌の色', 'SLIME':'スライム', 'Scale Colour':'うろこの色',
    'Setae colour':'剛毛の色', 'Shell':'殻', 'Shirt':'シャツ',
    'Shirt Color':'シャツの色', 'Shirt Colour':'シャツの色', 'Shirt colour':'シャツの色',
    'Skin Color':'肌の色', 'Skin Colour':'肌の色', 'Skin colour':'肌の色',
    'TENEBHRAE':'テネブレイ', 'THELUSIAN':'テルシアン', "TIKNASS'UUT":'ティクナスート',
    'UNDY COLOR':'下着の色', "VEL'UUISH":'ヴェルーイッシュ',
}

CHARCREATION = {
    'Cancel':'キャンセル', 'CASUAL':'カジュアル', '^#8d8d8d;CUSTOMISE':'^#8d8d8d;外見',
    '^#8d8d8d;DIFFICULTY':'^#8d8d8d;難易度', '^#8d8d8d;FEMALE':'^#8d8d8d;女性',
    'HARDCORE':'ハードコア', '^#8d8d8d;MALE':'^#8d8d8d;男性',
    '^#8d8d8d;NAME':'^#8d8d8d;名前', 'HUMAN':'ヒューマン',
    'RANDOMISE:':'ランダム：', '^#8d8d8d;SPECIES':'^#8d8d8d;種族',
    'SURVIVAL':'サバイバル', 'Show clothing':'服を表示',
    'Skip intro mission':'導入をスキップ',
    'No need to eat and no death penalties.':'食事不要。死亡ペナルティもありません。',
    'Eat to survive, drop items on death.':'生存には食事が必要です。死亡するとアイテムを落とします。',
    'Hunger. Death: Lose 50% pixels, drop ^red;ALL^reset; items.':'空腹あり。死亡時：ピクセルを50%失い、^red;すべて^reset;のアイテムを落とします。',
    'When you die your character stays dead!':'死亡すると、そのキャラクターは復活できません！',
    'Name':'名前', 'Done':'完了',
}

STATWINDOW = {
    'Research':'研究', 'GPS':'惑星情報', 'Codex':'図鑑', 'Tech Equip':'テック装備',
    'Tech Craft':'テック製作', 'Mech Gear':'メック装備', 'Mech Fuel':'メック燃料',
    'Upgrade':'強化', 'Adv. Stats':'詳細能力', 'Immunities':'状態異常耐性',
    ' ^#bbbbbb;Accesses Stats, Research, Mechs and more.':' ^#bbbbbb;能力・研究・メックなどを確認できます。',
    ' ^#00eaff;Personal Tricorder^reset;':' ^#00eaff;携帯トライコーダー^reset;',
    ' ^#ffffff;Resistances^reset;':' ^#ffffff;属性耐性^reset;',
}

# These corrections apply only to species description fields, never globally.
DESCRIPTION_TERMS = {
    'ダイエット':'食性', 'レジスト':'耐性', '秋の被害':'落下ダメージ',
    '秋のダメージ':'落下ダメージ', '最大健康':'最大体力', '健康':'体力',
    '最大食品':'最大満腹度', '最大食糧':'最大満腹度', '弱さ':'弱点',
}
