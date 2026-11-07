# 翻訳・開発への参加

不具合や翻訳の修正案はIssueで報告できます。表示される画面、アイテム・クエスト等の名前、MODとFUの版、原文・現在の訳文・修正案を記載してください。

## 翻訳の修正場所

`mods/FU_Japanese/` と `source/source/translated_catalog.jsonl` は生成結果です。変更を再ビルドでも維持するため、翻訳入力を修正し、生成結果との対応を示してください。

- 通常の表示文：`source/source/manual_*.json`、用語集 `glossary.json` など。既存の同じ原文を検索し、補正の適用順を `source/tools/build.py` で確認します。
- 配列追加・埋め込みJSON：`manual_append.json`、`manual_embedded.json` と対応する抽出カタログ。
- Luaの表示文：`lua_translations.json`、`lua_dynamic_translations.json`、対象を限定するマニフェスト。
- ガイド・種族の表示補完：`source/compat/followup_022/` と `source/source/followup_022_manifest.json`。ハッシュを固定した入力のため、変更時は関連マニフェストと回帰検査も更新します。

機械翻訳を再実行して手動補正を上書きする必要はありません。固有名・用語は用語集との整合性を確認してください。

## 保持するデータ

アイテムID、種族ID、スクリプト名、JSONの構造キー、数値、参照先、制御パラメーターを翻訳しないでください。`^green;` などの色指定、変数・置換タグ、`[(pause)...]` などのFUコマンドは保持します。

キャラクター名生成の学習辞書・候補・参照IDは翻訳対象に戻しません。`retired_character_name_assets.json` に列挙された32ファイルの空パッチは、旧版の変更を取り除くためのものです。表示文に見える文字列でも、生成アルゴリズムの入力である場合は原文を維持します。

## 検査

Python 3.11以降を使い、ルートから実行します。

```sh
python -m pip install -r source/requirements-test.txt
python source/tools/test_public_release.py
python source/tools/test_namegen_semantics.py --project source --mod mods/FU_Japanese --fixtures source/tests/namegen_fixtures
python source/tools/check_public_repo.py
```

変更内容をレビューしてから `python source/tools/check_public_repo.py --write-checksums` で公開対象のハッシュを更新します。ゲーム用データを変更した場合は、先に変更に対応する実質的な検査を行い、検証レポートとMODハッシュを更新します。検査を通すためだけに既存の証跡を書き換えないでください。

再生成、Lua共有ライブラリ、旧版配布物の前提は [docs/BUILDING.md](docs/BUILDING.md) に記載しています。Pull Requestには入力側の修正、対象アセット、実行した検査、未確認の画面を記載してください。ゲームの描画・文字の見切れ・操作遷移は実機で確認する項目です。

## ライセンスと公開資料

独立したPython実装はMIT、FU由来の原文・翻訳・固定データは既存のCC BY 4.0に従います。詳細は [LICENSE.md](LICENSE.md) を参照してください。

生ログ、セーブ、認証情報、個人のパスは含めないでください。Issueの画像やログ抜粋では、利用者名・SteamアカウントID・IPアドレス等を伏せ、エラー前後の関係を残します。
