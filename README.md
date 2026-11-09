# Frackin' Universe 日本語化MOD

> [!IMPORTANT]
> このMODは、生成AI（ChatGPTなど）を用いて実装しています。翻訳の確認・補完にも生成AIを使用しており、コードや訳文に誤り・不具合が含まれる可能性があります。

Starboundの大型MOD **Frackin' Universe（FU）6.5.8** 向けの非公式日本語化です。現在の版は **0.2.4-fu6.5.8**。アイテム、研究、クエスト、会話、ガイド、種族情報などを日本語化します。FuguMTによる機械翻訳を基礎に、用語や表示文を個別に補完しています。0.2.4では通信メッセージ26本文の日本語化と、固定対象20アセットの再生成・整合を行いました。

## 導入

Starbound本体、FU 6.5.8、日本語を表示できるフォントが必要です。このリポジトリにはゲーム本体とFU本体を含めていません。

1. 配布時は **Releases** から `FU_Japanese_0.2.4-public.1-install.zip`（フォルダ版）または `FU_Japanese_0.2.4-public.1-pak.1-install.zip`（PAK版）を取得し、ZIPを展開します。いずれか一方だけを使ってください。
2. Starboundを完全に終了します。
3. 更新する場合は、旧版の `Starbound/mods/FU_Japanese` フォルダと `Starbound/mods/FU_Japanese.pak`（存在する場合）をmodsの外へ移動します。
4. フォルダ版なら展開した `mods/FU_Japanese` を `Starbound/mods` へコピーします。PAK版なら `mods/FU_Japanese.pak` をコピーします。
5. 日本語が四角になる場合は、`optional/FU_Japanese_Font` も `Starbound/mods` へコピーします。

正しい配置は `Starbound/mods/FU_Japanese/_metadata` です。展開した外側のフォルダや `source` をゲームへコピーする必要はありません。導入にPythonやpak化は不要です。詳細は [導入手順](docs/INSTALL_JA.txt) にあります。

## 収録内容

| パス | 内容 |
| --- | --- |
| `mods/FU_Japanese/` | 導入用MOD。JSONパッチとLuaの表示処理など |
| `optional/FU_Japanese_Font/` | 任意のPixelMplusフォントとライセンス |
| `docs/` | 導入・開発手順、互換性の説明、翻訳・検証資料。[文書一覧](docs/README.md) |
| `source/source/` | 翻訳カタログ、用語集、手動補完データ |
| `source/tools/` | 抽出、ビルド、検査ツール |
| `source/compat/`・`source/tests/` | 互換処理、固定した原文フィクスチャ、回帰検査 |
| `source/reports/` | 既存の検査記録。過去版の記録を含む |
| `SHA256SUMS.txt` | このリポジトリの公開対象ファイルのSHA-256 |

調査用の `source/reports/scope/`、実行ログ、ローカルの開発資料はGitの対象外です。ゲーム用データ、翻訳カタログ、回帰検査用の資料は収録しています。`0.2.4-public.1` はフォルダ版とソース版の識別子、`0.2.4-public.1-pak.1` はPAK版の識別子です。`-install.zip` は導入用、`-source.zip` とGitHubが生成する **Source code** は開発用です。フォルダ版とPAK版を同時にmodsへ入れないでください。

## 開発・検査

GitとPython 3.11以降を用意し、リポジトリのルートで実行します。公開ファイルの検査には追加のPythonパッケージは不要です。

```sh
python source/tools/check_public_repo.py
```

公開対象のファイル名・容量、典型的な認証情報のパターン、JSON構文、SHA-256、既存のMODハッシュ、キャラクター名生成用の空パッチを検査します。ゲームの起動、全翻訳の品質、秘密情報の完全な検出を保証する検査ではありません。

再ビルドには `source/requirements-build.txt` の依存パッケージと、基準コミット `17868d86c9bb7bc00f92038fb78b48cebd1b41b8` のFUソースが別途必要です。[開発・再生成手順](docs/BUILDING.md)と[翻訳修正の案内](CONTRIBUTING.md)を参照してください。通常の再ビルドで機械翻訳モデルを再実行する必要はありません。

同梱構成から導入用・開発用ZIPを作成するには、次を実行します。`dist/` はGitの対象外です。

```sh
python source/tools/package_release.py --output-dir dist
```

## 出典・ライセンス

- 原作：Sayterおよび [Frackin' Universeの貢献者](https://github.com/sayterdarkwynd/FrackinUniverse)。公式Steamページは [こちら](https://steamcommunity.com/sharedfiles/filedetails/?id=729480149) です。
- 翻訳・改変アセット：既存の配布表記に従いCC BY 4.0。詳細は [ライセンス案内](LICENSE.md) と [帰属表示](mods/FU_Japanese/ATTRIBUTION.txt) を参照してください。
- 任意フォント：PixelMplus（itouhiro / M+ FONTS PROJECT）、M+ FONT LICENSE。
- 独立したPythonコード：MIT。埋め込まれたFU由来の原文・翻訳データは別扱いです。[適用範囲](LICENSE.md)を参照してください。
- 機械翻訳モデル：FuguMT（S-Taka）、CTranslate2変換（jkawamoto）。モデル重みは同梱していません。[モデルの出典とライセンス](source/machine_translation/README.md) を参照してください。

翻訳はFuguMTを基礎とし、ChatGPTによる確認・補完を行っています。人手で全文を校正済みという意味ではありません。第三者の出典は [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) にまとめています。

本MODはFU原作者・Chucklefishによる制作・承認を受けたものではありません。
