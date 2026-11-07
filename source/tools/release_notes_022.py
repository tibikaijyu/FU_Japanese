"""Release notes for the guide/race display and upgrade repair."""
import json
from pathlib import Path


def make_readme(project, version, coverage, validation):
    project=Path(project)
    guide=json.loads((project/'reports/guide_022_manifest.json').read_text())
    audit=json.loads((project/'reports/final_residual_decisions.json').read_text())
    return f'''# Frackin' Universe 日本語化MOD {version}

FU 6.5.8向けの非公式日本語化MODです。機械翻訳を基礎に、表示文を個別に補完しています。日本語を表示できるフォントが必要です。

## 今回の修正

### FUガイド

- 基本・各種システム・戦闘・電力・アイテムネットワークなど、**{guide['guide_count']}冊・{guide['guide_display_fields']}表示項目**を対象に、コーデックス画面の表示時にも日本語化を補完します。
- 基本ガイド本文184行を原文と照合して訳し直し、ガイド名、導線、用語、URL、カテゴリ表示などを修正しました。
- 元の文章にLF・CRLF・インデント等の差があっても、文字・数値・句読点・タグが既知の原文に一致する場合に翻訳します。元の文章が更新されて内容が変わった場合は、新しい文章を保持します。

### 種族情報

- 種族情報画面の表示時にも、既知の種族と表示文章を照合して日本語化します。
- 標準種族・FU主要種族の説明を見直し、食性、耐性、落下ダメージなどの用語、種族名、キャラクター作成ラベルを修正しました。
- 種族説明のJSONパッチにも、元ファイルの実改行から作った照合候補を追加しました。元素記号 `Ne` は、そのまま元素記号として表示します。

### キャラクター作成画面でのクラッシュ

利用者のログには、女性の名前生成で次の致命的例外が記録されていました。

```text
(NameGeneratorException) Unknown name source 'エルドゥカー・メス'
```

`elduukharfemale` は表示文ではなく、名前生成用データの参照IDです。0.2.0はこのIDと男性側のIDを誤って翻訳していました。0.2.1では問題ファイルを除去しましたが、旧フォルダに上書きする更新では、除去したファイルが残ります。

今回のZIPには、問題の男女2ファイルを**同名の空パッチ**として入れています。正しいフォルダへ上書きすれば古い内容が置き換わり、FU本来の参照IDを使います。名前の候補文114件の日本語化は保持しています。

ログだけでは実際の導入版や旧ファイルが残った経緯は確定できません。上書き更新とフォルダ交換の両方に対応するための修正です。

## 導入・更新

1. Starboundを完全に終了します。
2. このZIPを展開します。
3. 既存の `Starbound/mods/FU_Japanese` フォルダをmodsの外へ移動します。
4. ZIP内の `mods/FU_Japanese` を、ゲームの `Starbound/mods` へコピーします。
5. 起動後、トライコーダーの本アイコンからFUガイドを開き、種族情報も確認します。キャラクター作成画面では男女の名前生成も確認してください。

正しい配置は `Starbound/mods/FU_Japanese/_metadata` です。外側の `FU_Japanese_{version}` フォルダやZIP自体をmodsへ入れないでください。同じ `FU_Japanese` フォルダへの上書きにも対応しますが、別名の旧MODフォルダが残っている場合はmodsの外へ移動してください。

FU本体、セーブデータ、現在使用中の日本語フォントはそのまま使用できます。日本語が四角になる場合だけ、`optional/FU_Japanese_Font` を追加してください。導入だけならPythonや翻訳モデル、pak化は不要です。`source` は開発・検証用なのでゲームのmodsへ入れる必要はありません。

## 翻訳範囲

通常のJSON表示は **{coverage['catalog_entries']:,}項目中{coverage['translated_entries']:,}項目**を日本語へ変更します。配列追加、Lua、埋め込みJSONは別枠です。既存の研究、クエスト、通信、アイテム、Pandora会話等の翻訳を引き継いでいます。

抽出済みカタログは合計 **{audit['all_catalog_fields']:,}項目**です。これはFU全画面の実機確認や、すべての機械翻訳の意味が完全であることを示しません。固有名、化学式、架空言語、置換変数等を意図的に保持する箇所があります。別MODが独自に追加した文章や、原作の装飾画像に描かれた文字も、すべてを対象にはしていません。

## 検証範囲と未確認の点

今回の検査には、実際のLua関数を使ったコーデックスのカテゴリ選択・ページ送り、種族情報の表示処理、原文のLF/CRLF混在、既存の日本語や未知の文章の保持、ID・数値の不変確認、0.2.0/0.2.1への上書き更新検査を含みます。完成ZIPは全ファイルのチェックサムを検査しています。

**この作業環境ではStarbound本体を起動して画面を確認していません。** Luaの検査ではStarbound APIを模擬しています。ゲーム上での起動・表示確認とは区別してください。

ガイドと種族説明には以前の版にも翻訳データがありました。元ファイルの改行と、旧抽出処理が正規化した改行に差があることは確認しましたが、利用者のPAK内で実際にどの照合が外れたかは未確定です。今回の表示補完は、そのような書式差に対応する処理です。

表示処理を読み込むと、ログに各画面につき次の行が1回記録されます。

```text
[FU Japanese 0.2.2] Guide display helper active
[FU Japanese 0.2.2] Species display helper active
```

再度落ちる場合や英語が残る場合は、最新版でその画面を開いた直後の `Starbound/storage/starbound.log` と、英語が残っている画面の画像があると確認できます。

## 再生成・開発資料

`source/source` に翻訳カタログと今回のフィールド別変更、`source/compat/followup_022` に検証済みの表示処理、`source/tests/followup_022` に小さな固定元データと回帰検査を収録しています。今回の表示用ファイルは、既存版と出力版のSHA-256を照合してビルドの最後に適用します。対象ファイルが別の内容へ変更されていた場合は、無条件に上書きせずビルドを停止します。

`source` フォルダからの再生成例:

```sh
python -m venv .venv
.venv/bin/pip install -r requirements-build.txt
.venv/bin/python tools/build.py --project . --upstream /path/to/FrackinUniverse --machine machine_translation/machine_translations.json --output build/FU_Japanese
.venv/bin/python tools/validate.py --project . --upstream /path/to/FrackinUniverse --mod build/FU_Japanese
```

WindowsではPythonのパスを `.venv/Scripts/python.exe` に読み替えてください。Luaの構文・動作検査にはLua共有ライブラリが必要です。モデル本体やFU本体は同梱していません。

## 対応元・ライセンス

- FUメタデータ版: 6.5.8。
- 基準ソース: `17868d86c9bb7bc00f92038fb78b48cebd1b41b8`。
- ガイド比較元の公式タグ6.5.8: `329e714b3fe87571055c8ad7aa38135d199d3317`。
- 原作: SayterおよびFrackin' Universeの貢献者。原作・翻訳・改変部分はCC BY 4.0。出典とライセンス本文を同梱しています。
- 公式ソース: https://github.com/sayterdarkwynd/FrackinUniverse
- 公式Steam: https://steamcommunity.com/sharedfiles/filedetails/?id=729480149
- 機械翻訳の基礎: FuguMT（S-Taka）、CTranslate2変換（jkawamoto）。モデル重みは含めていません。
- 任意フォント: PixelMplus（itouhiro / M+ FONTS PROJECT）。M+ FONT LICENSEを同梱しています。

本MODはFU原作者・Chucklefishによる制作・承認を受けたものではありません。
'''


def make_install(version):
    return f'''Frackin' Universe 日本語化MOD {version}

1. Starboundを完全に終了します。
2. ZIPを展開します。
3. 既存の Starbound/mods/FU_Japanese をmodsの外へ移動します。
4. 新しい mods/FU_Japanese を Starbound/mods へコピーします。
5. FUガイド、種族情報、キャラクター作成時の男女の名前生成を確認します。

正しい配置: Starbound/mods/FU_Japanese/_metadata
同じフォルダへの上書き更新にも対応するため、旧版で問題だった男女2ファイルを同名の空パッチで置き換えます。
別名の旧版フォルダをmods内に残さないでください。
FU本体・セーブデータ・既存の日本語フォントはそのまま使用できます。
日本語が四角になる場合だけ optional/FU_Japanese_Font を追加してください。
source は開発資料です。ゲームのmodsにコピーする必要はありません。

データ適用、Lua表示処理、上書き更新を検査しています。
この作業環境ではStarbound本体を起動していません。
詳しい修正内容・検証範囲・ライセンスは README_JA.md を参照してください。
'''
