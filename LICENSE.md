# ライセンスと帰属

このリポジトリには、ライセンスが異なる素材を含みます。既存の帰属表示とライセンス本文を保持しています。

## FU由来の素材・日本語化アセット

原作はSayterおよびFrackin' Universeの貢献者によるものです。FU由来の文章・スクリプト・検査用原文、および既存の配布表記で対象とされた翻訳文・改変スクリプトは **Creative Commons Attribution 4.0 International（CC BY 4.0）** に従います。

- [公式FUリポジトリ](https://github.com/sayterdarkwynd/FrackinUniverse)
- [基準コミットのライセンス](https://github.com/sayterdarkwynd/FrackinUniverse/blob/17868d86c9bb7bc00f92038fb78b48cebd1b41b8/LICENSE.txt)
- [同梱のライセンス本文](mods/FU_Japanese/LICENSE-FU-CC-BY-4.0.txt)
- [著作者・基準版・改変内容の帰属表示](mods/FU_Japanese/ATTRIBUTION.txt)
- [CC BY 4.0の公式説明](https://creativecommons.org/licenses/by/4.0/deed.ja)

日本語化には表示文の翻訳、表示境界での辞書参照、UTF-8対応などが含まれます。原作者・Chucklefishによる承認を示すものではありません。

## 任意フォント

`optional/FU_Japanese_Font/hobo.ttf` はPixelMplus10 Regularを無改変で改名したものです。itouhiroおよびM+ FONTS PROJECTの表記を保持しています。

- [帰属表示](optional/FU_Japanese_Font/ATTRIBUTION.txt)
- [M+ FONT LICENSE（日本語）](optional/FU_Japanese_Font/LICENSE-MPLUS-JA.txt)
- [M+ FONT LICENSE（英語）](optional/FU_Japanese_Font/LICENSE-MPLUS-EN.txt)

## 外部モデルと補助ツール

FuguMTのモデル重みとCTranslate2変換モデルは同梱していません。モデルのライセンスは [機械翻訳資料](source/machine_translation/README.md#translation-model-and-attribution) を参照してください。

独立して新規作成したPythonコードの実装部分は **MIT License** で提供します。対象は `source/tools/*.py`、`source/machine_translation/*.py`、`source/compat/test_*.py`、`source/tests/**/*.py` の独自コードです。[MITの本文](LICENSES/MIT-tools.txt)を参照してください。

Pythonファイルに埋め込まれたFUの原文・訳文・固定アセットはMITの対象に含めず、上記のCC BY 4.0と帰属表示を維持します。たとえば `curated_*.py`、`curate_*.py`、`curation.py` 内の翻訳辞書もこの区別に従います。第三者の実装に個別の表記がある場合は、その表記を優先します。リポジトリ全体を一律にMITとするものではありません。

新規ドキュメントについては、この公開準備で追加のライセンスを設定していません。
