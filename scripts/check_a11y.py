# AI-assisted: generated with Claude (Anthropic)
"""Colour accessibility check for the burn calendar (step 38).

Tests the colour ramp, the "zero" and "no data" fills, the marker/outline colours and the controls
(buttons, selects, focus ring) used in web/app.js and web/style.css. The page has one dark theme:
  - grayscale: lightness steps between neighbouring levels
  - colour-vision deficiency: deuteranopia, protanopia (and tritanopia), Machado et al. 2009, severity 1.0
  - contrast of markers/outlines against the cell colour (WCAG 1.4.11 asks for 3:1)

Usage: python scripts/check_a11y.py   (prints a report; use --write to save docs/accessibility_colors.md)
"""
import argparse
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent

# Inferno (matplotlib, CC0) sampled from 0.15 to 0.98, as INFERNO in web/app.js
INFERNO = ["#2b0b57", "#57106e", "#82206c", "#ad305d", "#d24644",
           "#ee6a24", "#fb9706", "#f9cb35", "#f5f992"]
THEMES = {   # values copied from web/style.css (:root) and the ramp() function in web/app.js
    "dark": dict(surface="#161a21", ink="#eceef1", muted="#9aa0a9", zero="#2a2e34", ramp=INFERNO,
                 control_bg="#2a313d", control_bg_hover="#364050", control_border="#7e8796", control_border_hover="#b4bac4",
                 accent="#ff7a1a", accent_ink="#1a0f05", primary_border="#ffb27a", focus="#ffd0a1"),
}
# Design criteria (our own, stated so the result can be judged): neighbouring levels of a 7-level ramp
# differ by dE2000 >= 6 (clearly different side by side) and by >= 8 L* in lightness, in every view,
# with lightness always changing in the same direction.
MIN_DE, MIN_DL = 6.0, 8.0
LEVELS = 7   # how many distinct levels a reader is expected to tell apart

# Machado, Oliveira, Fernandes (2009), severity 1.0, applied to linear RGB
CVD = {
    "deuteranopia": np.array([[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]]),
    "protanopia": np.array([[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]]),
    "tritanopia": np.array([[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]]),
}


def hex_rgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)]) / 255.0


def to_linear(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def luminance(rgb):
    return float(to_linear(np.asarray(rgb)) @ np.array([0.2126, 0.7152, 0.0722]))


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def lab(rgb):
    m = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
    xyz = m @ to_linear(np.asarray(rgb)) / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])


def de2000(c1, c2):
    """CIEDE2000 colour difference between two Lab colours."""
    L1, a1, b1 = c1
    L2, a2, b2 = c2
    C1, C2 = np.hypot(a1, b1), np.hypot(a2, b2)
    Cm = (C1 + C2) / 2
    G = 0.5 * (1 - np.sqrt(Cm ** 7 / (Cm ** 7 + 25 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1p = np.degrees(np.arctan2(b1, a1p)) % 360
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360
    dLp, dCp = L2 - L1, C2p - C1p
    dh = h2p - h1p
    if C1p * C2p == 0:
        dh = 0
    elif dh > 180:
        dh -= 360
    elif dh < -180:
        dh += 360
    dHp = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dh / 2))
    Lpm, Cpm = (L1 + L2) / 2, (C1p + C2p) / 2
    if C1p * C2p == 0:
        hpm = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hpm = (h1p + h2p) / 2
    else:
        hpm = (h1p + h2p + 360) / 2 if h1p + h2p < 360 else (h1p + h2p - 360) / 2
    T = (1 - 0.17 * np.cos(np.radians(hpm - 30)) + 0.24 * np.cos(np.radians(2 * hpm))
         + 0.32 * np.cos(np.radians(3 * hpm + 6)) - 0.20 * np.cos(np.radians(4 * hpm - 63)))
    dtheta = 30 * np.exp(-(((hpm - 275) / 25) ** 2))
    Rc = 2 * np.sqrt(Cpm ** 7 / (Cpm ** 7 + 25 ** 7))
    Sl = 1 + 0.015 * (Lpm - 50) ** 2 / np.sqrt(20 + (Lpm - 50) ** 2)
    Sc, Sh = 1 + 0.045 * Cpm, 1 + 0.015 * Cpm * T
    Rt = -np.sin(np.radians(2 * dtheta)) * Rc
    return float(np.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2 + Rt * (dCp / Sc) * (dHp / Sh)))


def simulate(rgb, kind):
    if kind == "normal":
        return np.asarray(rgb)
    if kind == "grayscale":
        g = float(to_srgb(np.array(luminance(rgb))))
        return np.array([g, g, g])
    return to_srgb(CVD[kind] @ to_linear(np.asarray(rgb)))


def ramp_color(ramp, t):
    x = t * (len(ramp) - 1)
    i = min(int(x), len(ramp) - 2)
    a, b = hex_rgb(ramp[i]), hex_rgb(ramp[i + 1])
    return a + (b - a) * (x - i)


def ink_on(fill):   # same rule as inkOn() in web/app.js
    return hex_rgb("#1d1f23") if luminance(fill) > 0.25 else hex_rgb("#ffffff")


