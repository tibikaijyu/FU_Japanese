# 種族情報・キャラクター作成画面の限定監査

対象は配布済み `FU_Japanese_0.2.2` と、公式FUコミット `17868d86c9bb7bc00f92038fb78b48cebd1b41b8` の取得済み種族・画面データです。配布ステージは変更していません。Starbound本体は実行していません。

## 結果

この範囲では、キャラクター作成・既存キャラクター選択のフリーズを起こすと確定できる欠陥は見つかりませんでした。確認済みの表示パッチを推測で削除する修正は作成していません。名前生成辞書・候補の監査と修正は別担当です。

| 対象 | 確認結果 |
| --- | --- |
| 134個の `.species.patch`、528組の置換 | 変更先は `charCreationTooltip` の題名・副題・説明、および `charGenTextLabels` の文字列のみ。種族ID・名前生成参照・性別設定・効果量は変更しない。 |
| FU本体の完全な種族アセット22個 | LF/CRLFの44ケースで実パッチを適用。表示文字以外の全データとラベル個数が不変。 |
| `charcreation.config.patch` | 21操作は表示文字の置換。代替原文を含むため、基準FUへ適用される文字列変更は20件。残る2操作は入力透過の画像と見出しの追加。 |
| 追加されたキャラクター作成用画像・見出し | 0.2.1から同一。元のウィジェット名と衝突せず、コールバックやスクリプトを含まない。 |
| 種族表示ヘルパー | `statWindow.lua` だけから読み込む。ネイティブのキャラクター作成・選択画面からは参照されていない。今回のログにも読込マーカーがない。 |
| 最新ログの `labelGender` エラー | 発生元は `japanese.pak`。公式FUの画面定義は `labelMale` / `labelFemale` であり、`labelGender` は存在しない。Extended GUIの変更を仮定しなくても、このパス不一致は説明できる。これ自体がフリーズ原因であるとは確定していない。 |

監査スクリプトのアサーション3,843回が成功しました。結果は `species_ui_audit.json`、再実行コードは `audit_species_ui.py` にあります。

## 名前欄について分かったことと限界

公式FUの `/paneLayout/name/regex` は `[a-zA-Z0-9 '-]{0,16}` です。FU Japanese 0.2.2はこの規則を変更せず、28個の非空 `species/*namegen.config.patch` で18,250件の候補文字列を非ASCII文字列へ置換しています。元から空の互換パッチ2個を含めると、名前生成パッチは30個です。

ただし、これはFU基準データの入力規則です。ユーザーの `japanese.pak` や別の修正MODによる最終値は未取得です。また、自動生成した名前にもネイティブエンジンがこの正規表現を適用するか、拒否時に再生成するかは確認できませんでした。したがって、正規表現不一致による無限ループを発見したとは主張できません。

作者公開の独立ツールSBCharCreatorも確認しました。同ツールの `randomNameButton_Click` は名前を一度生成してWinFormsのTextBoxへ代入するだけで、入力正規表現や再生成ループはありません。ゲーム本体の実装ではないため、native 1.4.4の判定に代用できません。

## Readable UI参照版

取得した `Starbound-ReadableUI-1.0.0.zip` のゲーム用ファイルは `_metadata` と `interface.config.patch` の2個だけです。パッチ内容は `minInterfaceScale=3` と `maxInterfaceScale=3` の2操作です。

キャラクター作成・選択画面、フォント、名前欄の入力規則を直接変更しません。FU Japanese 0.2.2との同名アセット重複もありません。3xで画面の収まりが変わることはあり得ますが、この設定からフリーズ原因を確定する根拠はありません。ユーザー導入物と参照版のバイト一致は未確認です。結果とZIPのSHA-256は `readable_ui_audit.json` にあります。

## Extended GUI

作者の公式Workshop説明は画面拡張を案内しています。別作者の「FU + Extended GUI Patch」が説明する修正範囲は紡績機・メック作業台・基本製作画面のタブです。この説明だけではキャラクター作成や既存キャラクター読込みのフリーズとは結び付けられません。

Extended GUI本体のPAKは取得できていないため、そのバイト単位の重複検査は未実施です。作者が案内する旧公式フォーラムのダウンロード先は、現在の閉鎖案内へ転送されました。Steamの公開メタデータAPIではMOD名とファイルサイズを確認できましたが、直接取得URLは返りませんでした。

## 出典

- FU公式キャラクター作成設定： https://github.com/sayterdarkwynd/FrackinUniverse/blob/17868d86c9bb7bc00f92038fb78b48cebd1b41b8/interface/windowconfig/charcreation.config
- FU公式追加パッチ： https://github.com/sayterdarkwynd/FrackinUniverse/blob/17868d86c9bb7bc00f92038fb78b48cebd1b41b8/interface/windowconfig/charcreation.config.patch
- Extended GUI作者説明： https://steamcommunity.com/sharedfiles/filedetails/?id=729426797
- FU + Extended GUI Patch作者説明： https://steamcommunity.com/sharedfiles/filedetails/?id=1681880007
- 独立ツールSBCharCreator： https://github.com/Kawa-oneechan/SBCharCreator/blob/master/CharCreator.cs

`playable_species_namegen_mapping.json` はFUの選択20種族の名前生成参照一覧です。FUが完全な `.species` を持つ11種族は確定し、バニラ由来の基本7種族とfenerox/shadowは完全元データが手元にないため参照値未確定として記録しています。
