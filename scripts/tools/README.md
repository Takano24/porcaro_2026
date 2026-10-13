# scripts/tools/ — 補助ツール（学習スクリプト以外）

学習・再生の本体（`scripts/rsl_rl/`）以外の、実験を回す・確認する・集計するための小さなツールを置く。

```text
scripts/tools/
 ├── common/      誰でも使えるツール（共有。変更は後方互換で、CODEOWNERS のレビュー対象）
 └── userN/       各自のツール（自分のフォルダだけを触る。レビュー不要）
```

## ルール

- **使い回せるものは `common/`、自分の実験に固有のもの（タスク名・チェックポイント・出力先を決め打ちしているもの）は `userN/`。**
  `userN/` のツールを他の人が使うときは、自分の `userN/` にコピーして書き換える。
- **`common/` のツールは user を決め打ちしない。** 入力・出力のフォルダは引数で必ず受け取る（既定値を `data/user0/...` にしない）。
- **出力をここに置かない。** データは `data/<user>/<venue>/`、実行時のログや一時ファイルは `logs/<user>/`（git管理外）へ。
- 実行はリポジトリ直下から（例: `python scripts/tools/common/check_binary_log.py <フォルダ>`）。
- `userN/` は必要になったときに自分で作る。

## いまあるツール

| ファイル | 内容 |
|---|---|
| `common/check_binary_log.py` | sim の `simulation_log.csv` の圧力指令が 0 / Pmax の2値だけか、ON率・切替回数を確認する |
| `common/analyze_binary_sim.py` | sim の再生ログを RA-L と同じ判定（1 N・±30 ms）で集計し、表と図を出す |
| `user0/` | 2値（電磁弁）方策の学習から実機登録まで（手順は `user0/README.md`） |
