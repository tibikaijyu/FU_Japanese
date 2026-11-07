"""Individually reviewed Japanese for FU's appended crew/status descriptions."""
import json
from pathlib import Path

STATUS = '''Accelerating their heartbeat through the power of aerobics	エアロビクスの力で心拍数を上げている
Actively avoiding social contact	積極的に人付き合いを避けている
Appears to be on many narcotics	大量の麻薬を使っているようだ
Babbling about delicious face skin	おいしい顔の皮について口走っている
Can't feel his legs	脚の感覚がない
Can't get enough of snarshing crunchy chicks	カリカリのヒナをスナーシュするのがやめられない
Cheerfully singing about murder	殺人の歌を陽気に歌っている
Compulsively checking their weapon	取りつかれたように武器を点検している
Concocting additional ways to block access to your captains chair	船長席をふさぐ新たな方法を練っている
Contemplating the futility of life	人生のむなしさを考えている
Creeping in the shadows	物陰をこっそり移動している
Debating on how to hide the body	死体の隠し方を考えている
Debating on the nature of existence	存在の本質について考えている
Desiring a bed	ベッドが欲しい
Desiring social interaction	誰かと交流したい
Does not believe in miracles, or frogs	奇跡もカエルも信じていない
Doesn't believe that planets are spheroid	惑星が丸いとは信じていない
Doesn't remember anything about you	あなたのことを何も覚えていない
Dreaming of murder	殺人の夢を見ている
Du hast mich	君は僕を……
Eavesdropping	盗み聞きしている
Farts to impress you	あなたの気を引こうとおならをする
Fearing certain death at the hands of an oven	オーブンによる避けられない死を恐れている
Fed a snake some beer	ヘビにビールを飲ませた
Feeling like everyone's too slow	みんな遅すぎると感じている
Feeling sleep deprived	寝不足を感じている
Feeling sociable	人と話したい気分
Feeling unconfortible in the current room but too lazy to leave	今の部屋は居心地が悪いが、出ていくのも面倒くさい
Feels left out from awesome times	楽しい時間に自分だけ取り残された気分
Feels like an idiot. As usual	自分がバカに思える。いつものことだ
Forgetting their name	自分の名前を忘れかけている
Getting this party started	パーティーを盛り上げ始めている
Has a fetish for waterguns	水鉄砲に妙な執着がある
Has a smile so big that you're creeped out	あなたが不気味に思うほど満面の笑みを浮かべている
Has a super hot date tonight	今夜はとびきり魅力的な相手とデートだ
Has absolutely no idea where they last relieved themselves	最後にどこで用を足したのか、まったく覚えていない
Has constant thoughts about the universe and the true purpose of tacos	宇宙とタコスの真の目的を絶えず考えている
Has horrid soul-shattering night terrors	魂が砕けそうな恐ろしい夜驚症に悩まされている
Has kissed a girl and liked it	女の子にキスして気に入った
Has lost their self-esteem	自尊心を失っている
Has no idea you are there	あなたがそこにいることに気づいていない
Has only eaten a baby one time	赤ん坊を食べたのは一度だけだ
Has reached their final form	最終形態に到達した
Has recurring nightmares about tacos	タコスの悪夢を繰り返し見ている
Has sickening hobbies	気味の悪い趣味がある
Hates virtually everything about nachos	ナチョスのほぼすべてが嫌い
Is a real go-getter	とても意欲的な行動派だ
Is brooding	ふさぎ込んでいる
Is capable of delivering pizzas	ピザの配達ができる
Is certainly not debating where to hide the body	死体の隠し場所なんて、決して考えていない
Is chugging expensive coffee	高級コーヒーをがぶ飲みしている
Is constantly thinking about new ways to eat coal	石炭の新しい食べ方をいつも考えている
Is debating purchasing prophylactics	避妊具を買うかどうか迷っている
Is farting loudly for far too long	大きなおならをいつまでも続けている
Is feelimg empty-headed	頭の中が空っぽに感じる
Is positive that they imagined you	あなたは自分の想像の産物だと確信している
Is representing for the gangstas all across the world	世界中のギャングを代表しているつもりだ
Is slowly going crazy. 1-2-3-4-5-6, switch	少しずつ正気を失っている。1-2-3-4-5-6、切り替え
Is snarshing his garflipps	自分のガーフリップをスナーシュしている
Is suffering from an intestinal parasite	腸内寄生虫に苦しんでいる
Is thinking of pushing you down some stairs	あなたを階段から突き落とそうと考えている
Is trying to hide something	何かを隠そうとしている
Is trying to pick up the pieces	なんとか立ち直ろうとしている
Is unsure of exactly what the color purple is trying to prove	紫という色がいったい何を証明したいのか分からない
Is utterly wasted	完全に泥酔している
Is wondering why you did that	なぜあなたがそんなことをしたのか考えている
Just can't stop singing The Final Countdown	『ザ・ファイナル・カウントダウン』を歌うのがやめられない
Keeping an eye out for Kevin	ケヴィンが来ないか見張っている
Kick, punch, stab. Kick, punch, stab	蹴る、殴る、刺す。蹴る、殴る、刺す
Knows the best soundtrack ever is from 'The Crow'	史上最高のサントラは『クロウ』だと思っている
Knows you can hear their thoughts and hates you for it	自分の考えが聞こえていると知って、あなたを嫌っている
Learning the secrets of the cosmos	宇宙の秘密を学んでいる
Looking for good hiding spots	よい隠れ場所を探している
Loves you unconditionally, even though you smell awful	あなたがひどく臭くても、無条件に愛している
Making haste	急いでいる
More than anything, wants to block your chair just to annoy you	あなたを困らせるため、何よりも椅子をふさぎたい
Needing sleep	睡眠が必要だ
Never wipes his butt	お尻を一度も拭かない
Nobody understands them	誰も自分のことを分かってくれない
Outperforming others	ほかの人よりよい成果を出している
Outrunning deadlines	締め切りを先回りして片づけている
Owning the night	夜を我が物にしている
Patting their lucky severed ear in a side pocket of their pants	ズボンのポケットに入れた、お守りの切り落とされた耳をなでている
Pees on the seat	便座におしっこをかける
Picking their nose	鼻をほじっている
Planning in advance	先の計画を立てている
Planning someone elses wedding	誰かの結婚式を計画している
Plots secretly to eat Vegans alive	完全菜食主義者を生きたまま食べる計画をひそかに立てている
Really needs to block your damned captains chair	何としても、あなたの忌々しい船長席をふさぎたい
Really wants to get out of here	本気でここから出ていきたい
Refuses to flush public toilets	公衆トイレの水を流そうとしない
Remotely piloting a drone into a windmill	遠隔操作でドローンを風車に突っ込ませている
Rudely gestures at you using a piece of garflipp	ガーフリップのかけらで、あなたに下品な身ぶりをしている
Running away	逃げている
Running their mouth	口からでまかせを言っている
Screaming internally	心の中で叫んでいる
Secretly videotaping your bathroom breaks	あなたがトイレへ行くところをこっそり撮影している
Secretly wishes you were homeless	あなたが住む場所を失えばいいとひそかに思っている
Shaking in their boots	恐怖で震えている
Suggestively winks at you	あなたに意味ありげなウインクをする
Thinking about your parents and the things they once shared	あなたの両親と、二人がかつて分かち合ったものを考えている
Thinking deeply about deep thoughts	深い思索について深く考えている
Thinking longingly of blocking your chair access	あなたが椅子に座れないよう邪魔したくてたまらない
Thinking of horrifying clowns	恐ろしいピエロのことを考えている
Thinking of your mother	あなたのお母さんのことを考えている
Thinks they would taste pretty good, if anyone was going to cannibalize them	誰かに食べられるなら、自分は結構おいしいはずだと思っている
Tripping over their own feet	自分の足につまずいている
Trying not to swallow their tongue	舌を飲み込まないようにしている
Under no circumstances would circumcise a Gasbag	どんなことがあってもガスバッグの包皮は切らない
Undressing you with their eyes	あなたをいやらしい目つきで見ている
Urging others on	ほかの人をせき立てている
Vacantly staring off into space	ぼんやり宙を見つめている
Wanting more intelligence	もっと賢くなりたい
Wants to be captain	船長になりたい
Wants to be famous for eating things	物を食べることで有名になりたい
Wants to be famous for knowing things	物知りとして有名になりたい
Wants to be famous for sewing things	裁縫で有名になりたい
Wants to be famous for stabbing things	物を刺すことで有名になりたい
Wants to be famous for stealing things	盗みで有名になりたい
Wants to dance with the devil in the pale moonlight	青白い月明かりの下で悪魔と踊りたい
Wants to evangelize to you about the coming of the Robot Tacos	ロボットタコスの到来について、あなたに布教したい
Wants to get a sex change	性別を変えたい
Wants to get in shape to attract mates	相手を引きつけるために体を鍛えたい
Wants to hear Rage Against the Machine	レイジ・アゲインスト・ザ・マシーンを聴きたい
Wants to kill a man just to watch him die	死ぬところを見たいというだけで人を殺したい
Wants to place a very non-transparent toaster into a bathtub	まったく透明でないトースターを浴槽に入れたい
Wants to push you down some stairs... for science, of course	あなたを階段から突き落としたい……もちろん科学のために
Wants to read from a strange and ancient text of unknown origin	出所不明の奇妙な古文書を読み上げたい
Wants to remind you that metaphysics is worth researching	形而上学にも研究する価値があるとあなたに伝えたい
Wants to see if I can make a salad using only Florans	フローランだけでサラダを作れるか試したい
Wants to sit in the dark	暗闇の中に座っていたい
Wants to steal lawn gnomes	庭に飾られたノーム人形を盗みたい
Wants to urinate in his friends beverage	友人の飲み物におしっこを入れたい
Wants you to stand by the stairs so they can protect you	あなたを守れるよう、階段のそばに立ってほしい
Watching you sleep	あなたの寝姿を見ている
Wishing they could evolve into a thumbtack	画びょうに進化できればと願っている
Won't shut up about what's on their mind	考えていることを延々としゃべり続ける
Wondering if their uniform comes in black	制服に黒色はないのかと考えている
Wondering what absolute power feels like	絶対的な権力を持つのはどんな気分か考えている
Wondering what having two anuses would be like	肛門が二つあったらどうなるか考えている
Wondering what it felt like for you to be born	あなたが生まれたとき、どんな気分だったのか考えている
Wonders if you've ever taken DMT	あなたがジメチルトリプタミンを使ったことがあるのか考えている
Wonders what your birth was like	あなたがどんなふうに生まれたのか考えている
Would love it if your ship had a toilet they could use	使えるトイレがあなたの船にあれば、と願っている
Would love to touch your back	あなたの背中に触れてみたい
Would never touch your things unless you weren't there	あなたがいないとき以外は、あなたの持ち物に決して触れない
Would rather appreciate if Kevin stopped emailing	ケヴィンがメールを送るのをやめてくれたらありがたい
Writing angsty poetry	苦悩に満ちた詩を書いている
Writing erotic stories about their fellow crew	仲間のクルーを題材に官能小説を書いている'''

