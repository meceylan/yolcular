# AI-assisted: generated with Claude (Anthropic)
"""Adım 32: uyumlu serinin doğrulaması.

1. Önce / sonra grafiği (demo için, İngilizce): ham birleşik seri ile uyumlu seri
2. Geçiş yılı (2012) çevresinde MODIS tahmini ile VIIRS ölçümü
Çıktı: docs/harmonized_before_after.png, docs/harmonized_validation.png, docs/validation_stats.json
Kullanım: python scripts/validate.py --region turkiye
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import DATA_PROCESSED, DOCS, load_region, region_parser
from harmonize import VIIRS_START
from overlap import STABLE_LAST, gap_dates

C_M, C_V, C_RAW, INK, INK2, MUTED, GRID, BG = "#2a78d6", "#eb6834", "#898781", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"


def style(base=10):
    plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG, "axes.edgecolor": "#c3c2b7",
                         "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
                         "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
                         "grid.linewidth": 0.7, "axes.axisbelow": True, "font.size": base, "axes.titlesize": base + 2,
                         "axes.titleweight": "bold", "axes.titlelocation": "left", "legend.frameon": False, "figure.dpi": 150})


def thousands(ax):
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v / 1000:.0f}k" if v else "0"))


def main():
    a = region_parser("Uyumlu serinin doğrulaması (adım 32)").parse_args()
    region = load_region(a.region)
    out_dir = DATA_PROCESSED / region["name"]
    mon = pd.read_csv(out_dir / "harmonized_monthly.csv")
    coef = json.loads((out_dir / "coefficients.json").read_text(encoding="utf-8"))
    c = {int(k): v for k, v in coef["modis_to_snpp"].items()}
    mon["y"], mon["mo"] = mon.ym.str[:4].astype(int), mon.ym.str[5:].astype(int)
    mon["raw_combined"] = np.where(mon.src == "M", mon.m, mon.v)            # uyumlaştırma yok: 2012 öncesi MODIS, sonrası VIIRS
    mon["modis_est"] = mon.m * mon.mo.map(c)                                 # MODIS × katsayı (tüm dönem)
    yr = mon[mon.y.between(2003, 2025)].groupby("y").agg(h=("h", "sum"), h_lo=("h_lo", "sum"), h_hi=("h_hi", "sum"), raw=("raw_combined", "sum"),
                                                         m=("m", "sum"), v=("v", "sum"), est=("modis_est", "sum"))
    pre, post = yr.loc[2003:2011], yr.loc[2012:2025]
    S = {
        "median_annual": {"raw_combined_2003_2011": float(pre.raw.median()), "raw_combined_2012_2025": float(post.raw.median()),
                          "harmonized_2003_2011": float(pre.h.median()), "harmonized_2012_2025": float(post.h.median())},
        "level_ratio_after_over_before": {"raw_combined": round(float(post.raw.median() / pre.raw.median()), 2),
                                          "harmonized": round(float(post.h.median() / pre.h.median()), 2),
                                          "modis_alone": round(float(post.m.median() / pre.m.median()), 2)},
        "level_ratio_excluding_2009_2011": {"raw_combined": round(float(post.raw.median() / yr.loc[2003:2008].raw.median()), 2),
                                            "harmonized": round(float(post.h.median() / yr.loc[2003:2008].h.median()), 2),
                                            "modis_alone": round(float(post.m.median() / yr.loc[2003:2008].m.median()), 2)},
        "change_2011_to_2012_pct": {"modis_alone": round(float((yr.m[2012] / yr.m[2011] - 1) * 100), 1),
                                    "harmonized": round(float((yr.h[2012] / yr.h[2011] - 1) * 100), 1),
                                    "raw_combined": round(float((yr.raw[2012] / yr.raw[2011] - 1) * 100), 1)},
    }
    # geçiş yılı: 2012 Şub–Ara, MODIS tahmini ile VIIRS ölçümü (kesinti günleri hariç, adım 31 sınamasından)
    hs = json.loads((DOCS / "harmonize_stats.json").read_text(encoding="utf-8"))
    S["junction_2012_modis_estimate_vs_viirs"] = hs["cv_year_actual_vs_predicted"]["2012"]
    ov = mon[(mon.ym >= VIIRS_START[:7]) & (mon.y <= 2025)]
    S["overlap_monthly_corr_estimate_vs_viirs"] = round(float(ov.modis_est.corr(ov.v)), 3)
    S["overlap_annual_err_pct"] = {int(y): round(float((r.est - r.v) / r.v * 100), 1) for y, r in post.iterrows()}
    # mevsim biçimi: ayların yıllık toplamdaki payı
    def shape(x, col):
        s = x.groupby("mo")[col].sum()
        return (s / s.sum() * 100).round(1)
    S["seasonal_share_pct"] = {"harmonized_2003_2008": shape(mon[mon.y.between(2003, 2008)], "h").to_dict(),
                               "viirs_2012_2025": shape(mon[mon.y.between(2012, 2025)], "h").to_dict(),
                               "raw_modis_2003_2008": shape(mon[mon.y.between(2003, 2008)], "m").to_dict()}
    (DOCS / "validation_stats.json").write_text(json.dumps(S, indent=1, ensure_ascii=False), encoding="utf-8")

    # ---------- 1. önce / sonra (demo) ----------
    style(12)
    fig, ax = plt.subplots(figsize=(11, 5.6))
    ax.axvspan(2002.5, 2011.5, color="#eef1f5", lw=0)
    ax.axvline(2011.5, color=MUTED, lw=1, ls="--")
    ax.fill_between(pre.index, pre.h_lo, pre.h_hi, color=C_V, alpha=0.16, lw=0, label="Estimate range (before 2012)")
    ax.plot(yr.index, yr.raw, color=C_RAW, lw=2.2, marker="o", ms=5.5, mfc=BG, mew=1.8, zorder=3, label="Before: raw counts (MODIS, then VIIRS)")
    ax.plot(yr.index, yr.h, color=C_V, lw=2.8, marker="o", ms=6, mec=BG, mew=1.2, zorder=4, label="After: harmonized (VIIRS-equivalent)")
    # Check line: MODIS × coefficient continued over the overlap years (2012–2022, before the MODIS orbit drift).
    # Not used for the series after 2011 (measured VIIRS is used); it shows the 2011→2012 change also in MODIS alone.
    chk = yr.loc[2011:2022]
    ax.plot(chk.index, chk.est, color=C_V, lw=1.8, ls=(0, (4, 3)), zorder=2, label="Check: MODIS × coefficient, 2012–2022 (not used)")
    h_, l_ = ax.get_legend_handles_labels()
    ax.legend([h_[2], h_[3], h_[1], h_[0]], [l_[2], l_[3], l_[1], l_[0]], loc="upper right", bbox_to_anchor=(0.995, 0.9), fontsize=11.5)
    top = yr.h_hi.max()
    ax.set_ylim(0, top * 1.08)
    ax.set_xlim(2002.5, 2025.6)
    ax.text(2007, top * 1.03, "MODIS only (2003–2011)", ha="center", va="center", fontsize=11, color=INK2)
    ax.text(2018.5, top * 1.03, "VIIRS available (2012–2025)", ha="center", va="center", fontsize=11, color=INK2)
    ax.annotate(f"Raw MODIS-era counts sit ×{S['level_ratio_excluding_2009_2011']['raw_combined']:.1f} lower:\nan artefact of the sensor change",
                (2010, yr.raw[2010]), (2012.4, 6500), fontsize=10.5, color=INK2, arrowprops=dict(arrowstyle="->", color=MUTED, lw=1), va="center")
    thousands(ax)
    ax.set_xticks(range(2003, 2026, 2))
    ax.grid(axis="x", visible=False)
    ax.set_ylabel("Fire detections per year")
    ax.set_title("Türkiye fire detections, 2003–2025: before and after harmonization")
    fig.text(0.01, 0.012, "Data: NASA FIRMS (MODIS Collection 6.1, VIIRS S-NPP 375 m). Static sources and low-confidence detections removed.\n"
             "Values before 2012 are estimates. Chart made with AI-assisted code (Claude).", fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.055, 1, 1))
    fig.savefig(DOCS / "harmonized_before_after.png")
    plt.close(fig)

    # ---------- 2. doğrulama ----------
    style(10)
    fig, axes = plt.subplots(2, 1, figsize=(11, 7.6), gridspec_kw={"height_ratios": [1, 1]})
    ax = axes[0]
    z = mon[(mon.ym >= "2009-01") & (mon.ym <= "2014-12")].copy()
    z["t"] = pd.to_datetime(z.ym + "-01")
    ax.axvline(pd.Timestamp(VIIRS_START), color=MUTED, lw=1, ls="--")
    ax.plot(z.t, z.modis_est, color=C_M, lw=2, label="MODIS × monthly coefficient (estimate)")
    zv = z[z.ym >= VIIRS_START[:7]]
    ax.plot(zv.t, zv.v, color=C_V, lw=2, label="VIIRS S-NPP (measured)")
    ax.text(pd.Timestamp("2012-03-01"), ax.get_ylim()[1] * 0.93, "VIIRS starts →", fontsize=9, color=INK2)
    thousands(ax)
    ax.set_title("Around the switch (2012): the MODIS-based estimate continues into the VIIRS record without a step")
    ax.set_ylabel("Detections per month")
    ax.legend(loc="upper left", fontsize=9)
    ax.set_ylim(0)
    ax = axes[1]
    w = 0.38
    ax.bar(post.index - w / 2, post.est, width=w, color=C_M, label="MODIS × monthly coefficient (estimate)")
    ax.bar(post.index + w / 2, post.v, width=w, color=C_V, label="VIIRS S-NPP (measured)")
    for y, r in post.iterrows():
        e = (r.est - r.v) / r.v * 100
        ax.text(y, max(r.est, r.v) + 700, f"{e:+.0f}%", ha="center", fontsize=8, color=INK2)
    ax.axvspan(STABLE_LAST + 0.5, 2025.5, color="#eef1f5", lw=0, zorder=0)
    ax.text(2024, post.est.max() * 1.0, "not used for calibration\n(MODIS orbit drift)", ha="center", va="top", fontsize=8.5, color=INK2)
    thousands(ax)
    ax.set_xticks(post.index)
    ax.grid(axis="x", visible=False)
    ax.set_ylim(0, post.est.max() * 1.28)
    ax.set_title("Overlap years: annual estimate from MODIS vs VIIRS measurement (labels: estimate error)")
    ax.set_ylabel("Detections per year")
    ax.legend(loc="upper left", fontsize=9, ncol=2)
    fig.tight_layout()
    fig.savefig(DOCS / "harmonized_validation.png")
    plt.close(fig)
    print(json.dumps(S, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
