# ドキュメント

## 導入・利用

- [導入手順](INSTALL_JA.txt)：インストール、更新、再発時の確認。
- [詳しい利用ガイド](README_JA.md)：変更内容、翻訳範囲、検証済み・未確認の範囲。
- [変更履歴](../CHANGELOG.md)／[ライセンス](../LICENSE.md)／[第三者の出典](../THIRD_PARTY_NOTICES.md)。

## 開発・翻訳

- [開発・再生成・配布](BUILDING.md)。
- [翻訳・開発への参加](../CONTRIBUTING.md)。
- [UTF-8表示の互換処理](compatibility/COMPATIBILITY.md)。
- [Luaの表示文の日本語化](compatibility/LUA_LOCALIZATION.md)。
- [手動翻訳の確認範囲](translation/manual_priority_review.md)。
- [機械翻訳環境とモデルの出典](../source/machine_translation/README.md)。

## 検証記録

以下は記載された版・時点での記録です。Starbound本体での利用者報告と、自動検査の結果を区別しています。

- [0.2.4対象アセットの再生成と検証](verification/2026-11-10-fu-024-targeted-verification.md)：固定20アセットと通信メッセージ26本文の対象限定検証。全体ビルドと実機表示は未確認です。
- [FU追加の通信メッセージ未翻訳の調査](verification/2026-11-09-radio-message-translation.md)：Shift＋Mouse 1の説明を含む10件の調査。過去時点の調査記録です。
- [2026-11-07のフリーズ解消報告](verification/2026-11-07-user-report.md)。
- [0.2.2の種族情報表示の修正](verification/README_SPECIES_022.md)。
- [種族情報・キャラクター作成画面の監査](verification/species_ui_audit_023.md)。
- [起動・キャラクター選択に関連するLua監査](verification/startup_lua_audit_023.md)。

機械処理する検査結果は `source/reports/`、テストデータとその説明は `source/tests/` にあります。依存関係を指定する `requirements*.txt` は、それぞれの実行環境の近くに置いています。

導入用ZIPでは、すぐ読めるように `README_JA.md` と `INSTALL_JA.txt` をZIP内の配布フォルダ直下へ配置します。開発用ZIPではリポジトリと同じ配置です。
