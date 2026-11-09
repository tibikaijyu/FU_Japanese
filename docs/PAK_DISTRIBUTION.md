# FU_Japanese PAK配布

PAK版は、ゲーム内MOD本体 `mods/FU_Japanese` だけをStarbound公式の `asset_packer.exe` で梱包した配布形式です。フォルダ版と同じ訳・設定を含み、`source/`、`docs/`、ビルド資料、検査記録はPAKへ入りません。

## 作成

Windows版Starboundの `win32` フォルダにある公式 `asset_packer.exe` と `asset_unpacker.exe` を指定します。ツールは読み取り専用で利用し、出力はリポジトリ内の `dist/` に作成します。

```powershell
python source/tools/check_public_repo.py
python source/tools/package_release.py `
  --output-dir dist `
  --release-id 0.2.4-public.1 `
  --pak-release-id 0.2.4-public.1-pak.1 `
  --pak-tools-dir "E:/SteamLibrary/steamapps/common/Starbound/win32"
```

この実行でフォルダ版、PAK版、ソース版のZIPを別々に作ります。`FU_Japanese_0.2.4-public.1-pak.1-install.zip` には `mods/FU_Japanese.pak` が入り、フォルダ版の `mods/FU_Japanese/` は入りません。PAK版ZIP内で両形式を併配しません。

PAKを作った後、公式 `asset_unpacker.exe` で作業用一時ディレクトリへ展開し、フォルダMODと相対パスを全件比較します。`_metadata` 以外はファイル数・サイズ・生バイトのSHA-256が一致することを要求します。公式ツールは `_metadata` をJSONとして再直列化し、空白とキー順を変更するため、生バイトSHAは一致しません。その代わり、JSONの深い構造を型も含めて比較し、キー・値・型が変わらないこととcanonical JSONのSHA-256一致を要求します。検証報告にはmetadataの入力・展開後の生SHAも記録します。このため「PAK内全ファイルの生バイト一致」とは報告しません。

次のファイルを確認します。

- `FU_Japanese_0.2.4-public.1-pak.1-install.zip` と `FU_Japanese_0.2.4-public.1-pak.1-verification.json`
- `SHA256SUMS-0.2.4-public.1.txt`：フォルダ版・PAK版・ソース版ZIPのSHA-256
- `release-artifacts.json`：各ZIPの一覧、SHA-256、PAKの検証結果

`0.2.4-public.1` はMODの公開リリースID、`0.2.4-public.1-pak.1` はそのリリース内のPAK配布形式のIDです。再梱包時は公開リリースIDを進め、PAK形式番号を1から付け直します。フォルダ版と同じIDをPAK版に使わないでください。

## 導入

1. Starboundを完全に終了します。
2. PAK版ZIPを展開し、最上位のリリースフォルダ内にある `mods/FU_Japanese.pak` をStarboundの `mods/` にコピーします。
3. 同名のフォルダ版 `mods/FU_Japanese/` や旧PAK版があれば、`mods/` の外へ移動します。同時にmods内へ置かないでください。
4. 起動して日本語表示を確認します。

フォルダ版を選ぶ場合はフォルダ版ZIPのみを展開します。フォルダ版ZIPとPAK版ZIPの両方を同じ `mods/` へ入れないでください。既存の日本語フォントやFU本体はこの切替では変更しません。

## 旧版の性能比較候補

修正前の `0.2.3-fu6.5.8` を対象MODのみ梱包した内容不変の比較用PAKと、入力スナップショット、unpack結果、SHA-256検証記録は、リポジトリ外のローカル作業データ `.local/fu-package-baseline/` に保存します。これは公開配布物ではなく、最終修正版のPAKとは別の性能比較候補です。
