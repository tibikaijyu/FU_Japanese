# 第三者の出典とクレジット

## Frackin' Universe

原作：SayterおよびFrackin' Universeの貢献者。FUメタデータ版6.5.8、基準コミット `17868d86c9bb7bc00f92038fb78b48cebd1b41b8` を使用しています。

- [公式ソース](https://github.com/sayterdarkwynd/FrackinUniverse)
- [基準版の貢献者表示](https://github.com/sayterdarkwynd/FrackinUniverse/blob/17868d86c9bb7bc00f92038fb78b48cebd1b41b8/_FUcredits.config)
- [CC BY 4.0の同梱本文](mods/FU_Japanese/LICENSE-FU-CC-BY-4.0.txt)／[詳細な帰属表示](mods/FU_Japanese/ATTRIBUTION.txt)

本配布物では表示文の日本語化、辞書による表示補完、UTF-8処理などを変更しています。翻訳カタログ、改変Lua、テストに含まれる原文も帰属表示の対象です。非公式の翻訳であり、原作者やChucklefishによる承認を意味しません。

## PixelMplus

作者：itouhiro / M+ FONTS PROJECT。`PixelMplus10-Regular.ttf` を無改変で `hobo.ttf` に改名しています。基準リビジョンは `d89b95f04eeb95bf98bb09cb9234a2f99d186df5` です。

- [作者リポジトリ](https://github.com/itouhiro/PixelMplus)
- [帰属表示](optional/FU_Japanese_Font/ATTRIBUTION.txt)
- [M+ FONT LICENSE（日本語）](optional/FU_Japanese_Font/LICENSE-MPLUS-JA.txt)／[英語](optional/FU_Japanese_Font/LICENSE-MPLUS-EN.txt)

## FuguMT

機械翻訳の基礎にはS-TakaによるFuguMTを使用しました。CTranslate2変換はjkawamotoによるものです。変換モデルの固定リビジョンは `5bdad25200fcf251bbf019a6ee613002df52869b` です。

- [原モデル：staka/fugumt-en-ja](https://huggingface.co/staka/fugumt-en-ja)
- [変換版：jkawamoto/fugumt-en-ja-ct2](https://huggingface.co/jkawamoto/fugumt-en-ja-ct2)
- [原作者の説明](https://github.com/s-taka/fugumt)／[S-Takaのブログ](https://staka.jp/wordpress/)
- [CTranslate2](https://github.com/OpenNMT/CTranslate2)

モデルカードのライセンスはCC BY-SA 4.0です。モデル重みはGit・導入用ZIP・開発用ZIPのいずれにも含めていません。モデル来歴は開発用ソースの `source/machine_translation/model_provenance.json` に保持しています。モデルの許諾と、FU原文・翻訳成果物の扱いを一律に同じものとはしていません。

翻訳にはChatGPTによる確認・補完も含まれます。全文を人手で校正済みという意味ではありません。
