# v0.2.2 起動・キャラクター選択に関連する Lua／設定監査

## 結論

この監査では、キャラクター作成や既存キャラクター選択時のフリーズを起こす **新しい Lua 無限ループ、API の再帰ラップ、世界生成用 ID・数値の改変を確認できなかった**。ガイド・種族ヘルパーの削除や書き換えを原因修正として推奨する根拠はない。MOD 本体は変更していない。

**ユーザー側のフリーズとの因果関係は未確定。** Starbound 本体の起動、ネイティブ処理の計測、ユーザーの PAK・セーブデータの実行再現はしていない。名前生成と種族／キャラクター UI は別担当の監査範囲であり、本監査の安全判定には含めない。

## ログから確認できる範囲

対象は `upload/starbound(2).log`。NameGenerator、PlayerFactory、SpeciesDatabase、CodexDatabase、ItemDatabase の読込完了が記録されている。LuaException、Fatal Exception、新ガイド／種族ヘルパーの activation ログはない。最後の記録は次の行である。

```text
[20:54:07.151] [Info] UniverseServer: Acquiring universe lock file
```

この行だけでは、ロック取得そのものが停止原因とは断定できない。後続処理の開始やプレイヤーのワールド参加を示す記録もないため、ガイド・種族のパネル内処理が実行された証拠はない。

記録された4件のエラーは既存 `japanese.pak` のパッチ不適用であり、FU_Japanese の Lua 例外ではない。

## Lua の差分と境界

v0.2.2 の Lua は135ファイル。v0.2.1 との比較は **131件がバイト一致、2件追加、2件変更**。

| ファイル | v0.2.1 からの差分 |
|---|---|
| `fujp/guide_display.lua` | 追加。既知ガイドの表示テキストを辞書参照するヘルパー |
| `fujp/species_display.lua` | 追加。既知種族の表示テキストを辞書参照するヘルパー |
| `interface/scripted/xcustomcodex/xcodexui.lua` | ガイドヘルパー読込と表示時の参照を追加 |
| `interface/scripted/statWindow/statWindow.lua` | 種族ヘルパー読込と表示時の参照を追加 |

これら以外の131件には、既存のアイテム build スクリプト、クエスト、NPC、UTF-8 対応、`fujp/lua_display.lua` が含まれる。新たな player／universe 用 Lua 置換や起動フックは追加されていない。新ヘルパーは有限の表を参照し、`while`／`repeat`、自己 `require`、Starbound API の差し替えを行っていない。

既存 `fujp/lua_display.lua` は辞書をキャッシュして値を返す方式で、`root.assetJson` や `widget.setText` などの API 自体をラップしていない。アイテム生成スクリプトの表示フックはツールチップ等を対象とし、元の属性 ID を生成処理に残している。

公式 FU 6.5.8 タグのアイテム build・プレイヤー関連など25ファイル（計192,999バイト）を限定取得した。参照元ハッシュがある22ファイルはすべて、MOD の基準コミットの原文とバイト一致した。少なくともこの22ファイルについて、FU 6.5.8 と基準コミット間のロジック差は確認されない。取得 URL とハッシュは `source_provenance.json` に記録した。

## JSON パッチの走査

14,385ファイルを走査した。操作は `test` 188,109件、`replace` 188,089件、`add` 60件。書込み値は文字列188,095件、整数7件、オブジェクト47件だった。文字列以外の54件はすべて `/gui/` または `/paneLayout/` 下の UI 調整・追加である。

`scripts`、`scriptDelta`、`callback`、`type`、`mode`、`seed`、`weight`、`probability`、`nameGen`、`oldsource` など、監査対象にした制御キーがパス末尾となる書込みは0件。既知のボタン画像 `base` 差し替えは7件あり、すべて UI ボタン用である。監査キーの完全な一覧は `startup_lua_audit.json` に記録した。

これは操作パスの走査であり、あらゆる文字列の意味的な安全性を証明するものではない。特に、配列の中にある名前生成素材や、表示名に見える内部制御文字列は別途意味を確認する必要がある。

| 起動・世界設定ファイル | 変更されたフィールド |
|---|---|
| `universe_server.config.patch` | `clientAssetsMismatchMessage` 1件 |
| `client.config.patch` | `windowTitle` 1件 |
| `celestial.config.patch` | `description` 58件、`regionName` 30件 |
| `system_objects.config.patch` | `description` 11件、`displayName` 11件 |

これらのパッチは、生成確率、軌道範囲、シード、惑星や星系の型 ID、スクリプト参照を書き換えていない。

## 未確定の性能要因

名前生成関連には、`species/feneroxnamegen.config.patch` の12,310バッチ、`celestial/names.config.patch` の10,761バッチなど、多数の位置照合ガードがある。初回読込コストの候補として名前担当に共有したが、ネイティブ実行時間は測定しておらず、フリーズの原因とは断定しない。

## 成果物

- `startup_lua_audit.json`：集計、ログの抜粋、全 Lua ハッシュ、設定変更パス、監査範囲と限界。
- `source_provenance.json`：限定取得した公式原文の URL、ハッシュ、基準との一致結果。
- `save_audit.py`：この読取監査の集計を再生成するスクリプト。
- `fetch_sources.py`：限定した公式原文だけを取得するスクリプト。

広い追加調査はここで終了し、別担当が特定した名前生成の問題に修正版の作業を集約する。
