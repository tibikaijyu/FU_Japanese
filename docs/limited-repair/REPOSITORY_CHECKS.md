# 限定修復版のリポジトリ検査

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
