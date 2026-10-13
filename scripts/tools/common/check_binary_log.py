"""シミュレーションの simulation_log.csv が、ちゃんと2値で動いているかを確認する。

使い方（リポジトリ直下から。ログのフォルダを引数で渡す）:
    python scripts/tools/common/check_binary_log.py data/<user>/<venue>/eval/<実験>

各ログについて次を出す:
  - P_cmd_DF/F/G が 0 と Pmax の2値だけか（Pmax はログの最大値。0.6 MPa のはず）
  - ON の割合（各チャンネル）
  - 切替回数/秒（ON<->OFF の変化。大きすぎる＝弁がバタつく）
  - 打撃数の概算: force_z が 1 N を上向きに超えた回数 と、目標(target_force)が 10 N を超えた山の数
    （概算。正式な成功率は analysis/eval/aggregate_sim_strikes.py の 1N 判定で出す）
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

if len(sys.argv) < 2:
    sys.exit("使い方: python scripts/tools/common/check_binary_log.py <simulation_log.csv を含むフォルダ>")
root = Path(sys.argv[1])
logs = sorted(root.rglob("simulation_log.csv"))
if not logs:
    sys.exit(f"{root} に simulation_log.csv がありません")


def rising(x, thr):
    a = np.asarray(x) > thr
    return int(np.sum(a[1:] & ~a[:-1]))


rows = []
for p in logs:
    df = pd.read_csv(p)
    t = df["time_s"].to_numpy()
    dur = float(t[-1] - t[0]) if len(t) > 1 else float("nan")
    cmd = df[["P_cmd_DF", "P_cmd_F", "P_cmd_G"]].to_numpy()
    pmax = float(np.nanmax(cmd))
    tol = 1e-4 * max(pmax, 1e-9)
    is_bin = bool(np.all((np.abs(cmd) < tol) | (np.abs(cmd - pmax) < tol)))
    n_vals = len(np.unique(np.round(cmd, 5)))
    on = (cmd > pmax / 2).mean(axis=0)
    sw = (np.abs(np.diff((cmd > pmax / 2).astype(int), axis=0)).sum(axis=0)) / dur if dur > 0 else np.zeros(3)
    rel = p.relative_to(root)
    rows.append({
        "run/条件": str(rel.parent.parent.parent.name[:30] + "/" + rel.parent.name),
        "Pmax": round(pmax, 3),
        "2値のみ": "OK" if is_bin else f"NG({n_vals}値)",
        "ON率 DF/F/G": "/".join(f"{v:.2f}" for v in on),
        "切替/s DF/F/G": "/".join(f"{v:.1f}" for v in sw),
        "打撃(実)": rising(df["force_z"], 1.0),
        "目標": rising(df["target_force"], 10.0),
        "最大力N": round(float(df["force_z"].max()), 1),
        "秒": round(dur, 1),
    })

pd.set_option("display.width", 250, "display.max_colwidth", 60)
print(pd.DataFrame(rows).to_string(index=False))
