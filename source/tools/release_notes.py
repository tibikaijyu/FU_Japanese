"""Generate the Japanese installation and coverage notes from final reports."""
import json
from pathlib import Path


def read_report(project, name):
    path = Path(project)/'reports'/name
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def make_readme(project, version, coverage, validation):
    if version=='0.2.3':
        from release_notes_023 import make_readme as current_readme
        return current_readme(project, version, coverage, validation)
    if version=='0.2.2':
        from release_notes_022 import make_readme as current_readme
        return current_readme(project, version, coverage, validation)
    project=Path(project)
    audit=read_report(project,'final_residual_decisions.json')
    lua=read_report(project,'lua_validation.json')
    ui=read_report(project,'ui_image_label_coverage.json')
    append=coverage['append_coverage']
    embedded=coverage['embedded_coverage']
    baseline=read_report(project,'v0.1.1_baseline_coverage.json')
    lua_tests=read_report(project,'lua_behavior_tests.json')
    sbvn=json.loads((project/'compat/sbvn_compatibility_report.json').read_text(encoding='utf-8'))
    npc=json.loads((project/'compat/npc_status_test_report.json').read_text(encoding='utf-8'))
    old_typer=json.loads((project/'compat/compatibility_test_report.json').read_text(encoding='utf-8'))
    assertions=sum(r.get('assertions',0) for r in (lua_tests,sbvn,npc,old_typer))
    names={
        'items':'アイテム・設備・ブロック','dialogue':'NPC会話','research':'研究',
        'quests':'クエスト','radio':'通信メッセージ','interface':'画面・ボタン',
        'worlds':'惑星・環境','status':'状態・効果','codex':'書籍・コーデックス',
        'abilities':'武器能力','species':'種族','missions':'ミッション',
        'crew':'クルー','cinematic':'演出中の文章','visual_novel':'Pandora系会話・図鑑',
        'monsters':'モンスター名・説明','combat_text':'戦闘中の文字表示',
        'generated_names':'自動生成名の単語・名前断片','information':'お知らせ・更新履歴',
        'dungeon_text':'ダンジョン内の文章',
    }
    table='\n'.join(f"| {names.get(k,k)} | {v['translated']:,} / {v['extracted']:,} |" for k,v in coverage['categories'].items())
    hotfix=read_report(project,'hotfix_0.2.1.json') if version=='0.2.1' else {}
    fix_intro=''
    feature_heading=f'{version}で追加した内容'
    runtime_note='下記のデータ適用検査と実Lua関数の実行検査を行っています。'
    verification=f'''- JSONパッチ **{validation['patch_files_parsed']:,}ファイル**を検査しました。
- 元データを取得できたFUアセット **{validation['known_full_assets_verified']:,}個**へ適用して変更内容を検査しました。
- Luaと互換処理の実行検査は **{assertions:,}回のアサーション**を通過しています。
- 起動設定、任意フォントの設定、完成ZIPの整合性を検査しました。'''
    if hotfix:
        fix_intro='''## 0.2.1の起動不具合修正

0.2.0でタイトル画面に進む前に終了する不具合を修正しました。利用者のログには次の致命的例外が記録されていました。

```text
(NameGeneratorException) Unknown name source 'エル・デュカ・マール'
```

名前生成の `source` は名前候補を指定する内部IDですが、0.2.0では `elduukharmale` を誤って日本語へ変更していました。女性側の `elduukharfemale` にも同じ誤りがありました。問題の2パッチを取り除き、FU本来の参照名を使用します。候補の日本語テキスト114件を含め、他の翻訳内容は保持しています。

抽出・ビルド・検証処理にも、名前生成の内部IDと制御設定を翻訳しない検査を追加しました。通常JSONの件数は、誤って表示文に数えていた2件を除き、69,039件中68,977件の翻訳に訂正しています。

**旧フォルダに上書きコピーするだけでは、削除対象の古い2ファイルが残ります。以下の手順でフォルダごと交換してください。**

'''
        feature_heading='0.2.0から引き継ぐ日本語化'
        runtime_note='今回は名前生成の参照解決検査と、変更範囲の全ファイル比較を行いました。変更のないLuaの前回検査記録は参考として保持しています。'
        verification=f'''- 公式FUの固定した男女の名前生成データと候補データを使い、旧版では参照解決が失敗し、修正版では両方とも登録名へ解決することを確認しました。
- 名前候補 **114件**の日本語化と、候補数・生成設定が保持されることを確認しました。
- 名前生成に関する回帰検査 **{hotfix.get('regression_tests_passed',0)}件**が成功しました。内部ID・制御オブジェクトの書き換え、不適切な照合条件も拒否します。
- 全JSONパッチ **{validation['patch_files_parsed']:,}ファイル**を解析し、名前生成に関する変更操作を独立して検査しました。
- 配布済み0.2.0とのSHA-256比較で、問題の2ファイルの除去とバージョン表記以外、実MODの **{hotfix.get('preserved_main_mod_files',0):,}ファイル**が完全に同一であることを確認しました。任意フォントも同一です。
- 全FUアセットへの適用試験や、変更のないLuaの実行試験は今回再実行していません。0.2.0の記録は `source/reports/history/v0.2.0` に保存しています。旧検査は内部IDの誤翻訳を見逃していたため、旧版の「検査成功」を起動成功の根拠にはできません。
- 検査範囲・制限は `source/reports/hotfix_0.2.1.json`、`validation.json`、`namegen_regression.json` に記載しています。Starbound本体の起動、Markov方式での最終的な名前生成、実画面の表示はこの作業環境では確認していません。'''
    return f'''# Frackin' Universe 日本語化MOD {version}

**FU 6.5.8向けの非公式日本語化MODです。** 機械翻訳を基礎に、表示用の文章・用語をChatGPTで個別に補完しています。日本語を表示できるフォントが必要です。

{fix_intro}\
## 既存版から更新する

1. Starboundを終了します。
2. このZIPを展開します。
3. 既存の `Starbound/mods/FU_Japanese` フォルダを、いったんmodsの外へ移動します。
4. ZIP内の新しい `mods/FU_Japanese` フォルダを、ゲームの `Starbound/mods` にコピーします。
5. ゲームを起動し、まずタイトル画面まで進めることを確認します。その後、研究画面・通信・名前入力などの表示を確認します。

既存の日本語フォント、FU本体、セーブデータはそのまま使用できます。

正しい配置は `Starbound/mods/FU_Japanese/_metadata` です。ZIPそのものや、一番外側の `FU_Japanese_{version}` フォルダをmodsへ入れる形では読み込まれません。古い版を別名でmods内に残すと二重読み込みになるため、バックアップはmodsの外に置いてください。

Steam版のゲームフォルダは、ライブラリでStarboundを右クリック → 管理 → ローカルファイルを閲覧、で開けます。

日本語が四角になる場合だけ、`optional/FU_Japanese_Font` もゲームのmodsへコピーしてください。導入するだけならPython、翻訳モデル、`.pak`化は不要です。`source` は編集・検証用であり、ゲームのmodsへ入れる必要はありません。

## {feature_heading}

- 通常のJSON表示箇所を **{baseline.get('catalog_entries',0):,} → {coverage['catalog_entries']:,}か所**へ拡張しました。
- 従来英語のままだった短い名称、ボタン、効果説明、英語が混在する説明文を補完しました。
- モンスター名、武器・星系などの生成名、戦闘中の文字、船・ペット・ルートボックスの画面を追加しました。
- Pandora系の会話・図鑑 **{coverage['categories'].get('visual_novel',{}).get('translated',0):,}か所**を翻訳し、日本語の一文字表示を修正しました。
- Luaスクリプト内の表示 **{lua.get('translated_literals',0):,}か所**を翻訳しました。電力、栽培、養蜂、燃料、装備、コロニー、研究・クエスト等の動的表示を含みます。
- 通常のJSONパッチでは配列位置が分からなかった追加文に対応しました。NPCの追加状態文 **{append['npc_status_values']:,}種類**は、表示直前に原文と照合して翻訳します。
- Tiledマップ内に埋め込まれた説明 **{embedded['translated_fields']:,}か所**を翻訳しました。
- 画像内の英字ボタン等に、日本語の文字表示 **{ui.get('japanese_static_labels',0)}個**と動的タイトルを追加しました。画像ファイル自体を編集せず、操作IDと既存の操作位置を維持しています。
- 一部の長い外部作品の引用は、新たに作成した日本語のステーション会話 **{coverage.get('authored_dialogue_adaptations',0)}件**へ置き換えました。引用の全文訳ではありません。

## 起動確認について

**0.1.1は、利用者から「起動でき、日本語化されている」との確認を受けています。** 今回もその起動設定を引き継いでいます。内部名は `FUJapaneseTranslation2026`、FUの後に読み込む指定は `includes: ["FrackinUniverse"]` で、必須依存 `requires` は空です。

以前の0.1.0で発生した `missing dependency 'FrackinUniverse'` を再び必須依存として追加することはしていません。任意フォントも単独で読み込めます。

**新しい{version}をこの作業環境でStarbound本体に導入して起動・画面確認したわけではありません。** {runtime_note} 文字の折り返し、画面からのはみ出し、他MODとの組み合わせは実際のゲーム画面での確認が必要です。

## 翻訳範囲と件数

通常のJSON表示 **{coverage['catalog_entries']:,}か所中 {coverage['translated_entries']:,}か所**を日本語へ変更します。次の表には、Luaや配列追加、埋め込みJSONの件数を混ぜていません。

| 分野 | 日本語へ変更 / 抽出した表示箇所 |
| --- | ---: |
{table}

別枠で、配列追加は **{append['translated_entries']:,} / {append['catalog_entries']:,}か所**、埋め込みJSONは **{embedded['translated_fields']:,} / {embedded['catalog_entries']:,}か所**、Lua文字列は **{lua.get('translated_literals',0):,} / {lua.get('selected_literals',0):,}か所**です。配列の原文を探すために同じ翻訳条件を複数の位置へ配置しますが、その数を翻訳件数として水増ししていません。

最終の抽出済みカタログは **{audit.get('all_catalog_fields',0):,}表示箇所**です。検査時点で、翻訳データの欠落 **{audit.get('missing_translation_fields',0)}件**、理由を分類できていない全文英語表示 **{audit.get('unclassified_whole_fields',0)}件**、タグ・数値等の構造エラー **{audit.get('structural_errors',0)}件**です。

保持・記号化する **{audit.get('whole_fields_preserved_with_decision',0)}か所**には理由を付けています。架空言語の呪文・鳴き声、恒星の記号、化学式、置換用の変数、内部選択名などは原文を保持し、ページ数の区切り1か所は「/」へ変更します。HP・DPS・EPP・キー名・URLや作品・開発者の名称が、日本語の文中に残る場合もあります。

この検査は、**抽出した表示範囲の翻訳データが揃ったこと**を示します。FU全画面の実機確認や、すべての機械翻訳の意味・自然さが完全であることを示すものではありません。装飾として描かれた世界内の看板、原作ロゴ、別MODの追加文章等は全件の対象にしていません。詳細は `source/reports/final_residual_decisions.json` と各分野の監査記録を参照してください。

通常JSONの重複を除く原文の内訳は、全文の個別補完 **{coverage['methods_unique_sources'].get('manual',0):,}件**、用語表 **{coverage['methods_unique_sources'].get('glossary',0):,}件**、機械訳の用語補完 **{coverage['methods_unique_sources'].get('machine_terminology',0):,}件**、一部の文節を修正した原文 **{coverage['methods_unique_sources'].get('machine_repaired',0):,}件**、その他は機械訳です。個別補完はChatGPTによるもので、専門翻訳者の校閲という意味ではありません。

## 検証したこと

{verification}

## 反映と互換性

既に生成・保存されたアイテム名、クエスト文、NPC名、星系名等には、セーブ側の文章が残ることがあります。新しく取得・生成されたものから反映される場合があります。保存済みのペット状態など、一部は表示時に補完します。

一般の翻訳パッチは、元の文章が一致した箇所だけを変更します。FUが文章を更新した場合や、別のMODが先に同じ文章を変更した場合は、その箇所を上書きしないため英語が残ることがあります。配列の追加順序を大きく変更する別MODも、翻訳対象の位置へ影響します。

Luaファイルの差し替えは、下記のFU基準ソースに対して作成・検査しています。同じLuaを変更するMODや、今後その処理が変わったFUと併用する場合は再確認が必要です。ゲーム全体の日本語化MODと併用できますが、同じFU文章を翻訳するMODの重複は避けてください。

このZIPはFU本体を含みません。FUの追加内容を翻訳するには、FU本体が読み込まれている必要があります。

## 通信欄とフォント

左下の通信欄の文字サイズ設定（7）は変更していません。既に表示できている日本語フォントをそのまま利用できます。

任意のPixelMplus10 Regularは漢字・かなを含みますが、Starbound独自の私用文字や古代文字のすべてには対応しません。既存フォントでそれらも表示できている場合は、既存フォントを使ってください。任意フォントだけを削除する場合も、ゲームを終了してから操作してください。

## 編集・再生成

`source/source` に元文・訳文、`source/tools` にビルド処理、`source/compat` に互換処理と検査、`source/reports` に監査結果を同梱しました。辞書の個別修正は `manual_*.json` へ、用語のみの部分修正は `partial_*.json` へ記録します。Luaは `lua_translations.json` と選択マニフェストを使います。

`source` フォルダでの再生成例:

```sh
python -m venv .venv
.venv/bin/pip install -r requirements-build.txt
.venv/bin/python tools/build.py --project . --upstream /path/to/FrackinUniverse --machine machine_translation/machine_translations.json --output build/FU_Japanese
.venv/bin/python tools/validate.py --project . --upstream /path/to/FrackinUniverse --mod build/FU_Japanese
```

ビルド処理はLua表示の生成も行います。構文検査にはLua 5.3または5.4の共有ライブラリが必要です。WindowsではPython/Pipのパスを `.venv\\Scripts\\python.exe` 等に読み替えてください。モデルを再実行せず、同梱の訳文でビルドできます。モデル本体は含めていません。

## 対応元とライセンス

- FUメタデータ版: **6.5.8**。
- 基準コミット: `17868d86c9bb7bc00f92038fb78b48cebd1b41b8`。
- 原作: SayterおよびFrackin' Universeの貢献者。CC BY 4.0。翻訳と改変箇所もCC BY 4.0です。元の著作権表記・出典・ライセンスを同梱しています。
- 公式ソース: https://github.com/sayterdarkwynd/FrackinUniverse/tree/17868d86c9bb7bc00f92038fb78b48cebd1b41b8
- 公式Steam: https://steamcommunity.com/sharedfiles/filedetails/?id=729480149
- 翻訳モデル: FuguMT（S-Taka） https://huggingface.co/staka/fugumt-en-ja 、CTranslate2変換（jkawamoto） https://huggingface.co/jkawamoto/fugumt-en-ja-ct2 。モデル自体はCC BY-SA 4.0で、重みはこの配布物に含めていません。
- 任意フォント: PixelMplus（itouhiro / M+ FONTS PROJECT） https://github.com/itouhiro/PixelMplus 。M+ FONT LICENSEを同梱しています。

本MODはFU原作者・Chucklefishが制作または承認したものではありません。
'''


