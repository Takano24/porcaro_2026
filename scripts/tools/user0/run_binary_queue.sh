#!/usr/bin/env bash
# 2値（電磁弁）版の学習キュー。porcaro_2026 のリポジトリ直下で実行する。
#   使い方:  bash scripts/tools/user0/run_binary_queue.sh        （計画を表示して確認 → 実行）
#            bash scripts/tools/user0/run_binary_queue.sh -y     （確認なしで実行）
#   キューの進行ログは logs/user0/binary_queue/（git管理外）に出る。
# 完了済みのランは飛ばし、1本失敗しても次へ進む。止まったら同じコマンドでやり直せば続きから回る。
# コード・設定・RA-L のログは変更しない。出力は logs/user0/ の下だけ。

# ---- 回すもの（上から順に実行。名前 | seed | ft=Model Bから追加学習 / scratch=最初から）----
JOBS=(
  "ft_from_B_seed1|1|ft"
  "scratch_seed1|1|scratch"
  "ft_from_B_seed2|2|ft"
  "scratch_seed2|2|scratch"
  "ft_from_B_seed3|3|ft"
)
NUM_ENVS=2048
TASK=Porcaro-DR-Discrete-user0
EXP=logs/user0/rsl_rl/porcaro_rslrl_lstm_dr_discrete
Q=logs/user0/binary_queue
# -------------------------------------------------------------------------------------------

cd "$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "porcaro_2026 のリポジトリ内で実行してください"; exit 1; }
[ -f scripts/rsl_rl/train.py ] || { echo "scripts/rsl_rl/train.py が見つかりません"; exit 1; }
grep -q init_checkpoint scripts/rsl_rl/train.py || { echo "train.py に --init_checkpoint がありません（git pull していますか）"; exit 1; }
[ -d logs/user0/rsl_rl ] || { echo "logs/user0/rsl_rl/ がありません。先に python data/migrate_old_layout.py を実行してください"; exit 1; }
mkdir -p "$Q"

# ft に使う Model B（先読み0.5 s／LSTM）の最終チェックポイントを、seed ごとに自動で探す
find_ckpt() {  # $1 = seed
  python - "$1" <<'EOF'
import sys
from pathlib import Path
import pandas as pd
from analysis.harness.discover import discover_all_runs
seed = int(sys.argv[1])
df = discover_all_runs("logs/user0/rsl_rl")
d = df[(df["model"] == "B") & (df["seed"] == seed) & (df["status"] == "completed")]
if len(d) != 1:
    print(f"ERROR: Model B seed{seed} の completed が {len(d)} 件（1件であるべき）", file=sys.stderr)
    sys.exit(1)
ck = Path(d.iloc[0]["run_dir"]) / "model_1499.pt"
if not ck.is_file():
    print(f"ERROR: {ck} がありません", file=sys.stderr)
    sys.exit(1)
print(ck.resolve())
EOF
}

declare -A CKPT
echo "== 計画（NUM_ENVS=$NUM_ENVS, task=$TASK）=="
for job in "${JOBS[@]}"; do
  IFS='|' read -r NAME SEED KIND <<< "$job"
  if [ "$KIND" = "ft" ]; then
    CKPT[$NAME]=$(find_ckpt "$SEED") || { echo "$NAME の元チェックポイントを特定できません。上のエラーを確認してください"; exit 1; }
    echo "  $NAME  seed=$SEED  元: ${CKPT[$NAME]}"
  else
    echo "  $NAME  seed=$SEED  最初から"
  fi
done
echo "出力先: $EXP/<日時>_<名前>   ログ: $Q/queue.log"
if [ "$1" != "-y" ]; then
  read -r -p "この内容で開始しますか？ [y/N] " ans
  [ "$ans" = "y" ] || [ "$ans" = "Y" ] || { echo "中止しました"; exit 0; }
fi

for job in "${JOBS[@]}"; do
  IFS='|' read -r NAME SEED KIND <<< "$job"
  if ls "$EXP"/*_"$NAME"/model_1499.pt >/dev/null 2>&1; then
    echo "[$(date '+%F %T')] skip (done): $NAME" | tee -a "$Q/queue.log"; continue
  fi
  ARGS=(--task "$TASK" --agent rsl_rl_lstm_cfg_entry_point
        --lookahead_horizon 0.5 --seed "$SEED" --num_envs "$NUM_ENVS" --headless --run_name "$NAME")
  [ "$KIND" = "ft" ] && ARGS+=(--init_checkpoint "${CKPT[$NAME]}" --init_action_std 0.5)
  echo "[$(date '+%F %T')] start: $NAME" | tee -a "$Q/queue.log"
  START=$(date +%s)
  python scripts/rsl_rl/train.py "${ARGS[@]}" > "$Q/$NAME.out" 2>&1
  RC=$?
  echo "[$(date '+%F %T')] end: $NAME rc=$RC elapsed=$(( ($(date +%s)-START)/60 ))min" | tee -a "$Q/queue.log"
done
echo "[$(date '+%F %T')] queue finished" | tee -a "$Q/queue.log"
