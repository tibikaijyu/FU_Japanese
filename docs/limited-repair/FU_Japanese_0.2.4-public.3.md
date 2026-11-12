# FU Japanese 0.2.4-public.3 限定修復版

この版は、導入済み `FU_Japanese.pak` を公式ツールで展開し、表示用Luaヘルパー3件だけを置き換える修復版です。対象は `fujp/lua_display.lua`、`fujp/species_display.lua`、`fujp/guide_display.lua` です。ほかのPAK内ファイルと `_metadata` は入力の内容を保ちます。

Lua 5.3と5.4で、既存互換テスト28ケース・各915 assertion、および種族・ガイド表示テスト249ケース・各639 assertionを実行しました。さらに、3つの表示辞書についてテスト時・入力PAK・生成MODのバイト列が一致することを照合します。Lua監査はMOD内135件のLuaファイルを現在の生成物と結び付けますが、互換テストが135件すべての動作を実行したことを意味しません。

この配布物はFU Japanese全体の再生成・検証を表明しません。ゲームへの導入や起動による表示確認は行っておらず、性能最適化も含みません。公式 `asset_packer` / `asset_unpacker` の全パス・通常ファイルのバイト列・型を含む `_metadata` の往復照合結果は、今回の生成レポートに記録します。

既存構成には未解決の差分が2種類あります。Weapon Stats Workshop item `729726478` はFUの `buildweapon.lua` と `buildunrandweapon.lua` に重なります。また、監査ではFU版 `researchTree.lua` に説明・更新タイミングに関するコード差分が1件見つかりました。いずれも今回変更せず、実行時の影響や原因は確認していません。

導入手順は [INSTALL_JA.txt](INSTALL_JA.txt) を参照してください。このZIPにはFU JapaneseのPAKだけを含み、任意のフォントPAKは含みません。展開済みMODフォルダーとPAKを同時に導入しないでください。
