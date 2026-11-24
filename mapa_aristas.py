"""
mapa de la red con el cambio del tiempo perdido de cada arista entre la
configuracion de netconvert y la mejor solucion del GA.

Lee las salidas por arista que deja run_detailed en detail/ y la geometria de
la red, asi que el mapa refleja los datos de la corrida y no numeros copiados a
mano. Los nombres de las vias salen de map.osm, con el mismo identificador de
OpenStreetMap que usa analisis_corrida.py para agruparlas.

Uso:
    python mapa_aristas.py g150p30m12touuniP2c2600s42
"""

import os
import re
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
import sumolib

from analisis_corrida import aristas, via

TINTA, TINTA_2 = "#0b0b0b", "#52514e"
EJE, FONDO = "#c3c2b7", "#fcfcfb"

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
    "figure.facecolor": FONDO,
    "axes.facecolor": FONDO,
})

DESTINO = r"C:\Users\noone\Documents\GitHub\protocolo\imagenes"

# escala divergente: azul = el tiempo perdido baja, rojo = sube, gris = sin cambio
# apreciable; tres pasos por brazo con la misma luminosidad en ambos lados
CLASES = [
    # (desde, hasta, color, grosor, etiqueta) sobre el cambio mejor - base en s
    (-np.inf, -10000, "#104281", 3.4, "baja más de 10 000 s"),
    (-10000, -1000, "#2a78d6", 2.2, "baja de 1000 a 10 000 s"),
    (-1000, -100, "#86b6ef", 1.4, "baja de 100 a 1000 s"),
    (-100, 100, EJE, 0.8, "cambia menos de 100 s"),
    (100, 1000, "#ec9893", 1.4, "sube de 100 a 1000 s"),
    (1000, 10000, "#d13d3c", 2.2, "sube de 1000 a 10 000 s"),
    (10000, np.inf, "#7f1e20", 3.4, "sube más de 10 000 s"),
]

# arista sobre la que va el numero de cada via; por defecto la de mayor ahorro,
# cambiada a mano donde dos numeros quedaban encimados
ANCLA = {"406701908": "406701908#18", "30279769": "30279769#7"}


def clase(cambio):
    for i, (lo, hi, *_resto) in enumerate(CLASES):
        if lo <= cambio < hi:
            return i
    return len(CLASES) - 1


def nombres_osm(path, vias):
    """nombre de calle de cada via de OpenStreetMap pedida"""
    texto = open(path, encoding="utf-8").read()
    out = {}
    for v in vias:
        m = re.search(r'<way id="%s".*?</way>' % v, texto, re.S)
        if m:
            tags = dict(re.findall(r'<tag k="([^"]+)" v="([^"]*)"', m.group(0)))
            out[v] = tags.get("name", v)
    return out


def forma(edge, con_opuesta):
    """
    geometria de la arista; si la calle tiene los dos sentidos en el mapa se usa
    el carril derecho, que netconvert ya desplaza del eje, para que no se tapen
    """
    if con_opuesta:
        return edge.getLane(0).getShape()
    return edge.getShape()


