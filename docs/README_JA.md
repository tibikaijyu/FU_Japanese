# Frackin' Universe 日本語化MOD 0.2.4

> [!IMPORTANT]
> このMODは生成AI（ChatGPTなど）を用いて実装し、翻訳の確認・補完にも生成AIを使用しています。コードや訳文に誤り・不具合が含まれる可能性があります。

FU 6.5.8向けの非公式日本語化です。ゲーム内MOD版は 0.2.4-fu6.5.8 です。フォルダ/ソース配布の識別子は 0.2.4-public.1、PAK配布の識別子は 0.2.4-public.1-pak.1 です。FuguMTによる機械翻訳を基礎に、表示文を補完しています。

## 0.2.4の内容

20個の固定対象アセットを再生成しました。更新対象は直接翻訳60グループと配列追加1,030グループです。20対象の最終JSONは独立比較で一致しています。

FU通信メッセージ26本文を日本語化し、既存の16本文を維持したうえで10本文を更新しました。本文の色タグ、数値、制御データ、キーなどの保護要素も検査しています。

検証は固定した対象の再生成と静的比較に限られます。FU全体ソースの再取得・全体ビルド・全体検証は行っていません。Starbound本体での表示や処理性能も未確認です。実機確認は後日行います。詳しくはソース版の `docs/verification/2026-11-10-fu-024-targeted-verification.md`を参照してください。

## 導入

Starbound本体、FU 6.5.8、日本語を表示できるフォントが必要です。ゲーム本体とFU本体は配布物に含みません。

フォルダ版は FU_Japanese_0.2.4-public.1-install.zip、PAK版は FU_Japanese_0.2.4-public.1-pak.1-install.zip を使用します。どちらか一方を選び、展開した後にStarboundを終了してから導入してください。更新時は古いFU_JapaneseフォルダとFU_Japanese.pak（存在する場合）をmodsの外へ移します。

- フォルダ版のMOD配置先は Starbound/mods/FU_Japanese/_metadata です。ZIP内のmods/FU_Japaneseをコピーします。
- PAK版はZIP内の mods/FU_Japanese.pak をStarbound/modsへコピーします。フォルダ版とPAK版を同時に導入しないでください。
- 日本語が四角で表示される場合だけ、optional/FU_Japanese_Fontを追加します。すでに使用中の日本語フォントで表示できるなら変更不要です。

展開した外側のフォルダやsourceをゲームのmodsへ入れないでください。導入にPythonや追加のpak化は必要ありません。画面ごとの案内は同梱の[導入手順](INSTALL_JA.txt)を参照してください。PAKの扱いは[PAK配布案内](PAK_DISTRIBUTION.md)を参照してください。

## 不具合の切り分け

同じ操作で問題が起きる場合は、Starboundを終了し、この日本語化MODだけを一時的にmodsの外へ移して比較してください。FU本体やセーブデータを削除する必要はありません。画面、選択した種族、直後のStarbound/storage/starbound.logを控えておくと、問題を調べやすくなります。

0.2.3より前のキャラクター画面フリーズに関する利用者報告・検証は、当時の版の記録として、ソース版の docs/verification/2026-11-07-user-report.md に残しています。0.2.4の実機確認を示すものではありません。

## 開発とライセンス

再生成・公開用パッケージ作成・検査の手順はソース版の `docs/BUILDING.md` にあります。FU由来アセットの原作はSayterおよびFrackin' Universeの貢献者によるもので、原作・翻訳・改変データはCC BY 4.0の表示条件に従います。任意フォントはM+ FONT LICENSEです。出典と適用範囲はソース版の `LICENSE.md`、`THIRD_PARTY_NOTICES.md`、MOD内のATTRIBUTION.txtを参照してください。

本MODはFU原作者・Chucklefishによる制作・承認を受けたものではありません。
