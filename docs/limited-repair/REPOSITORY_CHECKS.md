# 限定修復版のリポジトリ検査

## 0.2.4-public.4の現行検査

public.4はpublic.3の固定PAKから種族・ガイド表示ヘルパー2件だけを更新します。public.3の記録は過去の承認として保持し、現行の承認は次の別recordに結び付けます。

- `source/reports/limited_repair_024_public4.json` はpublic.3入力PAK、current helper hashes、2件の厳密な変更範囲、main/font PAKの公式往復、ZIP一件のallowlist、同梱資料とfontのhashを記録します。
- `source/reports/limited_helper_tests_024_public4.json` は現入力状態・2 helper・テストharnessへ結び付いた30単体テストと、Lua 5.3/5.4各core 8ケース/142 assertions、表示262ケース/785 assertionsの結果を記録します。
- `check_public_repo.py --release-profile limited-repair` は旧MOD manifestへpublic.3 approved helper hashes、続けてpublic.4の2 helper hashesを適用し、追加・未承認のMOD変更を拒否します。public.3記録自体は書き換えません。

```sh
python source/tools/check_public_repo.py --release-profile limited-repair
python source/tools/run_limited_helper_tests.py --lua-backend auto --report-output .local/public4-helper-tests.json
```

ローカルでLupaを読み込めない環境では `--lua-backend ctypes` を明示できます。CIの通常経路はLupaを使い、reportには実backendとバイナリhashを記録します。公式PAK生成・実機起動・全体再生成の証拠とは区別します。

0.2.4-public.3は、固定した導入PAKへ表示ヘルパー3件だけを反映する修復です。過去の全体検証記録を新しいソースへ付け替えず、今回の証跡を別ファイルに保存します。

- `source/reports/mod_sha256.json` は旧版の基準として保持します。今回の3件以外はこの基準と一致しなければ検査を通しません。
- `source/reports/limited_repair_024_public3.json` は入力PAK、修正3件、テスト時の辞書、公式PAK往復、導入ZIPのハッシュを記録します。
- `source/reports/limited_helper_tests_024_public3.json` は現在のMOD・ソース入力に結び付いた検査です。配布・生成・証跡の25テストと、core例外境界8ケース・種族/ガイド249ケースをLua 5.3/5.4で実行した結果を記録します。

```sh
python source/tools/check_public_repo.py --release-profile limited-repair
python source/tools/run_limited_helper_tests.py --report-output .local/ci-limited-helper-tests.json
```

CIは上記に加え、既存のPAK梱包・公開ファイル・種族表示・キャラクター名フィクスチャの回帰検査を実行します。Windowsの公式ツールを模擬したテストから配布物を生成しません。

旧 `check_public_repo.py` の全体検査は既定の `--release-profile full` として維持します。旧版の入力と合わない現在のソースでは失敗するため、今回の配布に全体検証済みという意味を与えません。

検査・ソースを変更した場合は実テストを実行し、公式生成レポートとの対応を確認してから限定修復記録と公開ファイルのチェックサムを更新します。ハッシュだけを付け替えてテスト成功を再利用しません。
