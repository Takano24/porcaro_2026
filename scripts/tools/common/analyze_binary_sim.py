"""2値（電磁弁）版のシミュレーション再生ログから、表と図を作る。

使い方（porcaro_2026 のリポジトリ直下で。入力と出力のフォルダは必ず指定する）:
    python scripts/tools/common/analyze_binary_sim.py --root data/<user>/<venue>/eval/<実験> \
                                                      --out  data/<user>/<venue>/report
  例（2026-10 の user0 の2値実験）:
    python scripts/tools/common/analyze_binary_sim.py --root data/user0/binary2026/eval/sim_check \
                                                      --out  data/user0/binary2026/report

入力: <root>/<ラン>/model_1499/<曲>_trial0/simulation_log.csv   （run_sim_check.sh の出力）
出力: <out>/
    summary_by_condition.csv / .md   ラン x 曲ごとの表（成功率・誤差・力・2値チェック・バタつき）
    strikes_all.csv                  打点ごとの結果（目標時刻・実打撃時刻・誤差・力・成功）
    fig_success.png / .pdf           成功率（±30 ms）のラン別・曲別の棒グラフ
    fig_timing.png / .pdf            タイミング誤差の分布
    timeseries/<ラン>__<曲>.png      目標・接触力と、3チャンネルの圧力指令（2値）の時系列

打撃の判定は analysis/harness/strike_extract.py（RA-L と同じ。1 N 以上の山を打撃とみなし、
目標時刻から ±30 ms 以内なら成功）をそのまま使う。GPU は使わない。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.signal import find_peaks  # noqa: E402

sys.path.insert(0, str(Path.cwd()))
try:
    from analysis.harness.strike_extract import extract_strikes
except ImportError:
    sys.exit("analysis.harness.strike_extract が読めません。porcaro_2026 のリポジトリ直下で実行してください。")

TARGET_REF = 20.0     # 目標の打撃力 [N]
MIN_FRAC = 0.05       # 0.05 x 20 N = 1 N 以上を打撃とみなす（RA-L と同じ）
TOL_MS = 30.0         # 成功とみなす時間誤差 [ms]
CH = ["P_cmd_DF", "P_cmd_F", "P_cmd_G"]
COL = {"ft": "#0072B2", "scratch": "#D55E00", "other": "#666666"}   # Okabe-Ito


def parse_run(dirname: str) -> dict:
    m = re.match(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_(.+)$", dirname)
    label = m.group(1) if m else dirname
    seed = re.search(r"seed(\d+)", label)
    kind = "ft" if label.startswith("ft_") else "scratch" if label.startswith("scratch") else "other"
    short = {"ft": "ft(B)", "scratch": "scratch", "other": label}[kind] + (f" s{seed.group(1)}" if seed else "")
    return dict(run=label, kind=kind, short=short)


def episodes(df: pd.DataFrame):
    t = df["time_s"].to_numpy(float)
    b = np.r_[0, np.nonzero(np.diff(t) < 0)[0] + 1, len(df)]
    return [df.iloc[a:c].reset_index(drop=True) for a, c in zip(b[:-1], b[1:]) if c - a > 10]


def analyze_one(p: Path):
    run = parse_run(p.parents[2].name)
    cond = re.sub(r"_trial\d+$", "", p.parent.name)
    bpm_m = re.search(r"bpm(\d+)", cond)
    bpm = float(bpm_m.group(1)) if bpm_m else None
    df = pd.read_csv(p)
    if bpm is None:
        bpm = float(df["target_bpm"].median())

    sts, extra, n_act = [], 0, 0
    for ep in episodes(df):
        st = extract_strikes(ep, bpm=bpm, target_ref=TARGET_REF, tol_ms=TOL_MS, min_strike_frac=MIN_FRAC)
        sts.append(st)
        dt = float(np.median(np.diff(ep["time_s"])))
        dist = max(1, int(round(0.3 * (15.0 / bpm) / dt)))
        pk, _ = find_peaks(ep["force_z"].to_numpy(float), height=MIN_FRAC * TARGET_REF, distance=dist)
        n_act += len(pk)
        extra += len(pk) - int(st["peak_time"].notna().sum())
    st = pd.concat(sts, ignore_index=True)
    st.insert(0, "cond", cond)
    st.insert(0, "run", run["run"])
    hit = st[st["peak_force"] >= MIN_FRAC * TARGET_REF]

    # 2値チェックとバタつき
    cmd = df[CH].to_numpy(float)
    pmax = float(np.nanmax(cmd))
    tol = 1e-4 * max(pmax, 1e-9)
    is_bin = bool(np.all((np.abs(cmd) < tol) | (np.abs(cmd - pmax) < tol)))
    on = cmd > pmax / 2
    dur = float(df["time_s"].iloc[-1] - df["time_s"].iloc[0])
    dt = float(np.median(np.diff(df["time_s"])))
    sw = np.abs(np.diff(on.astype(int), axis=0)).sum(axis=0)
    # 1 制御ステップだけ ON/OFF して戻る「瞬間切替」の数（弁の応答より短い切替）
    blip = int(sum(((np.diff(on[:, k].astype(int)) != 0)[1:] & (np.diff(on[:, k].astype(int)) != 0)[:-1]).sum()
                   for k in range(3)))
    row = dict(
        run=run["run"], kind=run["kind"], short=run["short"], cond=cond, bpm=bpm,
        n_targets=len(st), success_rate=float(st["success"].mean()),
        n_missed=int((st["peak_force"] < MIN_FRAC * TARGET_REF).sum()),
        extra_peaks=int(extra),
        abs_err_ms=float(hit["timing_err_ms"].abs().mean()) if len(hit) else np.nan,
        err_ms_mean=float(hit["timing_err_ms"].mean()) if len(hit) else np.nan,
        peak_force_mean=float(st["peak_force"].mean()), peak_force_max=float(df["force_z"].max()),
        binary_only=is_bin, p_max=round(pmax, 4),
        on_DF=on[:, 0].mean(), on_F=on[:, 1].mean(), on_G=on[:, 2].mean(),
        sw_per_s_DF=sw[0] / dur, sw_per_s_F=sw[1] / dur, sw_per_s_G=sw[2] / dur,
        one_step_blips=blip, duration_s=dur, control_dt_ms=dt * 1000,
    )
    return row, st, df


def md_table(df: pd.DataFrame) -> str:
    h = "| " + " | ".join(df.columns) + " |\n|" + "---|" * len(df.columns) + "\n"
    return h + "".join("| " + " | ".join(str(v) for v in r) + " |\n" for r in df.itertuples(index=False))


def timeseries(df, st, run, cond, out: Path):
    t = df["time_s"].to_numpy(float)
    pmax = float(np.nanmax(df[CH].to_numpy(float)))
    fig, ax = plt.subplots(4, 1, figsize=(10, 6.5), sharex=True, gridspec_kw=dict(height_ratios=[2.2, 1, 1, 1]))
    ax[0].fill_between(t, df["target_force"], color="#bbbbbb", label="target")
    ax[0].plot(t, df["force_z"], color="#0072B2", lw=1, label="contact force")
    m = st[st["peak_time"].notna()]
    ax[0].scatter(m["peak_time"], m["peak_force"], s=14, zorder=3,
                  c=np.where(m["success"], "#009E73", "#D55E00"))
    ax[0].set_ylabel("force [N]")
    ax[0].legend(loc="upper right", fontsize=8, ncol=2)
    ax[0].set_title(f"{run['run']}  /  {cond}   (green: within ±{TOL_MS:.0f} ms, red: outside)", fontsize=10)
    for k, name in enumerate(CH):
        ax[k + 1].step(t, df[name], where="post", color="#333333", lw=1)
        ax[k + 1].set_ylim(-0.05 * pmax, 1.15 * pmax)
        ax[k + 1].set_yticks([0, pmax])
        ax[k + 1].set_ylabel(f"{name[2:]}\n[MPa]", fontsize=8)
    ax[-1].set_xlabel("time [s]")
    for a in ax:
        a.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="simulation_log.csv を含むフォルダ")
    ap.add_argument("--out", required=True, help="表と図の出力先（data/<user>/<venue>/ の下）")
    a = ap.parse_args()
    root, out = Path(a.root), Path(a.out)
    logs = sorted(root.rglob("simulation_log.csv"))
    if not logs:
        sys.exit(f"{root} に simulation_log.csv がありません")
    (out / "timeseries").mkdir(parents=True, exist_ok=True)

    rows, all_st = [], []
    for p in logs:
        row, st, df = analyze_one(p)
        rows.append(row)
        all_st.append(st)
        timeseries(df, st[st["cond"] == row["cond"]], parse_run(p.parents[2].name), row["cond"],
                   out / "timeseries" / f"{row['run']}__{row['cond']}.png")
    S = pd.DataFrame(rows).sort_values(["cond", "kind", "run"]).reset_index(drop=True)
    ST = pd.concat(all_st, ignore_index=True)
    S.to_csv(out / "summary_by_condition.csv", index=False)
    ST.to_csv(out / "strikes_all.csv", index=False)

    view = S[["short", "cond", "n_targets", "success_rate", "n_missed", "extra_peaks", "abs_err_ms",
              "peak_force_mean", "binary_only", "sw_per_s_DF", "sw_per_s_F", "sw_per_s_G", "one_step_blips"]].copy()
    for c in ["success_rate"]:
        view[c] = (view[c] * 100).round(1).astype(str) + "%"
    for c in ["abs_err_ms", "peak_force_mean", "sw_per_s_DF", "sw_per_s_F", "sw_per_s_G"]:
        view[c] = view[c].round(1)
    (out / "summary_by_condition.md").write_text(md_table(view))

    conds = list(S["cond"].unique())
    # --- 成功率 ---
    fig, axs = plt.subplots(1, len(conds), figsize=(4.6 * len(conds), 3.6), sharey=True, squeeze=False)
    for ax, c in zip(axs[0], conds):
        d = S[S["cond"] == c].sort_values(["kind", "short"])
        ax.bar(range(len(d)), d["success_rate"] * 100, color=[COL[k] for k in d["kind"]])
        for i, v in enumerate(d["success_rate"] * 100):
            ax.text(i, v + 1, f"{v:.0f}", ha="center", fontsize=8)
        ax.set_xticks(range(len(d)))
        ax.set_xticklabels(d["short"], rotation=40, ha="right", fontsize=8)
        ax.set_title(c, fontsize=9)
        ax.set_ylim(0, 105)
        ax.grid(axis="y", alpha=0.25)
    axs[0][0].set_ylabel(f"success rate (±{TOL_MS:.0f} ms) [%]")
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(color=COL["ft"], label="fine-tuned from continuous Model B"),
                        Patch(color=COL["scratch"], label="binary, from scratch")],
               loc="lower center", ncol=2, fontsize=8, frameon=False)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    for ext in ("png", "pdf"):
        fig.savefig(out / f"fig_success.{ext}", dpi=160)
    plt.close(fig)

    # --- タイミング誤差 ---
    fig, axs = plt.subplots(1, len(conds), figsize=(4.6 * len(conds), 3.6), sharey=True, squeeze=False)
    rng = np.random.default_rng(0)
    for ax, c in zip(axs[0], conds):
        d = S[S["cond"] == c].sort_values(["kind", "short"])
        for i, r in enumerate(d.itertuples()):
            e = ST[(ST["run"] == r.run) & (ST["cond"] == c)]["timing_err_ms"].dropna()
            ax.scatter(i + rng.uniform(-0.15, 0.15, len(e)), e, s=10, color=COL[r.kind], alpha=0.8)
        ax.axhspan(-TOL_MS, TOL_MS, color="#009E73", alpha=0.12)
        ax.axhline(0, color="k", lw=0.6)
        ax.set_xticks(range(len(d)))
        ax.set_xticklabels(d["short"], rotation=40, ha="right", fontsize=8)
        ax.set_title(c, fontsize=9)
        ax.grid(axis="y", alpha=0.25)
    axs[0][0].set_ylabel("timing error [ms]  (+: late)")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(out / f"fig_timing.{ext}", dpi=160)
    plt.close(fig)

    print(md_table(view))
    print(f"\n2値のみ: {int(S['binary_only'].sum())}/{len(S)} 条件")
    print(f"出力先: {out}/  （summary_by_condition.csv/.md, strikes_all.csv, fig_success, fig_timing, timeseries/）")


if __name__ == "__main__":
    main()
