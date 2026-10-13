#!/usr/bin/env bash
# 2値版の ONNX 5本を jetson_project に入れて、manifest に登録し、整合性チェックまで通す。
#   使い方（porcaro_2026 のリポジトリ直下から）:  bash scripts/tools/user0/install_binary_models.sh
#   jetson_project が porcaro_2026 と同じ階層にない場合は JETSON_DIR=<場所> を付ける。
#
# やること:
#   1. logs/user0/binary_onnx/binary_*.onnx（.pt は除く）を ../jetson_project/models/BINARY/ にコピー
#   2. ../jetson_project/models/manifest.yaml の「# BINARY:」雛形（コメント）を、5本分の本物のエントリに置き換え
#   3. python3 tools/check_models.py で、ONNX の入出力が manifest と合っているか確認
# jetson_project の git は触らない（add / commit / branch はしない）。変わるのは models/BINARY/ と manifest.yaml だけ。
set -e
SRC="logs/user0/binary_onnx"
JET="${JETSON_DIR:-../jetson_project}"

[ -d "$SRC" ] || { echo "$SRC がありません。porcaro_2026 のリポジトリ直下で実行してください"; exit 1; }
[ -f "$JET/models/manifest.yaml" ] || { echo "$JET/models/manifest.yaml がありません（JETSON_DIR で場所を指定できます）"; exit 1; }
grep -q "action_mode" "$JET/src/model_registry.py" || { echo "jetson_project に2値対応（action_mode）が入っていません。git pull してください"; exit 1; }

NAMES=(ft_from_B_seed1 ft_from_B_seed2 ft_from_B_seed3 scratch_seed1 scratch_seed2)
for n in "${NAMES[@]}"; do
  [ -f "$SRC/binary_$n.onnx" ] || { echo "$SRC/binary_$n.onnx がありません"; exit 1; }
done

mkdir -p "$JET/models/BINARY"
for n in "${NAMES[@]}"; do cp -v "$SRC/binary_$n.onnx" "$JET/models/BINARY/"; done

python3 - "$JET/models/manifest.yaml" <<'EOF'
import sys
path = sys.argv[1]
lines = open(path, encoding="utf-8").read().split("\n")
if any(l.startswith("BINARY:") for l in lines):
    print("manifest には既に BINARY: があります。何も変更しません"); sys.exit(0)
idx = [i for i, l in enumerate(lines) if l.strip() == "# BINARY:"]
if len(idx) != 1:
    sys.exit("manifest に「# BINARY:」の雛形が1つだけある想定でしたが、見つかりません。手で登録してください")
i0 = idx[0]
rest = [l for l in lines[i0:] if l.strip()]
if not all(l.startswith("#") for l in rest):
    sys.exit("「# BINARY:」より後ろにコメント以外があります。手で登録してください")

def entry(name, seed, src):
    return f"""  {name}:
    file: BINARY/binary_{name}.onnx
    arch: lstm
    lookahead_horizon: 0.5
    frame_stack: 1
    action_mode: binary
    binary_threshold: 0.5
    label: "binary: LSTM, lookahead=0.5s, {src}"
    seed: {seed}
    checkpoint: model_1499.pt"""

block = "BINARY:\n" + "\n".join([
    entry("ft_from_B_seed1", 1, "fine-tuned from RA-L B seed1"),
    entry("ft_from_B_seed2", 2, "fine-tuned from RA-L B seed2"),
    entry("ft_from_B_seed3", 3, "fine-tuned from RA-L B seed3"),
    entry("scratch_seed1", 1, "trained from scratch"),
    entry("scratch_seed2", 2, "trained from scratch"),
]) + "\n"
new = "\n".join(lines[:i0]) + "\n" + block
open(path, "w", encoding="utf-8").write(new)
print("manifest.yaml: BINARY に5本を登録しました")
EOF

cd "$JET"
echo; echo "== check_models（BINARY の分と総合判定）=="
python3 tools/check_models.py | sed -n '/^--- BINARY/,$p'
echo
echo; echo "変更されたファイル:"; git status --short
