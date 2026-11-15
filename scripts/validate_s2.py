# AI-assisted: generated with Claude (Anthropic)
"""Adım 50: Seviye 2 bölgelerinde uyumlu serinin doğrulaması (Türkiye karşılaştırmalı).

Çıktı: docs/s2_before_after.png, docs/validation_s2_stats.json
Kullanım: python scripts/validate_s2.py                                      (Seviye 2)
          python scripts/validate_s2.py --tag s3 se_australia california amazon_arc   (biyom kutuları, adım 81)
"""
import argparse
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import DATA_PROCESSED, DOCS, load_region

C_V, C_RAW, INK, INK2, MUTED, GRID, BG = "#eb6834", "#898781", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="s2")
    ap.add_argument("regions", nargs="*")
    a = ap.parse_args()
    REGIONS = (a.regions or ["balkanlar", "kafkasya", "dogu_akdeniz"]) + ["turkiye"]
    plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG, "axes.edgecolor": "#c3c2b7",
                         "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.7, "axes.axisbelow": True,
                         "font.size": 10, "axes.titlesize": 11.5, "axes.titleweight": "bold", "axes.titlelocation": "left",
                         "legend.frameon": False, "figure.dpi": 150})
    S, yrs = {}, {}
    for r in REGIONS:
        suffix = "" if r == "turkiye" else f"_{r}"
        mon = pd.read_csv(DATA_PROCESSED / r / "harmonized_monthly.csv")
        coef = json.loads((DATA_PROCESSED / r / "coefficients.json").read_text(encoding="utf-8"))
        hs = json.loads((DOCS / f"harmonize_stats{suffix}.json").read_text(encoding="utf-8"))
        c = {int(k): v for k, v in coef["modis_to_snpp"].items()}
        mon["y"], mon["mo"] = mon.ym.str[:4].astype(int), mon.ym.str[5:].astype(int)
        mon["raw"] = np.where(mon.src == "M", mon.m, mon.v)
        mon["est"] = mon.m * mon.mo.map(c)
        yr = mon[mon.y.between(2003, 2025)].groupby("y").agg(h=("h", "sum"), h_lo=("h_lo", "sum"), h_hi=("h_hi", "sum"), raw=("raw", "sum"),
                                                             m=("m", "sum"), v=("v", "sum"), est=("est", "sum"))
        yrs[r] = yr
        pre, post = yr.loc[2003:2011], yr.loc[2012:2025]
        ov = mon[(mon.ym >= "2012-02") & (mon.y <= 2025)]
        chosen = [k for k in hs["models_leave_one_year_out"] if k.startswith("seçilen")] or ["B ay"]
        m = hs["models_leave_one_year_out"][chosen[0]]
        S[r] = {
            "method": hs.get("method"), "coefficients": c,
            "cv_month_weighted_abs_err_pct": m["month_weighted_abs_err_pct"], "cv_year_mean_abs_err_pct": m["year_mean_abs_err_pct"],
            "cv_year_max_abs_err_pct": m["year_max_abs_err_pct"], "test_2023_2025_total_err_pct": m["test_2023_2025_total_err_pct"],
            "test_2023_2025_year_err_pct": m["test_2023_2025_year_err_pct"],
            "uncertainty_p16_p84": [hs["uncertainty"]["p16"], hs["uncertainty"]["p84"]],
            "uncertainty_p05_p95": [hs["uncertainty"]["p05"], hs["uncertainty"]["p95"]],
            "level_effect": hs["level_effect"],
            "junction_2012": hs["cv_year_actual_vs_predicted"]["2012"],
            "level_ratio_after_over_before": {"raw_combined": round(float(post.raw.median() / pre.raw.median()), 2),
                                              "harmonized": round(float(post.h.median() / pre.h.median()), 2),
                                              "modis_alone": round(float(post.m.median() / pre.m.median()), 2)},
            "change_2011_to_2012_pct": {"modis_alone": round(float((yr.m[2012] / yr.m[2011] - 1) * 100), 1),
                                        "harmonized": round(float((yr.h[2012] / yr.h[2011] - 1) * 100), 1),
                                        "raw_combined": round(float((yr.raw[2012] / yr.raw[2011] - 1) * 100), 1)},
            "overlap_monthly_corr_estimate_vs_viirs": round(float(ov.est.corr(ov.v)), 3),
            "out_of_range_months": [x["month"] for x in hs["out_of_range_months"]],
            "yearly_h": {int(y): round(float(v)) for y, v in yr.h.items()},
            "modis_2002_2011_total": int(mon[mon.src == "M"].m.sum()),
        }
    (DOCS / f"validation_{a.tag}_stats.json").write_text(json.dumps(S, indent=1, ensure_ascii=False), encoding="utf-8")

    fig, axes = plt.subplots(3, 1, figsize=(10.5, 10.5), sharex=True)
    for ax, r in zip(axes, REGIONS[:3]):
        yr, reg = yrs[r], load_region(r)
        pre = yr.loc[2003:2011]
        ax.axvspan(2002.5, 2011.5, color="#eef1f5", lw=0)
        ax.axvline(2011.5, color=MUTED, lw=1, ls="--")
        ax.fill_between(pre.index, pre.h_lo, pre.h_hi, color=C_V, alpha=0.16, lw=0, label="Estimate range (before 2012)")
        ax.plot(yr.index, yr.raw, color=C_RAW, lw=2, marker="o", ms=5, mfc=BG, mew=1.6, zorder=3, label="Before: raw counts (MODIS, then VIIRS)")
        ax.plot(yr.index, yr.h, color=C_V, lw=2.6, marker="o", ms=5.5, mec=BG, mew=1.1, zorder=4, label="After: harmonized (VIIRS-equivalent)")
        chk = yr.loc[2011:2022]   # check line, not used after 2011 (see validate.py)
        ax.plot(chk.index, chk.est, color=C_V, lw=1.6, ls=(0, (4, 3)), zorder=2, label="Check: MODIS × coefficient, 2012–2022 (not used)")
        ax.set_ylim(0, yr.h_hi.max() * 1.12)
        ax.set_xlim(2002.5, 2025.6)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: (f"{v / 1000:.0f}k" if v % 1000 == 0 else f"{v / 1000:.1f}k") if v else "0"))
        ax.grid(axis="x", visible=False)
        tag = "  (experimental: rough estimate)" if reg.get("harmonize", {}).get("quality") == "experimental" else ""
        ax.set_title(f"{reg['name_en']}{tag}")
        ax.set_ylabel("Detections per year")
    h_, l_ = axes[0].get_legend_handles_labels()
    axes[0].legend([h_[2], h_[3], h_[1], h_[0]], [l_[2], l_[3], l_[1], l_[0]], loc="upper right", fontsize=9.5)
    axes[0].text(2007, axes[0].get_ylim()[1] * 0.95, "MODIS only", ha="center", va="top", fontsize=9.5, color=INK2)
    axes[2].set_xticks(range(2003, 2026, 2))
    fig.suptitle("Fire detections 2003–2025, before and after harmonization", x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.text(0.01, 0.008, "Data: NASA FIRMS (MODIS Collection 6.1, VIIRS S-NPP 375 m). Static sources and low-confidence detections removed.\n"
             "Values before 2012 are estimates. Chart made with AI-assisted code (Claude).", fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.045, 1, 0.97))
    fig.savefig(DOCS / f"{a.tag}_before_after.png")
    plt.close(fig)
    brief = {r: {k: S[r][k] for k in ["cv_month_weighted_abs_err_pct", "cv_year_mean_abs_err_pct", "cv_year_max_abs_err_pct", "test_2023_2025_total_err_pct",
                                      "uncertainty_p16_p84", "junction_2012", "level_ratio_after_over_before", "change_2011_to_2012_pct",
                                      "overlap_monthly_corr_estimate_vs_viirs", "yearly_h", "modis_2002_2011_total"]} for r in REGIONS}
    print(json.dumps(brief, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
