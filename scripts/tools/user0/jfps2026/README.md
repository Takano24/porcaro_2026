# scripts/tools/user0/jfps2026/ — JFPS 2026秋季（開ループ再生と圧力モデル）

実機に送ったのと同じ圧力指令を sim に開ループで流し、圧力と関節角を実機と比べるためのもの。
出力は `data/user0/jfps2026/replay/`。3本は互いを同じフォルダから import するので、動かすときは3本まとめて動かす。

| ファイル | 内容 |
|---|---|
| `replay_open_loop.py` | 圧力指令 CSV を sim に開ループで流す（Isaac Lab が要る）。圧力モデルは `--pmodel` で切り替え |
| `itv_models.py` | ITV（電空レギュレータ）の小振幅・高周波のしきい値を入れた圧力チャネル（`shaped` / `pilot` / `pilot_leak`） |
| `real_log.py` | jetson_project の実機ログの読み込みと、指令の時間軸への位置合わせ（numpy / pandas だけ） |

`analysis/eval/` の `compare_replay.py`、`hys_loops.py`、`run_hys_sweep.py` は、このフォルダを import の検索先に足して
`real_log.py` を使い、`run_hys_sweep.py` は `replay_open_loop.py` を呼び出す。

使い方（コマンドの例と `--pmodel` の一覧）は `replay_open_loop.py` の先頭のコメントにある。Isaac Lab の環境で、リポジトリ直下から実行する。
