"""
diagramas de las etapas del algoritmo genetico para el documento.

Genera un PNG por etapa con el mismo lenguaje visual que las graficas de
resultados, para incrustar en las secciones correspondientes del capitulo
de metodologia.
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

AZUL, NARANJA = "#2a78d6", "#eb6834"
VERDE, AMBAR = "#2f8f4e", "#d99a2b"
TINTA, TINTA_2, APAGADO = "#0b0b0b", "#52514e", "#898781"
LINEA, FONDO = "#c3c2b7", "#fcfcfb"

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
    "figure.facecolor": FONDO,
    "axes.facecolor": FONDO,
})

DESTINO = r"C:\Users\noone\Documents\GitHub\protocolo\imagenes"


def lienzo(ancho, alto):
    fig, ax = plt.subplots(figsize=(ancho, alto))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100 * alto / ancho)
    ax.axis("off")
    return fig, ax


def caja(ax, x, y, w, h, texto, sub=None, color=None, relleno=None, punteado=False):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=relleno or "none",
                           edgecolor=color or LINEA, linewidth=1.4,
                           linestyle=(0, (4, 3)) if punteado else "solid", zorder=2))
    ax.text(x + w / 2, y + h * (0.62 if sub else 0.5), texto, ha="center", va="center",
            fontsize=9.5, color=color or TINTA, zorder=3)
    if sub:
        ax.text(x + w / 2, y + h * 0.28, sub, ha="center", va="center",
                fontsize=8, color=APAGADO, zorder=3)


def flecha(ax, x1, y1, x2, y2, color=None, punteada=False):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=11, linewidth=1.3,
                                 linestyle=(0, (4, 3)) if punteada else "solid",
                                 color=color or TINTA_2, zorder=1))


def guardar(fig, nombre):
    ruta = os.path.join(DESTINO, nombre)
    fig.savefig(ruta, dpi=200, facecolor=FONDO, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    print("escrito:", nombre)


# ---------------------------------------------------------------- evaluacion
def evaluacion():
    fig, ax = lienzo(10, 2.6)
    y, h = 10, 14
    etapas = [("Genoma", "440 enteros"), ("Red SUMO", "110 planes"),
              ("Simulación", "763 vehículos"), ("Tripinfo", "por vehículo"),
              ("Aptitud", "F = 1/J")]
    w, sep = 15.5, 5.5
    for i, (t, s) in enumerate(etapas):
        x = i * (w + sep)
        color = AZUL if i == len(etapas) - 1 else None
        caja(ax, x, y, w, h, t, s, color=color)
        if i:
            flecha(ax, x - sep + 0.6, y + h / 2, x - 0.6, y + h / 2)
    ax.text(50, 2.5, "cada evaluación exige una simulación completa; las de una misma generación "
                     "corren en procesos separados y simultáneos",
            ha="center", fontsize=8, color=APAGADO, style="italic")
    guardar(fig, "diag_evaluacion.png")


# -------------------------------------------------------------- codificacion
def codificacion():
    fig, ax = lienzo(10, 4.2)

    ax.text(0, 39, "GENES DE UNA INTERSECCIÓN", fontsize=7.5, color=APAGADO)
    for x, w, t, col, pt in [(0, 17, "ciclo 45", AZUL, False), (19, 13, "peso 30", None, False),
                             (34, 13, "peso 12", None, False), (49, 18, "desfase 25 %", None, True)]:
        caja(ax, x, 30, w, 7, t, color=col, punteado=pt)

    ax.text(0, 25, "REPARTO DEL CICLO — 45 s", fontsize=7.5, color=APAGADO)
    tramos = [(0, 21.3, AMBAR, .38, "ámbar fijo\n12 s"), (21.3, 24.9, TINTA, .12, "mínimos 7+7\n14 s"),
              (46.2, 33.8, AZUL, .28, "a repartir 19 s\n30 : 12")]
    for x, w, c, a, t in tramos:
        ax.add_patch(Rectangle((x, 15), w, 8, facecolor=c, alpha=a, edgecolor="none"))
        ax.text(x + w / 2, 19, t, ha="center", va="center", fontsize=7.5, color=TINTA_2)
    ax.add_patch(Rectangle((0, 15), 80, 8, facecolor="none", edgecolor=LINEA, linewidth=1))

    ax.text(0, 10.5, "PLAN RESULTANTE", fontsize=7.5, color=APAGADO)
    plan = [(0, 35.6, VERDE, .5, "verde 20 s"), (35.6, 10.7, AMBAR, .62, "6 s"),
            (46.3, 23.1, VERDE, .5, "verde 13 s"), (69.4, 10.6, AMBAR, .62, "6 s")]
    for x, w, c, a, t in plan:
        ax.add_patch(Rectangle((x, 1.5), w, 8, facecolor=c, alpha=a, edgecolor="none"))
        ax.text(x + w / 2, 5.5, t, ha="center", va="center", fontsize=8, color=TINTA)
    ax.add_patch(Rectangle((0, 1.5), 80, 8, facecolor="none", edgecolor=LINEA, linewidth=1))

    ax.text(83, 20, "La suma da\nexactamente el\nciclo pedido:\nel sobrante del\nredondeo se\nasigna por\nrestos mayores.",
            fontsize=7.5, color=APAGADO, va="center")
    guardar(fig, "diag_codificacion.png")


# ---------------------------------------------------------------- seleccion
def seleccion():
    fig, ax = lienzo(10, 3.2)
    ax.text(0, 29, "POBLACIÓN — 30 INDIVIDUOS ORDENADOS POR APTITUD", fontsize=7.5, color=APAGADO)
    sorteados = {0, 3, 7, 12, 19}
    for i in range(24):
        x = i * 2.7
        dentro = i in sorteados
        ax.add_patch(Rectangle((x, 22), 2.1, 4.5, facecolor=AZUL if dentro else "none",
                               alpha=.75 if dentro else 1, edgecolor=LINEA if not dentro else "none",
                               linewidth=1))
    ax.text(65.5, 24.2, "… hasta 30", fontsize=8, color=APAGADO)

    ax.text(0, 16.5, "UN TORNEO — 5 SORTEADOS AL AZAR, CON REEMPLAZO", fontsize=7.5, color=APAGADO)
    for i in range(5):
        ax.add_patch(Rectangle((i * 5, 9.5), 4, 4.5, facecolor=AZUL, alpha=.55, edgecolor="none"))
    flecha(ax, 10.5, 8.8, 10.5, 5.2)
    ax.add_patch(Rectangle((7.5, 0.5), 6, 4.2, facecolor=NARANJA, alpha=.8, edgecolor="none"))
    ax.text(10.5, 2.6, "gana", ha="center", va="center", fontsize=8, color=TINTA)
    ax.text(15.5, 2.6, "el de mejor aptitud entre esos cinco pasa a ser padre", fontsize=8.5,
            color=TINTA_2, va="center")

    ax.text(52, 12, "Se repite 12 veces de forma independiente.\n\n"
                    "Un mismo individuo puede ganar varios\n"
                    "torneos, así que los 12 padres pueden ser\n"
                    "menos de 12 individuos distintos.",
            fontsize=8, color=APAGADO, va="center")
    guardar(fig, "diag_seleccion.png")


# -------------------------------------------------------------------- cruce
def cruce():
    fig, ax = lienzo(10, 3.6)

    ax.text(0, 33, "EMPAREJAMIENTO EN ANILLO — 12 PADRES", fontsize=7.5, color=APAGADO)
    for i, et in enumerate(["0", "1", "2", "3", "…", "11"]):
        x = 3 + i * 7
        if et == "…":
            ax.text(x, 27.5, et, ha="center", va="center", fontsize=10, color=APAGADO)
            continue
        ax.add_patch(plt.Circle((x, 27.5), 2.6, facecolor="none", edgecolor=LINEA, linewidth=1.3))
        ax.text(x, 27.5, et, ha="center", va="center", fontsize=8, color=TINTA)
    for i in range(3):
        ax.annotate("", xy=(10 + i * 7, 30.4), xytext=(3 + i * 7, 30.4),
                    arrowprops=dict(arrowstyle="-", color=AZUL, lw=1.4,
                                    connectionstyle="arc3,rad=-0.5"))
    ax.text(48, 27.5, "el último cierra con el primero: de las 66 parejas\n"
                      "posibles solo se usan 12, y las no consecutivas\n"
                      "no se combinan nunca",
            fontsize=8, color=APAGADO, va="center")

    ax.text(0, 21, "CRUCE UNIFORME — UNA MONEDA POR CADA UNO DE LOS 440 GENES", fontsize=7.5, color=APAGADO)
    mascara = [0, 1, 1, 0, 1, 0, 0, 1]
    for fila, (y, col, alpha, et) in enumerate([(15, AZUL, .75, "padre A"), (8.5, NARANJA, .7, "padre B")]):
        ax.text(-1, y + 2, et, fontsize=8, color=TINTA_2, ha="right", va="center")
        for i in range(8):
            ax.add_patch(Rectangle((i * 7, y), 5.6, 4, facecolor=col, alpha=alpha, edgecolor="none"))
    ax.text(-1, 3.5, "hijo", fontsize=8, color=TINTA_2, ha="right", va="center")
    for i, m in enumerate(mascara):
        ax.add_patch(Rectangle((i * 7, 1.5), 5.6, 4,
                               facecolor=NARANJA if m else AZUL, alpha=.7 if m else .75, edgecolor="none"))
        ax.text(i * 7 + 2.8, 7.2, "B" if m else "A", ha="center", va="center",
                fontsize=8, color=APAGADO)
    ax.text(60, 8, "El ciclo de una intersección y los pesos\n"
                   "que lo reparten viven en tramos lejanos\n"
                   "del cromosoma: el hijo puede heredar el\n"
                   "ciclo de un padre y el reparto del otro.",
            fontsize=8, color=APAGADO, va="center")
    guardar(fig, "diag_cruce.png")


# ----------------------------------------------------------------- mutacion
def mutacion():
    fig, ax = lienzo(10, 2.9)

    ax.text(0, 26, "HIJO — SE RECORREN LOS 440 GENES", fontsize=7.5, color=APAGADO)
    mutados = {2, 7}
    for i in range(12):
        x = i * 5.4
        m = i in mutados
        ax.add_patch(Rectangle((x, 19), 4.4, 4.5, facecolor=NARANJA if m else "none",
                               alpha=.8 if m else 1, edgecolor="none" if m else LINEA, linewidth=1))
    ax.text(66, 21.2, "… hasta 440", fontsize=8, color=APAGADO)
    ax.text(0, 16, "los marcados sacaron menos de 0.02 — unos 9 de los 440", fontsize=8, color=NARANJA)

    ax.text(0, 10.5, "QUÉ LE PASA A UN GEN MUTADO — EJEMPLO: UN GEN DE CICLO", fontsize=7.5, color=APAGADO)
    ax.plot([0, 62], [5, 5], color=TINTA_2, lw=1.3)
    for x in (0, 62):
        ax.plot([x, x], [4.2, 5.8], color=TINTA_2, lw=1.3)
    ax.text(0, 2.6, "26 s", fontsize=8, color=APAGADO)
    ax.text(62, 2.6, "120 s", fontsize=8, color=APAGADO, ha="right")
    ax.plot(13, 5, "o", ms=7, color=AZUL)
    ax.text(13, 7.4, "actual · 45 s", ha="center", fontsize=8, color=AZUL)
    ax.plot(48, 5, "o", ms=7, color=NARANJA)
    ax.text(48, 7.4, "nuevo · 110 s", ha="center", fontsize=8, color=NARANJA)
    ax.annotate("", xy=(46.5, 3.4), xytext=(14.5, 3.4),
                arrowprops=dict(arrowstyle="-|>", color=NARANJA, lw=1.4,
                                connectionstyle="arc3,rad=0.35"))

    ax.text(68, 7, "Reemplazo, no perturbación:\n"
                   "el nuevo valor se sortea uniforme\n"
                   "en todo el rango, sin relación con\n"
                   "el anterior. El élite no se muta.",
            fontsize=8, color=APAGADO, va="center")
    guardar(fig, "diag_mutacion.png")


# ---------------------------------------------------------------- actividad
def actividad():
    """proceso general del algoritmo, tal como se ejecuta"""
    fig, ax = lienzo(8.2, 11.8)
    H = 100 * 11.8 / 8.2
    cx, w, h = 48, 62, 6.2

    def paso(y, texto, color=None, relleno=None):
        caja(ax, cx - w / 2, y, w, h, texto, color=color, relleno=relleno)

    ax.add_patch(plt.Circle((cx, H - 3), 2, color=TINTA, zorder=3))

    ys = [H - 13, H - 23, H - 33]
    textos = ["Inicializar simulador y controlador",
              "Leer la red: genoma y espacio genético",
              "Población inicial · individuo 0 = netconvert"]
    for y, t in zip(ys, textos):
        paso(y, t)
    paso(H - 43, "Evaluar población · 1 simulación por individuo", color=AZUL)

    flecha(ax, cx, H - 5, cx, H - 13 + h)
    for a, b in zip([H - 13, H - 23, H - 33], [H - 23, H - 33, H - 43]):
        flecha(ax, cx, a, cx, b + h)

    # rombo
    dy = H - 55
    ax.add_patch(plt.Polygon([(cx, dy + 9), (cx + 26, dy + 4.5), (cx, dy), (cx - 26, dy + 4.5)],
                             facecolor="none", edgecolor=LINEA, linewidth=1.4))
    ax.text(cx, dy + 4.5, "¿generación < 150?", ha="center", va="center", fontsize=9, color=TINTA)
    flecha(ax, cx, H - 43, cx, dy + 9)

    ops = [(dy - 12, "Seleccionar 12 padres  ·  torneo K=5"),
           (dy - 21, "Cruzar  ·  29 hijos, cruce uniforme"),
           (dy - 30, "Mutar  ·  reemplazo, Pm = 0.02"),
           (dy - 39, "Reemplazar  ·  1 élite + 29 hijos"),
           (dy - 48, "Evaluar los 29 hijos · el élite reutiliza la suya")]
    for y, t in ops:
        paso(y, t, color=AZUL if "Evaluar" in t else None)
    flecha(ax, cx, dy, cx, dy - 12 + h)
    ax.text(cx + 3, dy - 4, "sí", fontsize=8.5, color=TINTA_2)
    for i in range(len(ops) - 1):
        flecha(ax, cx, ops[i][0], cx, ops[i + 1][0] + h)

    # retorno al rombo
    xr = cx + 33
    ax.plot([cx + w / 2, xr, xr], [ops[-1][0] + h / 2, ops[-1][0] + h / 2, dy + 4.5],
            color=TINTA_2, lw=1.3)
    flecha(ax, xr, dy + 4.5, cx + 26, dy + 4.5)
    ax.text(xr + 1.5, (ops[-1][0] + dy) / 2, "generación ++", fontsize=8, color=TINTA_2, rotation=90,
            va="center")

    # salida del bucle
    xl = cx - 36
    yfin = ops[-1][0] - 13
    ax.plot([cx - 26, xl, xl], [dy + 4.5, dy + 4.5, yfin + h / 2], color=TINTA_2, lw=1.3)
    ax.text(xl - 8, dy + 6, "no", fontsize=8.5, color=TINTA_2)
    paso(yfin, "Guardar solución, configuración y bitácora", color=NARANJA)
    flecha(ax, xl, yfin + h / 2, cx - w / 2, yfin + h / 2)
    paso(yfin - 9, "Simular netconvert y la mejor con detalle", color=NARANJA)
    flecha(ax, cx, yfin, cx, yfin - 9 + h)
    flecha(ax, cx, yfin - 9, cx, yfin - 15)
    ax.add_patch(plt.Circle((cx, yfin - 17.5), 2.4, facecolor="none", edgecolor=TINTA, lw=1.3))
    ax.add_patch(plt.Circle((cx, yfin - 17.5), 1.3, color=TINTA))

    guardar(fig, "diag_actividad.png")


if __name__ == "__main__":
    actividad()
    evaluacion()
    codificacion()
    seleccion()
    cruce()
    mutacion()
