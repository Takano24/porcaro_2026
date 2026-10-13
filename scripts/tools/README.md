# scripts/tools/ — 補助ツール（学習スクリプト以外）

学習・再生の本体（`scripts/rsl_rl/`）以外の、実験を回す・確認する・集計するための小さなツールを置く。

```text
scripts/tools/
 ├── common/          誰でも使えるツール（共有。変更は後方互換で、CODEOWNERS のレビュー対象）
 └── userN/           各自のツール（自分のフォルダだけを触る。レビュー不要）
     └── <目的>/       実験・学会ごと。名前は data/userN/<目的>/ と同じにする（例: binary2026, jfps2026）
```

## ルール

- **使い回せるものは `common/`、自分の実験に固有のもの（タスク名・チェックポイント・出力先を決め打ちしているもの）は `userN/`。**
  `userN/` の下は目的ごとにフォルダを分け、名前を `data/userN/<目的>/` と揃える（そのツールが作るデータの置き場所と同じ名前）。
  `userN/` のツールを他の人が使うときは、自分の `userN/<目的>/` にコピーして書き換える。
- **`common/` のツールは user を決め打ちしない。** 入力・出力のフォルダは引数で必ず受け取る（既定値を `data/user0/...` にしない）。
- **出力をここに置かない。** データは `data/<user>/<venue>/`、実行時のログや一時ファイルは `logs/<user>/`（git管理外）へ。
- 実行はリポジトリ直下から（例: `python scripts/tools/common/check_binary_log.py <フォルダ>`）。
- `userN/` は必要になったときに自分で作る。

## いまあるツール

| ファイル | 内容 |
|---|---|
| `common/check_binary_log.py` | sim の `simulation_log.csv` の圧力指令が 0 / Pmax の2値だけか、ON率・切替回数を確認する |
| `common/analyze_binary_sim.py` | sim の再生ログを RA-L と同じ判定（1 N・±30 ms）で集計し、表と図を出す |
| `user0/binary2026/` | 2値（電磁弁）方策の学習から実機登録まで（手順は `user0/binary2026/README.md`） |
| `user0/jfps2026/` | JFPS 2026秋季の開ループ再生（実機の圧力指令を sim に流す）と、ITV の圧力モデル、実機ログの読み込み（`user0/jfps2026/README.md`） |
