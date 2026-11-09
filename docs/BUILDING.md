# 開発・再生成・配布

コマンドはリポジトリのルートから実行します。ビルドの `--project` は `source/` です。`source/source/` は翻訳入力、`source/compat/` は固定した互換処理を保持しており、この配置を維持します。

## 公開ファイルと回帰検査

Python 3.11以降とGitを使います。公開ファイルだけの検査は標準ライブラリで実行できます。

```sh
python source/tools/check_public_repo.py
```

名前生成の固定フィクスチャと、公開パッケージ・種族表示のLuaを検査する場合は、依存を追加します。

```sh
python -m pip install -r source/requirements-test.txt
python source/tools/test_public_release.py
python source/tools/test_pak_release.py
python source/tools/test_namegen_semantics.py --project source --mod mods/FU_Japanese --fixtures source/tests/namegen_fixtures
```

Luaの検査ではLupaに同梱されたLua 5.4を選択し、固定されたStarbound APIの代替実装から実際の表示用Luaを呼び出します。Starbound本体や画面描画は実行しません。保存済みの `species_runtime_test.lua` は、Lua 5.4から対象MODへのパスを第1引数として実行することもできます。引数がない場合は環境変数 `FUJP_TEST_MOD`、次に作業ディレクトリからの `mods/FU_Japanese` を使います。

## 固定版FUからの再ビルド

完全な再生成の基準はLinux／WSLです。Windowsネイティブでの完全な再ビルドと固定ハッシュ一致は未確認です。Windows版StarboundでMODを利用することとは別の確認項目です。

FU本体は別途取得します。基準コミットを固定し、常に最新のmasterを入力にしないでください。通信アセットだけは導入済みFUと一致する公式単一ファイルをoverrideとして固定し、出典コミットとSHA-256を `source/source/upstream_overrides.json` に記録します。FU全体の基準は `17868d86c9bb7bc00f92038fb78b48cebd1b41b8`、通信ファイルの基準は `1c80b714c8b7da9ce3d35f237850ffdb236b9a2e` です。配布PAKやゲーム原本をリポジトリへ含めません。

まず固定FUソースを取得し、依存をインストールします。

```sh
git init upstream/FrackinUniverse
git -C upstream/FrackinUniverse remote add origin https://github.com/sayterdarkwynd/FrackinUniverse.git
git -C upstream/FrackinUniverse fetch --depth 1 origin 17868d86c9bb7bc00f92038fb78b48cebd1b41b8
git -C upstream/FrackinUniverse checkout --detach FETCH_HEAD
python -m venv .venv
.venv/bin/python -m pip install -r source/requirements-build.txt
```

Windowsの仮想環境では `.venv/Scripts/python.exe` を使います。

次に、読み取り専用Starbound/Workshopのパスを記すローカル設定 `.local/append-basis-inputs.json` を用意します。JSONのschemaは `base_pak` と適用順の `layers` 配列です。baseの後に並べる12層は、日本語化、jpfix、FU本体、PerennialCrops、PlantPot、beam_up、One-Handed-Torch、ContainerUITweak、Weapon-Stats、Improved-Containers、food_stack、readable_ui です。層名と順序は固定し、pathだけ自分の環境に合わせます。この設定は公開せず、位置マニフェストにも環境固有パスを保存しません。

```json
{
  "base_pak": "<Starbound>/assets/packed.pak",
  "layers": [
    { "name": "japanese", "path": "<Starbound>/mods/japanese.pak" },
    { "name": "jpfix", "path": "<Workshop>/2819248968/contents.pak" },
    { "name": "fu", "path": "<Workshop>/729480149/contents.pak" },
    { "name": "PerennialCrops", "path": "<Workshop>/730378641/contents.pak" },
    { "name": "PlantPot", "path": "<Workshop>/1622305545/contents.pak" },
    { "name": "beam_up", "path": "<Workshop>/733047573/contents.pak" },
    { "name": "One-Handed-Torch", "path": "<Workshop>/730587191/contents.pak" },
    { "name": "ContainerUITweak", "path": "<Workshop>/729524482/contents.pak" },
    { "name": "Weapon-Stats", "path": "<Workshop>/729726478/contents.pak" },
    { "name": "Improved-Containers", "path": "<Workshop>/729427606/contents.pak" },
    { "name": "food_stack", "path": "<Workshop>/729427436/contents.pak" },
    { "name": "readable_ui", "path": "<Starbound>/mods/readable_ui" }
  ]
}
```

