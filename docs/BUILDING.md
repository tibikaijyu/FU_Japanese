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
python source/tools/test_namegen_semantics.py --project source --mod mods/FU_Japanese --fixtures source/tests/namegen_fixtures
```

Luaの検査ではLupaに同梱されたLua 5.4を選択し、固定されたStarbound APIの代替実装から実際の表示用Luaを呼び出します。Starbound本体や画面描画は実行しません。保存済みの `species_runtime_test.lua` は、Lua 5.4から対象MODへのパスを第1引数として実行することもできます。引数がない場合は環境変数 `FUJP_TEST_MOD`、次に作業ディレクトリからの `mods/FU_Japanese` を使います。

## 固定版FUからの再ビルド

完全な再生成の基準はLinux／WSLです。Windowsネイティブでの完全な再ビルドと固定ハッシュ一致は未確認です。Windows版StarboundでMODを利用することとは別の確認項目です。

FU本体は別途取得します。基準コミットを固定し、常に最新のmasterを入力にしないでください。

```sh
git init upstream/FrackinUniverse
git -C upstream/FrackinUniverse remote add origin https://github.com/sayterdarkwynd/FrackinUniverse.git
git -C upstream/FrackinUniverse fetch --depth 1 origin 17868d86c9bb7bc00f92038fb78b48cebd1b41b8
git -C upstream/FrackinUniverse checkout --detach FETCH_HEAD
python -m venv .venv
.venv/bin/python -m pip install -r source/requirements-build.txt
.venv/bin/python source/tools/build.py --project source --upstream upstream/FrackinUniverse --machine source/machine_translation/machine_translations.json --output source/build/FU_Japanese
.venv/bin/python source/tools/validate.py --project source --upstream upstream/FrackinUniverse --mod source/build/FU_Japanese
```

Windowsの仮想環境では実行ファイルが `.venv/Scripts/python.exe` になります。`build.py` は指定した出力先を作り直します。導入済みのゲームフォルダを `--output` に指定しないでください。再ビルドは作業コピーで行い、既存の検証記録も保管してください。

モデルの再翻訳は通常不要です。`machine_translations.json` と手動補正・用語集を使います。`source/compat/followup_022/`、必要な `source/reports/`、モデル来歴を削除しないでください。

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

旧版比較で参照する結果を更新した場合、`test_summary_023.json` にある参照先のSHA-256も更新が必要です。ビルド・配布ツールはこの集約を自動で作り直しません。

## 公開用ZIP

現在の同梱構成から作成するため、外部のPixelMplusディレクトリや元の機械翻訳作業フォルダは不要です。

```sh
python source/tools/check_public_repo.py
python source/tools/package_release.py --output-dir dist
```

- `FU_Japanese_0.2.3-public.1-install.zip`：ゲーム用MOD、任意フォント、導入説明、ライセンス、最小限の出典・確認資料。
- `FU_Japanese_0.2.3-public.1-source.zip`：SHA-256一覧に登録した公開ファイル一式。モデル来歴と `pre_review_semantic_candidates.jsonl` も保持。
- `SHA256SUMS-0.2.3-public.1.txt`：上記ZIP自体のハッシュ。
- `release-artifacts.json`：ファイル数・容量・ハッシュ・検査結果。

元の機械翻訳環境の `fugumt-model/provenance.json` ではなく、同梱の `model_provenance.json` をそのまま収録します。モデル重み、`scope/`、ログ、仮想環境、`docs/development/` は収録しません。チェックサム一覧が明示的な収録対象です。

収録順、ZIP内の時刻、権限、圧縮レベルを固定しています。同じPython/zlibと入力でのZIPバイト一致を検査します。Python/zlibの異なるバージョン間でも圧縮バイトが一致するとの保証はしていません。ゲームファイルの一致、検査の再現、ZIP全体の一致は別々に確認してください。

配布構成を変えた場合は `--release-id 0.2.3-public.2` など、識別できる再梱包番号を使い、README・変更履歴・Release説明のファイル名も更新します。
