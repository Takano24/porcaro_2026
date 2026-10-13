#!/usr/bin/env bash
# 2値版5本を、シミュレーションで1環境・方策の平均出力（ノイズなし）で再生してログを残す。
#   使い方（どこから実行してもよい。自分でリポジトリ直下に移動する）:
#       bash scripts/tools/user0/binary2026/run_sim_check.sh
#   コンソール出力は logs/user0/binary_queue/（git管理外）に出る。
# 出力: data/user0/binary2026/eval/sim_check/<ラン>/model_1499/<曲>_trial0/simulation_log.csv
# 完了済み（simulation_log.csv がある条件）は飛ばす。

# ---- 再生する曲（足したいときは行を足す）----
MIDIS=(
  data/common/midi/test_single4_bpm60.mid
  data/common/midi/test_single8_bpm120.mid
)
TASK=Porcaro-DR-Discrete-user0
EXP=logs/user0/rsl_rl/porcaro_rslrl_lstm_dr_discrete
OUT=data/user0/binary2026/eval/sim_check
# --------------------------------------------

cd "$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "porcaro_2026 のリポジトリ内で実行してください"; exit 1; }
[ -f scripts/rsl_rl/play_sim_midi.py ] || { echo "scripts/rsl_rl/play_sim_midi.py がありません"; exit 1; }
mkdir -p "$OUT" logs/user0/binary_queue

for ckpt in "$EXP"/*/model_1499.pt; do
  [ -f "$ckpt" ] || { echo "model_1499.pt が見つかりません"; exit 1; }
  run=$(basename "$(dirname "$ckpt")")
  for midi in "${MIDIS[@]}"; do
    stem=$(basename "$midi" .mid)
    if [ -f "$OUT/$run/model_1499/${stem}_trial0/simulation_log.csv" ]; then
      echo "skip (done): $run $stem"; continue
    fi
    echo "[$(date '+%F %T')] play: $run $stem"
    python scripts/rsl_rl/play_sim_midi.py \
      --task "$TASK" --agent rsl_rl_lstm_cfg_entry_point \
      --checkpoint="$ckpt" --lookahead_horizon 0.5 \
      --midi "$midi" --trial 0 --seed 1 \
      --eval_logs_root "$OUT" --headless \
      > "logs/user0/binary_queue/play_${run}_${stem}.out" 2>&1 \
      || echo "  失敗: logs/user0/binary_queue/play_${run}_${stem}.out を確認"
  done
done
echo "done. 次: python scripts/tools/common/check_binary_log.py $OUT"
echo "      python scripts/tools/common/analyze_binary_sim.py --root $OUT --out data/user0/binary2026/report"
