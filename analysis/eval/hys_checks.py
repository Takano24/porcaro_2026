"""hys_checks.py — Stage 2 の追加の確認（run_hys_sweep.py の出力を読む。hys_loops.py の補足）

確認すること
  (3) tm_B（ステップ）：各保持区間（rest 以外）の最後 0.5 s の平均手首角（整定角）で、
      ・|sim − 実機|（measured_raw / orificeV2 それぞれ）の中央値と最大
      ・同じヒステリシスで、圧力モデルだけ違う 2 本の差 |orificeV2 − measured_raw|（中央値・最大・5° を超える区間の数）
        と、そのときの圧力の差（DF と F の大きい方）の中央値
      → 圧力のわずかな違いで角度が振られる現象の大きさ
  (4) tm_D（拮抗）の共収縮区間（既定 35.6〜38.6 s。cocon_up0.45 の終わり〜cocon_hold0.45）の手首角の
      平均・peak-to-peak・標準偏差・0.3 s の移動平均を引いた残りの標準偏差（速い揺れ）
実機は hys_loops.load_real（エコーで時刻を合わせ、DT = 5 ms にそろえたもの）

使い方:
  python analysis/eval/hys_checks.py
出力（<hys_dir>/summary/）: checks.md, checks_tm_B.csv, checks_tm_D.csv
"""
from __future__ import annotations

import argparse
import glob
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hys_loops as H  # noqa: E402

DT = H.DT
PLATEAU_S = 0.5     # 整定角を取る区間（各保持区間の最後）
JUMP_DEG = 5.0      # 「振られた」とみなす角度差
HP_N = 61           # 速い揺れを見るときに引く移動平均（61 × 5 ms ≒ 0.3 s）


def load_sim(hys_dir, motion, pm, tag):
    f = os.path.join(hys_dir, f"sim_{motion}__{pm}__{tag}.csv")
    return pd.read_csv(f) if os.path.exists(f) else None


def hys_tags(hys_dir, motion):
    return sorted({H.NAME_RE.search(os.path.basename(f))["hys"]
                   for f in glob.glob(os.path.join(hys_dir, f"sim_{motion}__*__*.csv"))})


def check_steps(hys_dir, jetson, motion="tm_B_steps"):
    real = H.load_real(jetson, motion)
    seg = real.segment.values
    chg = np.r_[0, np.flatnonzero(seg[1:] != seg[:-1]) + 1, len(seg)]
    win = [(chg[i + 1] - int(PLATEAU_S / DT), chg[i + 1]) for i in range(len(chg) - 1) if seg[chg[i]] != "rest"]

    def plateau(x):
        return np.array([x[a:b].mean() for a, b in win])

    th_real = plateau(real.wrist.values)
    rows = []
    for tag in hys_tags(hys_dir, motion):
        r, o = load_sim(hys_dir, motion, "measured_raw", tag), load_sim(hys_dir, motion, "orificeV2", tag)
        if r is None or o is None:
            continue
        th_r, th_o = plateau(r.wrist_angle_deg.values), plateau(o.wrist_angle_deg.values)
        dP = np.maximum(np.abs(plateau(o.P_out_DF.values) - plateau(r.P_out_DF.values)),
                        np.abs(plateau(o.P_out_F.values) - plateau(r.P_out_F.values))) * 1000
        dth = np.abs(th_o - th_r)
        rows.append(dict(hys=tag,
                         err_raw_med=np.median(np.abs(th_r - th_real)), err_raw_max=np.abs(th_r - th_real).max(),
                         err_orif_med=np.median(np.abs(th_o - th_real)), err_orif_max=np.abs(th_o - th_real).max(),
                         dth_med=np.median(dth), dth_max=dth.max(), n_dth_gt5=int((dth > JUMP_DEG).sum()),
                         dP_med_kPa=np.median(dP)))
    return pd.DataFrame(rows).set_index("hys"), len(win)


def check_cocontraction(hys_dir, jetson, t0, t1, motion="tm_D_antagonist"):
    a, b = int(t0 / DT), int(t1 / DT)

    def stats(x):
        x = x[a:b]; hp = x - H.smooth(x, HP_N)
        return dict(mean=x.mean(), p2p=np.ptp(x), std=x.std(), hp_std=hp[HP_N // 2:-(HP_N // 2)].std())

    rows = [dict(pmodel="real", hys="real", **stats(H.load_real(jetson, motion).wrist.values))]
    for pm in ("measured_raw", "orificeV2"):
        for tag in hys_tags(hys_dir, motion):
            s = load_sim(hys_dir, motion, pm, tag)
            if s is not None:
                rows.append(dict(pmodel=pm, hys=tag, **stats(s.wrist_angle_deg.values)))
    return pd.DataFrame(rows).set_index(["pmodel", "hys"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hys_dir", default=os.path.join(H.ROOT, "data/user0/jfps2026/replay/hys"))
    ap.add_argument("--jetson", default=os.environ.get("JETSON_PROJECT", os.path.join(os.path.dirname(H.ROOT), "jetson_project")))
    ap.add_argument("--cocon", type=float, nargs=2, default=(35.6, 38.6), help="tm_D の共収縮区間 [s]")
    a = ap.parse_args()
    out = os.path.join(a.hys_dir, "summary"); os.makedirs(out, exist_ok=True)
    B, nwin = check_steps(a.hys_dir, a.jetson)
    D = check_cocontraction(a.hys_dir, a.jetson, *a.cocon)
    B.to_csv(os.path.join(out, "checks_tm_B.csv"), float_format="%.2f")
    D.to_csv(os.path.join(out, "checks_tm_D.csv"), float_format="%.2f")
    with open(os.path.join(out, "checks.md"), "w", encoding="utf-8") as fo:
        fo.write("# ヒステリシスの追加の確認（hys_checks.py）\n\n")
        fo.write(f"## (3) tm_B：保持区間の整定角（{nwin} 区間、各区間の最後 {PLATEAU_S} s の平均）[deg]\n\n")
        fo.write("- err_raw / err_orif：|sim − 実機|（measured_raw / orificeV2）\n"
                 "- dth：同じヒステリシスで |orificeV2 − measured_raw|。n_dth_gt5 は 5° を超えた区間の数\n"
                 "- dP_med_kPa：そのときの圧力の差（DF と F の大きい方）の中央値\n\n")
        fo.write(H.to_md(B.round(2)) + "\n\n")
        fo.write(f"## (4) tm_D：共収縮区間 {a.cocon[0]}〜{a.cocon[1]} s の手首角 [deg]\n\n")
        fo.write(f"- p2p：peak-to-peak。hp_std：{HP_N * DT:.2f} s の移動平均を引いた残りの標準偏差（速い揺れ）\n\n")
        fo.write(H.to_md(D.round(2)) + "\n")
    print(open(os.path.join(out, "checks.md"), encoding="utf-8").read())


if __name__ == "__main__":
    main()