初回またはFU更新後は、依存をインストールした後に固定FU全体を抽出し、通信1件だけを公式overrideからマージします。マージ対象を他のアセットへ広げると失敗します。抽出後に位置基準を捕捉します。生成時にも入力の有無、名前重複、順序、対象データ、SHA-256を再照合します。

```sh
.venv/bin/python source/tools/extract.py upstream/FrackinUniverse source/source
.venv/bin/python source/tools/extract.py source/upstream-overrides source/source --merge-asset radiomessages/fu_quests.radiomessages
.venv/bin/python source/tools/append_index_basis.py --capture-inputs-json .local/append-basis-inputs.json --project source
.venv/bin/python source/tools/build.py --project source --upstream upstream/FrackinUniverse --machine source/machine_translation/machine_translations.json --output source/build/FU_Japanese --append-basis-inputs .local/append-basis-inputs.json
.venv/bin/python source/tools/validate.py --project source --upstream upstream/FrackinUniverse --mod source/build/FU_Japanese
```

`build.py` は指定した出力先を作り直します。導入済みゲームフォルダを `--output` に指定しないでください。モデルの再翻訳は通常不要です。`source/compat/followup_022/`、必要な `source/reports/`、モデル来歴を削除しないでください。

完成済みMODから固定位置配列20件だけを再生成する場合は `--indexed-assets` を使います。直接翻訳60群は通常カタログから再構成し、append 1,225行は位置マニフェストから解決します。通信だけなら `--asset-only` を使います。どちらも版情報・出典を更新する部分ビルドで、対象外の生成物を変更しません。全体ビルドの代用ではありません。今回の対象限定検証は [0.2.4 対象再生成・検証記録](verification/2026-11-10-fu-024-targeted-verification.md) を参照してください。

```sh
python source/tools/build.py --project source --machine source/machine_translation/machine_translations.json --output mods/FU_Japanese --append-basis-inputs .local/append-basis-inputs.json --indexed-assets
python source/tools/build.py --project source --machine source/machine_translation/machine_translations.json --output mods/FU_Japanese --append-basis-inputs .local/append-basis-inputs.json --asset-only radiomessages/fu_quests.radiomessages
```


## 0.2.4の対象再検証と証拠

再検証には、旧0.2.3 MODのローカル控えとStarbound/Workshopの読み取り専用アセットが必要です。これらは公開物に含めません。`.local/append-basis-inputs.json` の例とレイヤー順は前節を参照してください。

`run_release_regressions.py` は対象MOD検査、実回帰テスト、入力状態の前後一致を実行し、`source/reports/regression_024.json` を作成します。基準MODは未変更の0.2.3フォルダを使ってください。ゲームを起動するテストではありません。

```sh
python source/tools/run_release_regressions.py \
  --baseline-mod "<旧0.2.3 MODフォルダ>" \
  --mod mods/FU_Japanese \
  --append-basis-inputs .local/append-basis-inputs.json
```

検証の詳細出力は `source/reports/validation.json` と `source/reports/mod_sha256.json` です。回帰レポートが合格し、実行時点の入力状態と一致する場合に限り、次で `source/reports/test_summary_024.json` を作成します。

```sh
python source/tools/release_evidence.py create --report regression_024.json
```

入力状態が変わった後はテストを再実行してから要約を作り直してください。0.2.3の `verify_release_023.py` と `test_summary_023.json` は履歴として保持し、0.2.4用に上書きしません。

## 旧版比較と追加検査

同梱の検査記録は当時の結果です。公開準備で再実行した検査とは区別します。

