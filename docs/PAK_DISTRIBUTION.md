# FU_Japanese PAK配布

公開リリースに含める導入物はPAK版だけです。通常のMOD本体は `mods/FU_Japanese.pak`、任意フォントはフォント・メタデータ・ライセンスの計5ファイルをまとめた別PAK `optional/FU_Japanese_Font.pak` です。生のMODフォルダはGit上の開発用ソースとして保持しますが、配布ZIPには入れません。ソースはGitリポジトリで提供し、source ZIPとフォルダ版ZIPは生成しません。

今回の識別子はリリース `0.2.4-public.2`、PAK `0.2.4-public.2-pak.1` です。同一IDの既存出力がある場合は上書きせず、生成処理を停止します。古い `dist/` 成果物は履歴として保持します。

## 生成

公式Windows版Starboundの `win32` にある `asset_packer.exe` と `asset_unpacker.exe` が必須です。PAKツールを指定せずに実行することはできません。ツールがない、梱包または展開に失敗する、展開後の比較に不一致がある場合、配布生成全体を停止します。フォルダ版へのfallbackはありません。

```powershell
python source/tools/check_public_repo.py
python source/tools/package_release.py `
  --output-dir dist `
  --release-id 0.2.4-public.2 `
  --pak-release-id 0.2.4-public.2-pak.1 `
  --pak-tools-dir "<Starbound>/win32"
```

この実行が作る導入ZIPは `FU_Japanese_0.2.4-public.2-pak.1-install.zip` の1つです。ZIPには `mods/FU_Japanese.pak`、`optional/FU_Japanese_Font.pak`、README・導入案内、ライセンス・出典を収録します。ライセンス文書は `LICENSES/FU_Japanese/` と `LICENSES/FU_Japanese_Font/` に格納し、パッケージ内からのリンクも合わせます。

公式unpackerで各PAKを一時領域へ展開し、通常MODの各ファイルと比較します。`_metadata` 以外はファイル数・サイズ・生バイトのSHA-256を照合します。`_metadata` は公式ツールがJSONを再直列化して空白やキー順を変えるため、JSONの深い構造・型・値とcanonical JSONのSHA-256で比較し、検証レポートへ入力と展開後の生SHA-256も記録します。「全ファイルの生バイトが一致」とは表現しません。任意フォントPAKも収録ファイルを検証します。

生成物には次が含まれます。

- `FU_Japanese_0.2.4-public.2-pak.1-install.zip`：唯一の導入ZIP。
- `FU_Japanese_0.2.4-public.2-pak.1-verification.json`：PAKの検証記録。
- `SHA256SUMS-0.2.4-public.2.txt`：生成物のSHA-256一覧。
- `release-artifacts-0.2.4-public.2.json`：成果物情報とアップロード許可一覧。

## リリースへのアップロード

`release-artifacts-0.2.4-public.2.json` の `upload_allowlist` を確認し、そこに記された導入ZIPだけを選択します。対応する `SHA256SUMS-0.2.4-public.2.txt` は任意で添付できます。検証JSONや任意の `dist/*` を一括でアップロード対象にしないでください。古い成果物は消さず、新しく生成したIDの成果物だけを公開します。ソースコードはGitリポジトリを案内します。

## 導入

1. Starboundを完全に終了します。
2. PAK版ZIPを展開します。
3. 新しいPAKをコピーする前に、古い `mods/FU_Japanese/` フォルダと `mods/FU_Japanese.pak` があれば、modsの外へ移動します。別名の旧フォルダやPAKもmods内に残さないでください。
4. ZIP内の `mods/FU_Japanese.pak` をStarboundの `mods/` へコピーします。
5. 日本語が四角になる場合だけ、追加前に旧 `mods/FU_Japanese_Font/` フォルダと `mods/FU_Japanese_Font.pak` があればmodsの外へ移動し、その後 `optional/FU_Japanese_Font.pak` を `mods/` へコピーします。すでに使っている日本語フォントで表示できる場合は不要です。

Starbound本体・FU本体・セーブデータはこの切替で変更されません。ゲーム内の表示と速度は、この文書のパッケージ検証だけでは確認できません。実機での表示・性能確認は後日行います。

## 過去版の記録

0.2.3以前の配布物・検証記録と過去の `dist/` は履歴として保持します。この案内は今後作成するリリースZIPの規則で、古いリリース履歴を書き換えません。
