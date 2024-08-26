#!/usr/bin/env python3

import argparse
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd

plt.rc("text", usetex=True)
cmap_med = [
    "#F15A60",
    "#7AC36A",
    "#5A9BD4",
    "#FAA75B",
    "#9E67AB",
    "#CE7058",
    "#D77FB4",
    "#737373",
]
cmap = [
    "#EE2E2F",
    "#008C48",
    "#185AA9",
    "#F47D23",
    "#662C91",
    "#A21D21",
    "#B43894",
    "#010202",
]
dashseq = [
    (None, None),
    [10, 5],
    [10, 4, 3, 4],
    [3, 3],
    [10, 4, 3, 4, 3, 4],
    [3, 3],
    [3, 3],
]
markertype = ["s", "d", "o", "p", "h"]

def flatten(xss):
    return [x for xs in xss for x in xs]

def parse_input(fname):
    with open(fname, "r") as f:
        for line in f:
            if line.startswith("amr.n_cell"):
                n_cell = int(line.split("=")[-1].split()[0])
            elif line.startswith("incflo.godunov_type"):
                adv_type = line.split("=")[-1].strip()

    return n_cell, adv_type


if __name__ == "__main__":

    # Parse arguments
    parser = argparse.ArgumentParser(description="A simple plot tool")
    parser.add_argument(
        "-f", "--fdirs", help="Folders to plot", type=str, required=True, nargs="+"
    )
    args = parser.parse_args()

    fields = ["u", "v", "w"]

    lst = []
    for k, fdir in enumerate(args.fdirs):
        iname = os.path.join(fdir, "mms.inp")
        n_cell, adv_type = parse_input(iname)

        df = pd.read_csv(os.path.join(fdir, "mms.log"), delim_whitespace=True)
        df["res"] = n_cell
        df["adv"] = adv_type
        lst.append(df)

    df = pd.concat(lst).sort_values(by=["adv", "res", "time"])

    lst = []
    for i, (adv, group_adv) in enumerate(df.groupby(by="adv")):
        for j, (n_cell, group) in enumerate(group_adv.groupby(by="res")):
            lst.append(group.iloc[-1])
            for field in fields:
                plt.figure(field)
                p = plt.plot(
                    group.time,
                    group[f"L2_{field}"],
                    lw=2,
                    color=cmap[i],
                    label=f"{adv.upper()} (${{{n_cell}}}^3$)",
                )
                p[0].set_dashes(dashseq[j])

    ooa = pd.DataFrame(lst)

    fname = "plots.pdf"
    with PdfPages(fname) as pdf:
        for k, field in enumerate(fields):
            plt.figure(field)
            ax = plt.gca()
            plt.xlabel(r"$t$", fontsize=22, fontweight="bold")
            plt.ylabel(f"$L_2({field})$", fontsize=22, fontweight="bold")
            plt.setp(ax.get_xmajorticklabels(), fontsize=18, fontweight="bold")
            plt.setp(ax.get_ymajorticklabels(), fontsize=18, fontweight="bold")
            legend = ax.legend(loc="best")
            plt.tight_layout()
            pdf.savefig(dpi=300)

        lst_theory = []
        for i, (adv, group) in enumerate(ooa.groupby(by="adv")):
            for k, field in enumerate(fields):
                plt.figure(f"ooa_{field}")
                plt.loglog(
                    group.res,
                    group[f"L2_{field}"],
                    lw=2,
                    color=cmap[i],
                    marker=markertype[i],
                    mec=cmap[i],
                    mfc=cmap[i],
                    ms=10,
                    label=f"{adv.upper()}",
                )

                if k == 0:
                    idx = 1
                    theory_order = 2
                    group["theory"] = (
                        group["L2_u"].iloc[idx]
                        * (group.res.iloc[idx] / group.res) ** theory_order
                    )
                    plt.loglog(
                        group.res, group.theory, lw=1, color=cmap[-1], label="2nd order"
                    )
                    lst_theory.append(group.theory.to_list())

        ooa["theory"] = flatten(lst_theory)
        ooa.to_csv("data.csv", index=False)
        print(ooa)
        for k, field in enumerate(fields):
            plt.figure(f"ooa_{field}")
            ax = plt.gca()
            plt.xlabel(r"$N$", fontsize=22, fontweight="bold")
            plt.ylabel(f"$L_2({field})$", fontsize=22, fontweight="bold")
            plt.setp(ax.get_xmajorticklabels(), fontsize=18, fontweight="bold")
            plt.setp(ax.get_ymajorticklabels(), fontsize=18, fontweight="bold")
            legend = ax.legend(loc="best")
            plt.tight_layout()
            pdf.savefig(dpi=300)
