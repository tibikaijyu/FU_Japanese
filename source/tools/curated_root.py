"""Reviewed startup/interface translations, pinned to catalog entry IDs."""
import json
from pathlib import Path

REVIEWED = {
    '3613d1aae62359881ce6': '捕獲ポッドの中身に応じたモンスターを出現させる。燃料はビール。消費エネルギーは約^orange;100J ^cyan;/体。^reset; ^blue;入力^reset;1: オン/オフスイッチ',
    '00b9a1b17499eee32697': '重力のある場所では、メックは地上移動形態になります。惑星上でも、^#FF1493;[UP]キーを素早く二回押す^reset;と、地上移動から飛行モードへ手動で切り替えられます。今、切り替えて先へ進んでください。',
    '2b0498db6363464d91e4': '友人のところへ行く方法が分からないんだ。デルタ・フレイヤIIへ通じる^orange;テレポーターがすべて^reset;停止しているらしく、連絡も取れない。もし行く方法を見つけたら、友人のワーグナーを探してくれないか？',
    '22a9ee91f1b8675f3c3e': '先駆者の遺跡に秘められた謎を探った。費やした時間に見合う価値のある冒険だった。',
    'a6077b28dfbf614c6e80': 'この九十年間に耳にした噂からすると、あながち嘘でもなさそうです。^green;土台^reset;に何か隠されているのかもしれませんね。',
    '165dc474a62b3e2a6395': '通常の船の背景画像が検出されました。この画像はFrackin’ Shipの背景に表示され続けます。追加種族用のFrackin’ Ship対応パッチを導入していない場合は、https://steamcommunity.com/sharedfiles/filedetails/?id=1194878261 から導入し、新しいキャラクターを作成してください。',
    '417e157ce3f5474220d3': '決定',
    'e5570bb71bb9b5b6cd67': '船を修復する',
    'df0352677ddae13a47dd': '船の修復',
    'c75ae6aecaa1cd65b0da': '^white;自由建造^reset;',
    '8a276cc492411423852d': '^white;段階的拡張^reset;',
    '20920fd8458b3d523f46': '船を作り直します。船がリセットされてしまった場合にだけ実行してください。本当に実行しますか？',
    '509650b2c260164e5f6d': '船を修理済みの状態にします。船がリセットされていない場合にだけ実行してください。本当に実行しますか？',
    '59c04c304889be285fc0': '船の修理を省略する',
    '94116f6c95959409e2c1': '修理を省略',
    'bc44daa7c1ce960814a2': '選択',
    '83f9ae40c53cf2d55204': '確定',
    'afa8a264ef39bb5afc37': 'Frackin’ Shipは自由に建造できる船です。ブロックを設置して船内を広げ、より高性能なエンジンやブースターを取り付けて性能を上げます。\n\n選択中の船: <shipName>\n選択中の船モード: <shipMode>',
    'b76dca545d916217facc': '自由建造船',
    '0eeaf14dd5fcc28e4b0b': '標準の船',
    'f35bd817d79557658165': '地球から脱出する際に船が大破しました。使用する船の種類を選んでください。\n\n自由建造船（Frackin’ Ship）:\n複数のひな型から選び、ブロックを積んで自分だけの船を作れます。新しいFTLドライブの設置が必要です。トライコーダーのクエストに従ってください。\n\n標準の船（Vanilla Ship）:\n種族ごとに用意されたStarbound標準の船です。FUの船機能の一部は利用できません。',
    'cac168728d5890295660': '船を建造しています。しばらくお待ちください。',
    '7814ec602c93ce9d3b95': '船が損傷していない場合にだけ、修理を省略してください。',
    '048f73e07e40261778e1': 'Starbound標準の船です。船舶ライセンスを獲得または購入して、通常の方法で拡張します。ブースターなど、自由建造船で利用できる機能の一部は使えません。',
    '98bc56244d0ecf513040': '^#e43774;[FR]^reset; 種族ボーナス (%%status.statusProperty("fr_enabled")%%)',
    '29bc5b0c8b01ef50748b': '^cyan;[FU]^reset; BYOS船内大気 (%%world.getProperty("fu_byos.newAtmosphereSystem")%%)',
    'df0792a162aadc8f1366': '標準のSAIL',
    '79d764ed8f5c54b644e9': '^cyan;[FU]^reset; 船内ペット設定',
    '31d3816c257058379f14': '^cyan;[FU]^reset; 船内全域の自動回収を切り替え',
    '8ada37aa1810c7d74448': '^cyan;[FU]^reset; キャラクター情報',
    'a428f76e0d99a1070f7e': '^orange;[ZB]^reset; 更新情報',
    '1d1b837f12d632452505': '^orange;[ZB]^reset; クエスト一覧',
    'bcc5aaded2c1cc9249da': '^orange;[ZB]^reset; 研究ツリー',
    'c99ec4ecc1ea94c199a6': '^orange;[ZB]^reset; 研究の再確認を予約',
    '749f90fc04f9daaf4bd0': '^orange;[ZB]^reset; カスタムSAIL情報',
    'e3199216b8bbd98914c7': '[Admin] 状態異常を解除',
    '6f2baf6b5f44e8cdb9cc': '現在、この船に登録されているクルーはあなただけです。\n\nクルーを新たに雇えば、船の運用効率を高められる可能性があります。',
    '93fae00c488be2ae14bf': '現在、利用できるミッション座標はありません。',
    '9c168fab947b9add2c5a': '現在、待機中のクルーはいません。\n\n活動中のクルーが船の収容人数を超えると、超過したクルーは待機状態になります。',
    '63c89464342dea2a6820': 'すや…すや…すや…',
    '04373e66c492078cb9ae': '> 船のスラスターは停止中です。\n> テレポートシステムは正常に動作しています。\n> ^green;現在は直下の惑星にのみ移動できます。',
    '4343e39f9347ff87c267': '> 船のスラスターは稼働中です。\n> テレポートシステムは正常に動作しています。\n> ^green;この星系内の惑星へ移動できます。',
    '070d649215d93d9609ea': '> 船のスラスターは稼働中です。\n> FTLドライブは稼働中です。\n> テレポートシステムは正常に動作しています。\n> ^green;宇宙のあらゆる場所へ移動できます。',
    '49637443dbf17909e007': '交易品',
    'a63db94da935a7a7d61f': 'メイン',
    '12670de5ff22409669a3': '未分類',
    '3a5722f97aa9f1a971fa': '^red;エラー:^reset;\nボタンが押されていないのに、対応する処理が呼び出されました。\nSteamページかDiscordで発生時の操作を報告し、もう一度ボタンを押してみてください。',
    '2453a00507f0524b4761': '下のスロットにAIチップを入れると、AIをカスタマイズできます。\n「^green;作成^reset;」ボタンを押すと、AIチップの製作メニューが開きます。',
    '9e1d0e40594952839d4d': 'エラーが発生しました。ログを添えて、SteamページかDiscordで報告してください。^green;下のエラーメッセージが緑色の場合は、その内容を確認してください。^reset;\n\n各ボタンから標準版SAILを開くこともできます。',
    '2242cc72162f6ba05380': 'S.A.I.L.へようこそ。\n\nこの画面では船の状態を確認し、^green;[残高]^reset;を表示し、^green;[ミッション]^reset;を開始し、^green;[クルー]^reset;を管理できます。^green;[その他]^reset;から便利な機能も利用できます。',
    'ddc1e75cac8f913132e6': '^red;エラー:^reset;\n「^green;Scripted Artificial Intelligence Lattice^reset;」MODが見つかりません。\nこの機能を使う場合は導入してください。',
    '0a4cbe447d36e9888ca6': 'customDataPromiseの処理に失敗しました。SAILオブジェクトの定義に互換性の問題か不具合があります。使用中の種族MODの作者に、techStationオブジェクトの定義に問題があることを知らせてください。'
}

def main():
    root=Path(__file__).resolve().parent.parent
    catalog={r['id']:r for r in map(json.loads,(root/'source/catalog.jsonl').read_text(encoding='utf-8').splitlines())}
    mapping={catalog[k]['source']:v for k,v in REVIEWED.items()}
    (root/'source/manual_root.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Reviewed root strings:',len(mapping))

if __name__=='__main__':main()