OTHER = {
    'Coffee time!': 'コーヒーの時間だ！',
    'Floran ussse table. Patch ssself up.': 'フローラン、台を使う。自分の傷を治す。',
    'The best textile manipulator ever devised.': 'これまでに開発された中で最高の繊維加工装置。',
    '^orange;Fission Furnace^reset;': '^orange;核分裂炉^reset;',
    'I could make myself a mighty fine new shirt with this.': 'こいつがあれば、すこぶる上等なシャツを仕立てられそうだ。',
    'A clothing fabricator. Maybe I can start my own fashion company.': '衣類製造機だ。自分のファッション会社を始められるかもしれない。',
    '^orange;Health Center^reset;': '^orange;医療センター^reset;',
    'Machine sssew for Floran, work thread.': '機械、フローランの代わりに縫う。糸を扱う。',
    'This gives me the ability to heal and rejuvenate after incurring damage.': 'これがあれば、傷ついても治療して元気を取り戻せる。',
    'Observant. A hyper-advanced tailoring tool.': '観察。極めて高度な仕立て道具だ。',
    ' ^#b9b5b2;Health and well-being': ' ^#b9b5b2;健康と治療',
    "I can use materials I've found here to create new healing items.": '見つけた素材をここで使い、新しい回復アイテムを作れる。',
    'There is effectively nothing that this furnace cannot melt down.': 'この炉で溶かせないものは、事実上存在しない。',
    ' Health Center': ' 医療センター',
    "A chance to display one's medical ability.": '医療の腕前を発揮する機会だ。',
    ' ^#b9b5b2;Bars and ingredients': ' ^#b9b5b2;インゴットと素材',
    "It's not traditional in the least, but the clothes I can make with this will more than make up for it.": '伝統的とはほど遠いが、これで作れる衣服は、その欠点を補って余りある。',
    'A top-of-the-line medical station.': '最高級の医療設備。',
    "This table looks good for treatin' wounds.": 'こいつは傷の手当に役立ちそうだ。',
    '^orange;Clothing Fabricator^reset;': '^orange;衣類製造機^reset;',
    'A clothing fabricator. The Miniknog use these to enforce styles across the entire populace.': '衣類製造機だ。ミニノグはこれを使って、国民全員の服装を統一する。',
    'A tool for working fabrics on an industrial scale.': '布を工業規模で加工する道具だ。',
    'Inspired. Medical module activated.': '奮起。医療モジュールを起動。',
    ' Fission Furnace': ' 核分裂炉',
    'A table with a bunch of medical tools.': '医療器具がたくさん載った台だ。',
    ' ^9900ff;Clothing Fabricator^reset;': ' ^9900ff;衣類製造機^reset;',
    ' ^#dddddd;Advanced textiles and more.': ' ^#dddddd;高度な繊維加工など。',
    '^cyan;[FS]^reset; Change S.A.I.L Image': '^cyan;[FS]^reset; S.A.I.Lの画像を変更',
}

if __name__ == '__main__':
    project = Path(__file__).resolve().parents[1]
    pairs = dict(line.split('\t', 1) for line in STATUS.splitlines())
    pairs.update(OTHER)
    rows = [json.loads(line) for line in (project / 'source/append_catalog.jsonl').read_text(encoding='utf-8').splitlines()]
    status_sources = {r['source'] for r in rows if r['asset'] == 'npcs/statuses.config'}
    assert status_sources.issubset(pairs), status_sources - pairs.keys()
    (project / 'source/manual_append.json').write_text(json.dumps(pairs, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Reviewed appended sources:', len(pairs))