def make_install(version):
    if version=='0.2.3':
        from release_notes_023 import make_install as current_install
        return current_install(version)
    if version=='0.2.2':
        from release_notes_022 import make_install as current_install
        return current_install(version)
    return (f"Frackin' Universe 日本語化MOD {version}\n\n"
            '1. Starboundを終了します。\n'
            '2. ZIPを展開します。\n'
            '3. 既存の Starbound/mods/FU_Japanese フォルダをmodsの外へ移動します。\n'
            '4. 新しい mods/FU_Japanese フォルダを Starbound/mods にコピーします。\n'
            '5. 起動し、タイトル画面に進めることを確認します。\n\n'
            '上書きコピーだけでは、旧版の問題ファイル2個が残ります。フォルダごと交換してください。\n'
            'FU本体・セーブデータ・既存の日本語フォントはそのまま使用できます。\n\n'
            '正しい配置: Starbound/mods/FU_Japanese/_metadata\n'
            '古い版を別名でmods内に残さず、バックアップはmodsの外に置いてください。\n'
            '日本語が四角になる場合だけ optional/FU_Japanese_Font をmodsへ追加してください。\n'
            'source は開発資料です。ゲームのmodsへコピーする必要はありません。\n\n'
            '0.1.1で利用者が起動と日本語表示を確認した設定を引き継いでいます。\n'
            f'{version}は名前生成の内部ID誤翻訳2件を取り除いた修正版です。\n'
            '参照解決・回帰検査・変更範囲を確認していますが、この作業環境で実ゲームは起動していません。\n'
            '機械訳を含む非公式版です。範囲・件数・保持理由・詳しい説明はREADME_JA.mdをご覧ください。\n')
