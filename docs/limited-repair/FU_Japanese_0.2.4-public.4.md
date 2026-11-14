# FU Japanese 0.2.4-public.4 限定修復版

このPre-releaseは、種族・ガイド表示ヘルパー `fujp/species_display.lua` と `fujp/guide_display.lua` の2件を修正します。Starbound JSON由来のLua tableには型ヒントやnull位置を記録する既知のメタテーブルが付くため、通常tableだけを許可する検査では有効な辞書を拒否していました。修正版は通常tableと既知のJSONメタテーブルを検査し、不明なproxyや不正なshapeを拒否します。

Lua 5.3/5.4で種族・ガイド各262ケース、785 assertion、core 8ケース、142 assertionを実行しました。テストはJSONメタデータ、null、未知proxy、失敗時の原文維持、警告抑制を含みます。限定修復用の単体テストは30件です。

公開3からのゲーム用差分はこの2ヘルパーだけです。公式Starbound packer/unpackerで本体PAKと任意フォントPAKを往復検証し、相対パス、通常ファイルのSHA-256、型を含む `_metadata` のJSON構造を照合しました。フォントは既存の許可済みファイルのみを独立PAKにし、フォルダーは配布しません。

FU全体の再生成、Starbound実機での表示確認、マルチプレイ切断原因の確認は未実施です。researchTreeの既知のコード差分1件と他MODとのbuilder競合2件もこの修復の対象外です。公開3の過去証拠・成果物は履歴として保持しています。

導入方法は [INSTALL_JA_public4.txt](INSTALL_JA_public4.txt) を参照してください。唯一の導入ZIPは生成レポートの `upload_allowlist` に記録します。