def report():
    out, fails = [], []
    for name, th in THEMES.items():
        out.append(f"\n## {name} theme\n")
        ts = np.linspace(0, 1, LEVELS)
        cols = [ramp_color(th["ramp"], t) for t in ts]
        out.append(f"Ramp compared at {LEVELS} evenly spaced levels (low to high detections).\n")
        out.append("| view | smallest step between neighbouring levels (dE2000) | smallest lightness step (dL*) | lightness order |")
        out.append("|---|---|---|---|")
        for kind in ["normal", "deuteranopia", "protanopia", "tritanopia", "grayscale"]:
            sim = [simulate(c, kind) for c in cols]
            labs = [lab(c) for c in sim]
            steps = [de2000(labs[i], labs[i + 1]) for i in range(LEVELS - 1)]
            dl = [labs[i + 1][0] - labs[i][0] for i in range(LEVELS - 1)]
            mono = "monotonic" if all(d > 0 for d in dl) or all(d < 0 for d in dl) else "NOT monotonic"
            ok = min(steps) >= MIN_DE and mono == "monotonic" and min(abs(d) for d in dl) >= MIN_DL
            out.append(f"| {kind} | {min(steps):.1f} | {min(abs(d) for d in dl):.1f} | {mono} {'ok' if ok else 'CHECK'} |")
            if not ok and kind != "tritanopia":
                fails.append(f"{name}/{kind}: ramp steps too small or not monotonic")
        # "0 detections" carries a ring marker, so colour only has to keep it apart for normal and colour-deficient vision
        f = hex_rgb(th["zero"])
        out.append("\n0-detection fill versus the nearest ramp level (it also carries a ring marker, so grayscale is covered by shape):\n")
        out.append("| view | dE2000 to nearest ramp level |")
        out.append("|---|---|")
        for kind in ["normal", "deuteranopia", "protanopia"]:
            lf = lab(simulate(f, kind))
            d = min(de2000(lf, lab(simulate(ramp_color(th["ramp"], t), kind))) for t in np.linspace(0, 1, 21))
            out.append(f"| {kind} | {d:.1f} |")
        ts101 = np.linspace(0, 1, 101)
        surf, ink, muted = (hex_rgb(th[k]) for k in ("surface", "ink", "muted"))
        worst_ink = min(contrast(ink_on(ramp_color(th["ramp"], t)), ramp_color(th["ramp"], t)) for t in ts101)
        worst_ink_zero = contrast(ink_on(f), f)
        ring = min(max(contrast(ink, ramp_color(th["ramp"], t)), contrast(surf, ramp_color(th["ramp"], t))) for t in ts101)
        ink_only = min(contrast(ink, ramp_color(th["ramp"], t)) for t in ts101)
        low = [t for t in ts101 if contrast(ramp_color(th["ramp"], t), surf) < 3]
        hatch = contrast(muted, f)
        out.append(f"\n- Marker triangles, dashed outline and zero ring (colour chosen per cell): worst contrast with the cell colour {worst_ink:.2f}:1 (needs 3:1); on 0-detection cells {worst_ink_zero:.2f}:1.")
        out.append(f"- Selected-month ring: a single dark outline would reach only {ink_only:.2f}:1 on some cells (fails). The two-tone ring (dark outside, light inside) reaches at least {ring:.2f}:1 on every cell colour.")
        out.append(f"- Cells with under 3:1 against the page: {len(low)} of 101 ramp positions, plus the 0 and no-data fills. They get a thin outline in the muted text colour ({contrast(muted, surf):.1f}:1 against the page).")
        out.append(f"- No-data hatch lines against their base fill: {hatch:.1f}:1 (the pattern, not the colour, carries the meaning).")
        if worst_ink < 3:
            fails.append(f"{name}: marker contrast {worst_ink:.2f} < 3")
        if ring < 3:
            fails.append(f"{name}: selected ring contrast {ring:.2f} < 3")
        if contrast(muted, surf) < 3:
            fails.append(f"{name}: outline colour contrast < 3")
        if hatch < 3:
            fails.append(f"{name}: hatch contrast {hatch:.1f} < 3")
        # Controls (WCAG 1.4.11 for the boundary and focus ring, 1.4.3 for the button text)
        if "control_border" in th:
            c = {k: hex_rgb(v) for k, v in th.items() if k != "ramp"}
            checks = [
                ("control border against the card", contrast(c["control_border"], surf), 3),
                ("control border against the control fill", contrast(c["control_border"], c["control_bg"]), 3),
                ("hovered control: border against its fill", contrast(c["control_border_hover"], c["control_bg_hover"]), 3),
                ("control text on the control fill", contrast(ink, c["control_bg"]), 4.5),
                ("control text on the hovered fill", contrast(ink, c["control_bg_hover"]), 4.5),
                ("orange button against the card", contrast(c["accent"], surf), 3),
                ("orange button text", contrast(c["accent_ink"], c["accent"]), 4.5),
                ("focus ring against the card", contrast(c["focus"], surf), 3),
                ("focus ring against the page", contrast(c["focus"], hex_rgb("#0d0f13")), 3),
            ]
            out.append("\nControls (buttons, selects, inputs):\n")
            out.append("| what | contrast | needs |")
            out.append("|---|---|---|")
            for label, v, need in checks:
                out.append(f"| {label} | {v:.2f}:1 | {need}:1 {'ok' if v >= need else 'FAIL'} |")
                if v < need:
                    fails.append(f"{name}: {label} {v:.2f} < {need}")
    return "\n".join(out), fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="save the report to docs/accessibility_colors.md")
    args = ap.parse_args()
    text, fails = report()
    print(text)
    print("\nPROBLEMS:" if fails else "\nNo problems found.")
    for f in fails:
        print(" -", f)
    if args.write:
        p = ROOT / "docs" / "accessibility_colors.md"
        p.write_text("# Colour accessibility check (step 38)\n\nGenerated by scripts/check_a11y.py.\n" + text + "\n", encoding="utf-8")
        print("written", p)


if __name__ == "__main__":
    main()
