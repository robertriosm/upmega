"""
graficas comparativas: netconvert contra la solucion del GA.

Lee los tripinfo que deja run_detailed en detail/, asi que la figura siempre
refleja los datos de la corrida y no numeros copiados a mano.
"""

import re
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

# paleta validada: slots 1 y 2 del tema categorico
AZUL, NARANJA = "#2a78d6", "#eb6834"
TINTA, TINTA_2, APAGADO = "#0b0b0b", "#52514e", "#898781"
REJILLA, EJE, FONDO = "#e1e0d9", "#c3c2b7", "#fcfcfb"

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
    "figure.facecolor": FONDO,
    "axes.facecolor": FONDO,
})


def leer(path):
    """duraciones y esperas de un tripinfo"""
    b = open(path, "rb").read()
    d = np.array(re.findall(rb'duration="([\d.]+)"', b), dtype=float)
    w = np.array(re.findall(rb'waitingTime="([\d.]+)"', b), dtype=float)
    return d, w


def resumen(v):
    return [v.mean(), np.percentile(v, 50), np.percentile(v, 90),
            np.percentile(v, 99), v.max()]


def barras(ax, base, opt, titulo, etiquetas):
    x = np.arange(len(etiquetas))
    ancho = 0.36
    hueco = 0.02  # separacion entre las dos barras del par

    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color=REJILLA, linewidth=0.8)
    ax.xaxis.grid(False)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color(EJE)

    for xi, (a, b) in enumerate(zip(base, opt)):
        for desp, valor, color in ((-ancho / 2 - hueco, a, AZUL),
                                   (ancho / 2 + hueco, b, NARANJA)):
            ax.add_patch(FancyBboxPatch(
                (xi + desp - ancho / 2, 0), ancho, valor,
                boxstyle="round,pad=0,rounding_size=0.045",
                mutation_aspect=max(base + opt) / 6,
                facecolor=color, edgecolor="none"))
        # etiqueta directa: solo la reduccion, no un numero en cada barra
        ax.text(xi, max(a, b) * 1.04, f"−{(1 - b / a) * 100:.0f}%",
                ha="center", va="bottom", fontsize=9.5, color=TINTA_2)

    ax.set_xticks(x)
    ax.set_xticklabels(etiquetas)
    ax.set_xlim(-0.6, len(etiquetas) - 0.4)
    ax.tick_params(colors=APAGADO, length=0, labelsize=10)
    ax.set_title(titulo, fontsize=12.5, color=TINTA, pad=14, loc="left")


def fitness(run, destino):
    """evolucion del fitness por generacion, en J (segundos) para que se lea"""
    import cloudpickle
    with open(f"{run}.pkl", "rb") as f:
        ga = cloudpickle.load(f)
    J = [1 / v for v in ga.best_solutions_fitness]

    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color=REJILLA, linewidth=0.8)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color(EJE)

    ax.plot(range(len(J)), J, color=AZUL, linewidth=2, solid_capstyle="round")
    mejor = int(np.argmin(J))
    ax.plot(mejor, J[mejor], "o", markersize=9, color=AZUL,
            markeredgecolor=FONDO, markeredgewidth=2)
    ax.annotate(f"generación {mejor}\nJ = {J[mejor]:.1f} s",
                (mejor, J[mejor]), textcoords="offset points", xytext=(-12, 16),
                ha="right", fontsize=10, color=TINTA_2)
    ax.annotate(f"punto de partida (netconvert)\nJ = {J[0]:.1f} s",
                (0, J[0]), textcoords="offset points", xytext=(14, -4),
                ha="left", va="top", fontsize=10, color=TINTA_2)

    ax.set_xlabel("generación", fontsize=10, color=TINTA_2)
    ax.set_ylabel("J = viaje + 1.1 × espera  (s)", fontsize=10, color=TINTA_2)
    ax.tick_params(colors=APAGADO, length=0, labelsize=10)
    ax.set_title("Evolución del mejor individuo", fontsize=12.5, color=TINTA,
                 pad=14, loc="left")
    fig.tight_layout()
    fig.savefig(destino, dpi=200, facecolor=FONDO)
    print(f"escrito: {destino}")


def main(run):
    db, wb = leer(f"detail/{run}.baseline.tripinfo.xml")
    dm, wm = leer(f"detail/{run}.best.tripinfo.xml")
    etiquetas = ["media", "mediana", "p90", "p99", "máximo"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.8), sharey=True)

    barras(ax1, resumen(db), resumen(dm), "Tiempo de viaje", etiquetas)
    barras(ax2, resumen(wb), resumen(wm), "Tiempo de espera", etiquetas)

    ax1.set_ylabel("segundos por vehículo", fontsize=10, color=TINTA_2)
    ax1.set_ylim(0, max(db.max(), wb.max()) * 1.14)

    fig.legend(handles=[plt.Line2D([], [], marker="s", linestyle="none", markersize=9,
                                   color=AZUL, label="netconvert (punto de partida)"),
                        plt.Line2D([], [], marker="s", linestyle="none", markersize=9,
                                   color=NARANJA, label="SGA (mejor solución)")],
               loc="lower center", ncol=2, frameon=False, fontsize=10.5,
               labelcolor=TINTA_2, bbox_to_anchor=(0.5, -0.02))

    fig.suptitle(f"Demora por vehículo · {len(db)} vehículos · {run}",
                 fontsize=13.5, color=TINTA, x=0.055, ha="left", y=0.99)
    fig.tight_layout(rect=[0, 0.06, 1, 0.94])
    fig.savefig(f"{run}.comparativa.png", dpi=200, facecolor=FONDO)
    print(f"escrito: {run}.comparativa.png")
    fitness(run, f"{run}.fitness.png")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "g150p30m12touuniP2c1000s42")
