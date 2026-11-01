"""
orden de las escenas y geometria de los paneles de la escena de simulacion.

No importa manimgl a proposito: manimgl lee los argumentos de la linea de
comandos al importarse, y renderizar.py necesita estos datos con sus propios
argumentos.
"""

ESCENAS = ["Introduccion", "Arquitectura", "Cromosoma", "CicloAG", "Simulacion", "Evaluacion", "Seleccion",
           "Cruce", "Mutacion", "Elitismo", "Evolucion", "Resultados", "Cierre"]

# cuadro de manim: 8 unidades de alto en proporcion 16:9
ALTO_CUADRO = 8.0
ANCHO_CUADRO = ALTO_CUADRO * 16 / 9

# paneles donde se insertan los clips de SUMO-GUI (en unidades de manim)
SIM_ANCHO = 6.3
SIM_ALTO = SIM_ANCHO * 840 / 1290
SIM_CENTROS = {"netconvert": (-3.45, 0.25), "algoritmo": (3.45, 0.25)}
SIM_INICIO_CLIP = 7.0      # segundo de la escena en que arrancan los clips
SIM_FUNDIDO = 0.8          # duracion del fundido final de la escena


def rect_pixeles(plan, ancho_px=1920, alto_px=1080):
    """(x, y, ancho, alto) en pixeles del panel de un plan, con medidas pares para FFmpeg"""
    escala = alto_px / ALTO_CUADRO
    cx, cy = SIM_CENTROS[plan]

    def par(v):
        return int(round(v / 2)) * 2

    x0 = (cx - SIM_ANCHO / 2 + ANCHO_CUADRO / 2) * escala
    y0 = (ALTO_CUADRO / 2 - (cy + SIM_ALTO / 2)) * escala
    return par(x0), par(y0), par(SIM_ANCHO * escala), par(SIM_ALTO * escala)
