# FU追加の通信メッセージが未翻訳になる原因と対策

調査日：2026-11-09。状態：原因確認済み・対策提案。修正実装、配布物更新、ゲームへの再配置は未実施。

利用者が報告した「Shift＋Mouse 1」の説明は、`fu_start_Complete2a` と特定できた。導入済みFUの通信データに存在するが、FU_Japaneseが基準にしたGitHubコミットでは削除されており、翻訳カタログと配布パッチに収録されていない。

根本原因は、**同じFU 6.5.8表記でも、導入済み配布物と翻訳に使ったGitHubソースの通信データが異なること**。対象ファイル26件の本文に現行パッチを適用すると、10件が英語のまま残る。内訳は翻訳項目の欠落6件、原文不一致による置換スキップ4件。

推奨対策は、対象の通信ファイルについて導入済みFUと一致する公式原文を基準にし、カタログと訳文を補完してパッチを再生成すること。以下は実装前の計画であり、適用済みではない。

## 1. 症状・確認環境

利用者報告は「FUで追加されたキャラクターが左下で話す内容が翻訳されない」。追加情報の「Shift＋Mouse 1の説明をしていた」は、`fu_start_Complete2a` の内容に一致する。

| 項目 | 確認内容 |
| --- | --- |
| ゲーム | 通常版Starbound 1.4.4、Windows x86_64。既存ログで確認 |
| FU本体 | 導入済みWorkshop item `729480149` のPAK。メタデータは6.5.8 |
| 日本語化 | FU_Japanese 0.2.3-fu6.5.8 |
| 作業開始時のHEAD | `a5ec22209c85bd60f8e702cbfab141d4dcc49c82`。変更なし |
| 対象アセット | `radiomessages/fu_quests.radiomessages` |
| 対象パッチ | `mods/FU_Japanese/radiomessages/fu_quests.radiomessages.patch` |
| 配置の確認 | 対象パッチは作業フォルダとゲーム導入先でバイト一致 |
| 再現方法 | PAKを読み取り専用で解析し、既存のパッチ検証処理で対象データを合成 |

該当する通信データにプレイヤー種族別の本文分岐はない。今回の原因を説明するために追加種族の条件は不要であり、特定種族だけの不具合とは確認していない。すべてのNPC会話・表示経路を検証したという意味ではない。

## 2. 原因と証拠

### 翻訳元と実配布物の不一致

