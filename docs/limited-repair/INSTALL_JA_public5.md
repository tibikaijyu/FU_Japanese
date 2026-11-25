# FU Japanese 0.2.4-public.5

FU 6.5.8向けの非公式日本語化MODです。生成AIを用いた実装・翻訳を含みます。
実ゲームの描画確認前のPre-releaseです。

狂気の文字演出で日本語を1バイトずつ送っていた処理を、UTF-8の文字単位へ修正しました。
public.4の種族・ガイド表示修正を含み、public.4から変わるゲーム用アセットは
`stats/typer_particle.lua` の追加1件です。ステータス効果やセーブの値は変更しません。

1. Starboundを完全に終了します。
2. 旧 `Starbound/mods/FU_Japanese` フォルダと `Starbound/mods/FU_Japanese.pak` をmodsの外へ退避します。
3. ZIP内の `mods/FU_Japanese.pak` を `Starbound/mods/` にコピーします。
4. 既存の日本語フォントMODを使用します。必要な場合だけ `optional/FU_Japanese_Font.pak` をmodsへ追加します。
5. 同じ惑星で再開し、新しいログで `Invalid UTF-8 code unit sequence` が出ないことを確認します。

`SHA256SUMS.txt` はZIP内部ファイルの照合用です。Release本文にあるSHA-256はダウンロードしたZIP全体に対して照合してください。
元へ戻す場合はゲーム終了後に退避した旧MODを復元します。

Lua 5.3/5.4で各172ケース・987粒子、既存表示ヘルパーのcore 8ケースと追加262ケースを検証しています。
公式packer/unpackerで本体と任意フォントの相対パス・通常ファイルのバイト列・型付きmetadataを照合しています。
実ゲーム、以前のマルチ切断、Discord・Steam連携エラーの解消は未確認です。
この配布物にゲーム・Workshop・セーブへの自動配置機能はありません。

原作はSayterおよびFrackin' Universeの貢献者です。改変LuaとFU由来の文章・翻訳はCC BY 4.0です。
出典と改変内容は `FU_COMPATIBILITY.md`、帰属とライセンス本文は `LICENSES/FU_Japanese/` を参照してください。
任意フォントの著作権表示とM+ライセンスは `LICENSES/FU_Japanese_Font/` にあります。

- 原作：https://github.com/sayterdarkwynd/FrackinUniverse
- ソースと配布：https://github.com/tibikaijyu/FU_Japanese/releases/tag/v0.2.4-public.5

展開済みMODソース・開発用ZIPは配布しません。ソースはGitリポジトリで管理します。
