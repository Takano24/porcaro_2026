# scripts/tools/user0/binary2026/ — 2値（電磁弁）方策の学習から実機登録まで（2026-10）

タスク `Porcaro-DR-Discrete-user0`（LSTM・先読み 0.5 s）で5本学習し、sim で確認して、jetson_project に登録するまで。
データの置き場所は `data/user0/binary2026/`。実機側（jetson_project）の手順と結果は、別の資料にまとめてある。

実行はすべて porcaro_2026 のリポジトリ直下から。jetson_project は同じ階層にある前提。

| 順 | コマンド | 内容 |
|---|---|---|
| 1 | `bash scripts/tools/user0/binary2026/run_binary_queue.sh` | 5本を順に学習（2048環境、1本約4.8時間）。RA-L の Model B（seed 1〜3）から追加学習3本、最初から2本。元のチェックポイントは自動で探し、完了済みは飛ばす。tmux の中で回す |
| 2 | `bash scripts/tools/user0/binary2026/run_sim_check.sh` | 5本を2曲（`test_single4_bpm60`、`test_single8_bpm120`）で sim 再生。出力は `data/user0/binary2026/eval/sim_check/` |
| 3 | `python scripts/tools/common/analyze_binary_sim.py --root data/user0/binary2026/eval/sim_check --out data/user0/binary2026/report` | sim の集計（表と図） |
| 4 | `scripts/rsl_rl/export_onnx.py` を5本分（下） | ONNX を `logs/user0/binary_onnx/` に書き出す |
| 5 | `bash scripts/tools/user0/binary2026/install_binary_models.sh` | ONNX を `../jetson_project/models/BINARY/` にコピーし、`models/manifest.yaml` に登録して `check_models.py` を流す |

手順4:

```bash
for ckpt in logs/user0/rsl_rl/porcaro_rslrl_lstm_dr_discrete/*/model_1499.pt; do
  run=$(basename "$(dirname "$ckpt")")
  python scripts/rsl_rl/export_onnx.py --task Porcaro-DR-Discrete-user0 --agent rsl_rl_lstm_cfg_entry_point \
    --checkpoint="$ckpt" --lookahead_horizon 0.5 --headless \
    --out_dir logs/user0/binary_onnx --out_name "binary_${run#*_*_}"
done
```

手順5の `check_models.py` には onnxruntime が要る。Isaac Lab の環境に入っていなければ、別の conda 環境で
`pip install onnxruntime numpy pandas pyserial pyyaml` してから `../jetson_project` で `python3 tools/check_models.py` を流す。

他の user が同じことをするときは、このフォルダを自分の `scripts/tools/userN/<目的>/` にコピーし、
タスク名（`...-user0`）、`logs/user0/`、`data/user0/` を書き換える。