FU_Japaneseの[再ビルド手順](../BUILDING.md)と `source/tools/build.py` は、基準コミットを `17868d86c9bb7bc00f92038fb78b48cebd1b41b8` に固定している。その[通信ファイル](https://github.com/sayterdarkwynd/FrackinUniverse/blob/17868d86c9bb7bc00f92038fb78b48cebd1b41b8/radiomessages/fu_quests.radiomessages)には、報告された `fu_start_Complete2a` が存在しない。

公式の[2026-10-02の変更](https://github.com/sayterdarkwynd/FrackinUniverse/commit/62be869b8e04bc553e813423a9e7888d411c2a83)で、トライコーダーの説明6件が削除され、`fu_start_tricorder_brief` に置き換えられた。同時に研究案内3件も変更された。[同日の別変更](https://github.com/sayterdarkwynd/FrackinUniverse/commit/c0014c8550515fc42f811419720830103fc163db)では、防具製作の案内1件も変更されている。日付は公式コミットの記録による。

一方、導入済みPAKの対象ファイルは、公式コミット `1c80b714c8b7da9ce3d35f237850ffdb236b9a2e` の[同ファイル](https://github.com/sayterdarkwynd/FrackinUniverse/blob/1c80b714c8b7da9ce3d35f237850ffdb236b9a2e/radiomessages/fu_quests.radiomessages)と、CRLFをLFへ正規化すると完全一致した。これはファイル1件の同一性を示す。導入済みFU全体がこのコミットと一致するとの意味ではない。

外部資料の参照日はすべて2026-11-09。

### 未翻訳になる二つの経路

**欠落6件：** `source/source/catalog.jsonl`、`source/source/translated_catalog.jsonl`、対象パッチのすべてに本文パスがない。報告された説明はこのケース。ビルドはカタログの行を処理するため、手動翻訳辞書に訳文を追加するだけでは出力されない。

**不一致4件：** 既存パッチは英文を `test` で照合し、一致したときだけ `replace` で訳文にする。GitHubで変更された後の英文を照合しているため、導入済み原文とは一致せず置換がスキップされる。

実装上の根拠は次のとおり。

| 箇所 | 処理 |
| --- | --- |
| `source/tools/extract.py:42` | `.radiomessages` の `text` と `senderName` を抽出 |
| `source/tools/build.py:77` | `catalog.jsonl` を翻訳対象として読み込み |
| `source/tools/build.py:95` | `manual_*.json` の手動訳文を読み込み |
| `source/tools/build.py:133` | 原文の `test` と訳文の `replace` を1組として生成 |
| `source/tools/validate.py` の `apply_batches` | 失敗した独立パッチ組をスキップして適用結果を検証 |

原文照合を削除しても、欠落6件の置換は追加されない。条件を緩めるだけでは報告された説明は直らない。

### 別の原因との切り分け

| 仮説 | 結果 |
| --- | --- |
| フォントの問題 | 合成後の本文自体が英語。今回の未翻訳は描画以前に発生 |
| 古い日本語化の導入 | 対象パッチは作業ツリーと導入先で一致 |
| 読み込み順の問題 | 既存ログはFUが先、FU_Japaneseが後。この順でも再現 |
| 種族固有の処理 | 該当データに種族別の本文分岐はない |
| 他MODの競合だけが原因 | FUとFU_Japaneseの対象データだけで再現。他の競合すべてを否定するものではない |

派生エンジンOpenStarboundの[通信データベース実装](https://github.com/OpenStarbound/OpenStarbound/blob/6352e8e3196f78388b6c771073f9e03eaa612673/source/game/StarRadioMessageDatabase.cpp)も、`.radiomessages` の `text` 等を読み取る経路を裏付ける。ただし通常版の実行ファイルを直接検証した資料ではない。結論の主な根拠は実データとパッチ適用結果である。

## 3. 確認できた影響範囲

すべて `radiomessages/fu_quests.radiomessages` の `/メッセージID/text`。

| メッセージID | 内容 | 未翻訳の理由 |
| --- | --- | --- |
| `fu_start_greetings2` | 炉の研究・製作 | 原文不一致 |
| `fu_start_makeFurnace` | 製錬とForaging Tableの研究 | 原文不一致 |
| `fu_start_makeForaging` | 生存・農業とMachining Tableの研究 | 原文不一致 |
| `fu_start_Complete1a` | Armorworksと装備の準備 | 原文不一致 |
| `fu_start_Complete2` | 左クリックでステータス等を開く | カタログ欠落 |
| **`fu_start_Complete2a`** | **Shift＋Mouse 1、またはビーカーから研究を開く** | **カタログ欠落。利用者報告に一致** |
| `fu_start_Complete2b` | 研究メニューと農業研究の案内 | カタログ欠落 |
| `fu_start_Complete3` | Mouse 2でタスク管理を開く | カタログ欠落 |
| `fu_start_Complete3a` | Shift＋Mouse 2でツール設定を開く | カタログ欠落 |
| `fu_start_Complete3b` | 捨てない注意と再製作方法 | カタログ欠落 |

本文26件のうち16件は翻訳され、上記10件は原文のまま。本文と送信者名を合わせた変更は36フィールド。ID、種別、表示時間、顔画像等の制御データは変わっていない。

10件は今回確定した対象ファイル内の件数であり、FU全体の未翻訳件数ではない。ほかの通信には架空言語等の意図的な原文維持もあるため、英字の存在だけで翻訳漏れとは判断しない。

## 4. 再現と確認結果

導入済みPAKから原文をメモリに読み、`common.read_asset` と同じ解析処理を経て、現行パッチを `validate.apply_batches` で適用した。`fu_start_Complete2a.text` は適用前後で完全一致し、英語のまま残った。

```text
input_messages: 26
patch_groups: 41
changed_fields: 36
untranslated_message_bodies: 10
reported_message_id: fu_start_Complete2a
reported_message_changed: false
preserved_non_display_fields: true
```

ゲーム本体を起動した画面検証ではなく、データとパッチの適用結果の再現である。

### 再現用の検査

依存関係は `source/requirements-test.txt` を参照。公式コミット `1c80b714…` の対象ファイルを作業用フォルダへ取得し、リポジトリ直下から以下を実行する。ゲームフォルダやセーブの変更は不要。

```python
import sys
from pathlib import Path

sys.path.insert(0, "source/tools")
from common import read_asset
from validate import apply_batches

# 取得した公式ファイルの場所に置き換える。
fixture = Path("upstream-radio/radiomessages/fu_quests.radiomessages")
before = read_asset(fixture)
patch = read_asset(
    "mods/FU_Japanese/radiomessages/fu_quests.radiomessages.patch"
)
after = apply_batches(before, patch)
missing = [key for key in before
           if before[key]["text"] == after[key]["text"]]
assert len(before) == 26
assert len(missing) == 10
assert "fu_start_Complete2a" in missing
print(missing)
```

### SHA-256による原文の識別

| 対象 | SHA-256 |
| --- | --- |
| 導入済みFUの原文、生バイト | `c986539a89a10ac526a1aa21cb0d1cf80629f8249473c9a5d6dd2c490e9a03f1` |
| 同原文、CRLFをLFへ正規化 | `d26825121dc268b03a21cff56180be75fa20ed499cef4bb4786d98eb0259ff0c` |
| 公式 `1c80b714…` の対象ファイル | `d26825121dc268b03a21cff56180be75fa20ed499cef4bb4786d98eb0259ff0c` |
| 現行FU_Japaneseの対象パッチ | `061d0f0c537e71e09595748bcf0953e3abc152214cfb47b886d05fdf59cbaa82` |

## 5. 対策案

| 案 | 内容 | 評価 |
| --- | --- | --- |
| **A：実配布原文に合わせて再生成** | 対象原文・カタログ・手動訳・生成パッチを揃える | **推奨。** 欠落と不一致の両方を修正でき、再ビルドでも保持できる |
| B：完成パッチだけを手修正 | 対象パッチへ10件を追加・修正 | 一時的には直るが、再生成で失われる。恒久対策に不十分 |
| C：原文照合を削除 | 本文を無条件、またはパスの存在だけで置換 | 欠落6件は直らない。異なる原文へ不適切な訳を適用し得るため不採用 |

案Aでは現行導入先を修正対象とし、後方互換性の維持は要件に含めない。FU全体を過去のコミットへ戻す必要はない。一致を確認した通信ファイルの出典を明示して扱う。

### 推奨する実装手順

1. **原文を固定する。** 導入済み配布物と一致する公式原文を検証用フィクスチャにし、コミット・相対パス・ハッシュを記録する。既存の基準コミットとはこのファイルが異なることを資料に明記する。
2. **抽出入力を揃える。** 対象アセットの原文を選択して抽出できるようにし、`catalog.jsonl` の対象行を更新する。カタログだけを直して次の抽出で戻る状態にしない。
3. **訳文を補完する。** `manual_radio_extra.json` 等へ欠落6件を追加し、不一致4件の訳文を実際の英文に合わせる。既存16件の本文訳は維持する。
4. **パッチを再生成する。** `translated_catalog.jsonl` と対象パッチを更新する。導入済み原文にない `fu_start_tricorder_brief` も、採用する原文に合わせて整理する。
5. **検証・配布記録を更新する。** 対象テストと新しい検証記録を追加し、MODハッシュ・公開チェックサム・変更履歴・対応原文の説明を更新する。過去の検証記録を今回の結果として扱わない。

想定する変更範囲は原文の選択・固定、対象カタログ行、手動訳文、対象パッチ、検査と資料。戦闘、クエスト進行、通信の発火処理の変更は不要。

報告された説明の訳文案：

> 個人用トライコーダーの研究メニューは、あらゆる製作レシピを解放するための重要な機能です。Shift＋左クリック、または左クリックで開いたメニュー内のビーカーのアイコンから、研究メニューを開けます。

これは未適用の案。実データでは原文の色タグを順序どおり保持し、操作キーの意味と既存の訳語を揃える。

## 6. 検証・完了条件

| 検証 | 合格条件 |
| --- | --- |
| 報告された本文 | `fu_start_Complete2a.text` が意図した日本語になる |
| 同原因の10件 | 全件が翻訳され、対象26件に今回の理由による未翻訳が残らない |
| 既存翻訳 | 正常だった16件が引き続き正しい訳文になる |
| 制御データ | ID、`type`、`unique`、`persistTime`、顔画像・フレーム数等が原文と一致 |
| 書式 | 色タグの順序、キー操作、数値、置換トークンを保持 |
| 原文識別 | アセットハッシュの相違を検出できる。6.5.8表記だけで合格にしない |
| 再生成 | 固定原文から抽出・生成して、配布する対象パッチと一致 |
| 公開整合性 | 更新後のハッシュを記録し、`check_public_repo.py` 等の必要な検査が通る |
| ゲーム内 | 左下で日本語と操作キーが読め、読込エラーが増えていない |

対象説明は `unique: true`。既読キャラクターで再表示されないだけでは修正失敗とは判断できない。実画面では発話前の状態、または検証用の状態で対象メッセージを再現する。既存セーブの既読フラグを無断で変更しない。

今回は修正前のデータ再現のみ実施。修正後の確認、ゲーム内の描画・長文の収まりは未確認。

## 7. リスク・取り消し・残る確認事項

主なリスクは、同じ6.5.8表記を根拠に異なる原文へ訳文を適用すること。対象アセットのハッシュ照合で防ぐ。日本語を20秒の表示時間で読めるかは実画面で確認し、表示時間の変更が必要なら別途判断する。

修正の取り消しは、対象のカタログ・手動訳・生成パッチ・原文選択・来歴を同じ変更単位で戻す。ゲームへ導入した後は対応する旧パッチへ戻す。セーブ変更を伴う対策は想定しない。

全種族・全NPCでの表示、ほかの通信経路の翻訳漏れ、今後のSteam配信内容の変更は未確認。今回の証拠から通信表示処理や種族処理全体へ修正を広げる必要は認めていない。

原因の確度は高い。利用者が挙げた操作説明、導入済み原文、公式変更履歴、カタログ欠落、パッチ適用後の英文残存が一致している。