| 検査 | 追加で必要な入力 |
| --- | --- |
| `test_namegen_semantics.py` | 同梱の `source/tests/namegen_fixtures` を `--fixtures` に明示 |
| `test_namegen_upgrade.py` | 実際の旧版配布フォルダと固定原文。詳細は `--help` |
| `test_character_name_restoration.py` | 旧版MOD、固定FU原文、取得元マニフェスト。詳細は `--help` |
| `verify_release_023.py` | 元の0.2.2 ZIP。SHA-256は `ae519e8b48b099981e448e87744bdb02a5b26b6b944809dbae175ec227ee37b9` |
| 既存の全Lua・互換処理検査 | 固定FUソースと、各スクリプトが指定するLua共有ライブラリ |

旧配布物は同梱していません。入手した元の配布物をローカルに置き、対応する検査のハッシュ・版確認を通してください。整理して作り直した公開用ZIPを、元の旧版ZIPの代用にしてはいけません。

`verify_release_023.py` と `test_summary_023.json` は0.2.3以前の履歴資料です。0.2.4のリリース判定へ流用・上書きしないでください。0.2.4では `verify_release_024.py` を実行し、その検査結果と現在のMOD・生成ソースの状態を結び付けた `test_summary_024.json` を作成します。集約対象レポートを変更した後は、検査を再実行して要約を更新してください。

## 公開用ZIP

現在の同梱構成から作成するため、外部のPixelMplusディレクトリや元の機械翻訳作業フォルダは不要です。

```sh
python source/tools/check_public_repo.py
python source/tools/package_release.py --output-dir dist --release-id 0.2.4-public.1
```

- `FU_Japanese_0.2.4-public.1-install.zip`：フォルダ版MOD、任意フォント、導入説明、ライセンス、最小限の出典・確認資料。
- `FU_Japanese_0.2.4-public.1-source.zip`：SHA-256一覧に登録した公開ファイル一式をリポジトリと同じ配置で収録。モデル来歴と `pre_review_semantic_candidates.jsonl` も保持。
- `SHA256SUMS-0.2.4-public.1.txt`：上記ZIP自体のハッシュ。
- `release-artifacts.json`：ファイル数・容量・ハッシュ・検査結果。

元の機械翻訳環境の `fugumt-model/provenance.json` ではなく、同梱の `model_provenance.json` をそのまま収録します。モデル重み、`scope/`、ログ、仮想環境、`docs/development/` は収録しません。チェックサム一覧が明示的な収録対象です。

収録順、ZIP内の時刻、権限、圧縮レベルを固定しています。同じPython/zlibと入力でのZIPバイト一致を検査します。Python/zlibの異なるバージョン間でも圧縮バイトが一致するとの保証はしていません。ゲームファイルの一致、検査の再現、ZIP全体の一致は別々に確認してください。

配布構成を変えた場合は `--release-id 0.2.4-public.2` など、識別できる再梱包番号を使い、README・変更履歴・Release説明のファイル名も更新します。

## PAK版の生成

公式Windows版Starboundのwin32ツールを指定すると、フォルダ版・PAK版・ソース版をそれぞれ別のZIPとして生成し、PAKを公式unpackerで検証します。

```powershell
python source/tools/check_public_repo.py
python source/tools/package_release.py `
  --output-dir dist `
  --release-id 0.2.4-public.1 `
  --pak-release-id 0.2.4-public.1-pak.1 `
  --pak-tools-dir "E:/SteamLibrary/steamapps/common/Starbound/win32"
```

PAK版だけが必要な場合も同じコマンドで生成されますが、公開出力には通常のフォルダ版・ソース版も含まれます。PAK版ZIPは `mods/FU_Japanese.pak` を含み、`mods/FU_Japanese/` は含みません。個別のIDと検証項目、metadata再直列化の扱いは [PAK_DISTRIBUTION.md](PAK_DISTRIBUTION.md) を参照してください。フォルダ版とPAK版を同じ `mods/` へ同時導入しないでください。