def main(run):
    base = aristas(f"detail/{run}.baseline.edgedata.xml")
    mejor = aristas(f"detail/{run}.best.edgedata.xml")
    ids = sorted(set(base) | set(mejor))
    cambio = {e: mejor.get(e, 0.0) - base.get(e, 0.0) for e in ids}

    net = sumolib.net.readNet("test.net.xml")
    conjunto = set(ids)

    def opuesta(e):
        return e[1:] if e.startswith("-") else "-" + e

    fig, ax = plt.subplots(figsize=(7.2, 8.6))
    ax.set_aspect("equal")
    ax.axis("off")

    # todas las aristas por donde pueden circular vehiculos aparecen en la salida
    # por arista, asi que no hace falta un fondo; se dibujan de menor a mayor
    # cambio para que las grandes queden encima
    for i in sorted(range(len(CLASES)), key=lambda k: abs(k - 3)):
        segs = [forma(net.getEdge(e), opuesta(e) in conjunto)
                for e in ids if clase(cambio[e]) == i]
        if segs:
            _lo, _hi, color, grosor, _et = CLASES[i]
            ax.add_collection(LineCollection(segs, colors=color, linewidths=grosor,
                                             capstyle="round", zorder=2 + abs(i - 3)))

    # semaforos
    tls = [net.getNode(n.getID()).getCoord() for n in net.getNodes()
           if n.getType() == "traffic_light"]
    xs, ys = zip(*tls)
    ax.scatter(xs, ys, s=7, color=TINTA_2, linewidths=0, zorder=7)

    # las cinco vias que mas ahorran: un numero sobre la propia calle y una clave
    # con su nombre; con nombres completos los rotulos se enciman, porque las
    # cinco quedan en la misma esquina de la red
    por_via = {}
    for e in ids:
        por_via.setdefault(via(e), []).append(e)
    tp = {v: (sum(base.get(e, 0.0) for e in es), sum(mejor.get(e, 0.0) for e in es))
          for v, es in por_via.items()}
    top = sorted(tp, key=lambda v: tp[v][0] - tp[v][1], reverse=True)[:5]
    nombres = nombres_osm("map.osm", top)
    for k, v in enumerate(top, 1):
        e = ANCLA.get(v) or min(por_via[v], key=lambda a: cambio[a])
        shape = np.array(net.getEdge(e).getShape())
        largo = np.r_[0, np.cumsum(np.hypot(*np.diff(shape, axis=0).T))]
        x, y = (np.interp(largo[-1] / 2, largo, shape[:, 0]),
                np.interp(largo[-1] / 2, largo, shape[:, 1]))
        ax.text(x, y, str(k), ha="center", va="center",
                fontsize=9, color=TINTA, zorder=9,
                bbox=dict(boxstyle="circle,pad=0.25", facecolor=FONDO,
                          edgecolor=TINTA, linewidth=0.9))

    xmin, ymin, xmax, ymax = net.getBoundary()

    # clave de las vias numeradas, en la esquina inferior derecha que queda libre;
    # redondeada a centenas como en el texto de resultados
    def miles(s):
        return f"{round(s, -2):,.0f}".replace(",", " ")

    kx, ky = 0.765, 0.25
    ax.text(kx, ky, "Vías con mayor ahorro neto:\ntiempo perdido total con\nnetconvert y con el AGS",
            transform=ax.transAxes, fontsize=9.5, color=TINTA, va="bottom", linespacing=1.3)
    for k, v in enumerate(top, 1):
        b, m = tp[v]
        yk = ky - 0.024 - 0.03 * (k - 1)
        ax.text(kx + 0.013, yk, str(k), transform=ax.transAxes, ha="center", va="center",
                fontsize=9, color=TINTA,
                bbox=dict(boxstyle="circle,pad=0.25", facecolor=FONDO,
                          edgecolor=TINTA, linewidth=0.9))
        ax.text(kx + 0.04, yk, f"{nombres.get(v, v)}: {miles(b)} a {miles(m)} s",
                transform=ax.transAxes, fontsize=9.5, color=TINTA_2, va="center")
    ax.set_xlim(xmin - 20, xmax + 20)
    ax.set_ylim(ymin - 20, ymax + 20)

    # escala grafica bajo la clave y norte arriba a la izquierda, donde no hay
    # calles; la red esta en UTM, asi que las unidades son metros
    x0, y0 = xmax - 500, ymin + 60
    ax.plot([x0, x0 + 500], [y0, y0], color=TINTA_2, linewidth=2, solid_capstyle="butt", zorder=8)
    for xt in (x0, x0 + 250, x0 + 500):
        ax.plot([xt, xt], [y0 - 14, y0 + 14], color=TINTA_2, linewidth=1, zorder=8)
    ax.text(x0, y0 + 30, "0", ha="center", va="bottom", fontsize=9, color=TINTA_2)
    ax.text(x0 + 250, y0 + 30, "250", ha="center", va="bottom", fontsize=9, color=TINTA_2)
    ax.text(x0 + 500, y0 + 30, "500 m", ha="center", va="bottom", fontsize=9, color=TINTA_2)
    ax.annotate("", xy=(xmin + 80, ymax - 240), xytext=(xmin + 80, ymax - 400),
                arrowprops=dict(arrowstyle="-|>", color=TINTA_2, linewidth=1.2))
    ax.text(xmin + 80, ymax - 220, "N", ha="center", va="bottom", fontsize=10, color=TINTA_2)

    # leyenda: una entrada por clase con el numero de aristas
    cuenta = [sum(1 for e in ids if clase(cambio[e]) == i) for i in range(len(CLASES))]
    entradas = [Line2D([0], [0], color=c, linewidth=g, solid_capstyle="round")
                for _lo, _hi, c, g, _et in CLASES]
    etiquetas = [f"{et} ({n})" for (_lo, _hi, _c, _g, et), n in zip(CLASES, cuenta)]
    entradas.append(Line2D([0], [0], marker="o", color="none", markerfacecolor=TINTA_2,
                           markeredgewidth=0, markersize=3.5))
    etiquetas.append("semáforo")
    ley = fig.legend(entradas, etiquetas, loc="lower center", ncol=2, frameon=False,
                     fontsize=9.5, title="Cambio del tiempo perdido total por arista",
                     title_fontsize=10.5, handlelength=2.4, columnspacing=1.8,
                     bbox_to_anchor=(0.5, 0.0))
    ley.get_title().set_color(TINTA)
    for t in ley.get_texts():
        t.set_color(TINTA_2)

    fig.subplots_adjust(left=0.01, right=0.99, top=0.995, bottom=0.17)
    salida = f"{run}.mapa_aristas.png"
    fig.savefig(salida, dpi=200, facecolor=FONDO)
    if os.path.isdir(DESTINO):
        fig.savefig(os.path.join(DESTINO, salida), dpi=200, facecolor=FONDO)
    print(salida, "| aristas por clase:", cuenta)
    print("vias numeradas:", [(v, nombres.get(v), *map(round, tp[v])) for v in top])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "g150p30m12touuniP2c2600s42")
