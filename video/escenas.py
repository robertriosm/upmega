"""
video explicativo del algoritmo genetico simple (AGS) de la tesis, con manimgl.

Cada escena es una parte del video; todas las cifras salen de datos.py, que
las lee de los archivos de la corrida. Uso, desde esta carpeta:

    .venv\\Scripts\\manimgl escenas.py Arquitectura          vista previa
    .venv\\Scripts\\manimgl escenas.py Arquitectura -w --hd  escribe salida/Arquitectura.mp4
    .venv\\Scripts\\python renderizar.py                      todas las escenas y el video unido
"""

import sys
import textwrap
from pathlib import Path

import numpy as np
from manimlib import *

# manimgl carga este archivo sin agregar su carpeta a la ruta de importacion
sys.path.insert(0, str(Path(__file__).resolve().parent))
import datos  # noqa: E402
from disposicion import (ESCENAS, SIM_ALTO, SIM_ANCHO, SIM_FUNDIDO,  # noqa: E402,F401
                         SIM_INICIO_CLIP)
from disposicion import SIM_CENTROS as _CENTROS  # noqa: E402

SIM_CENTROS = {p: np.array([x, y, 0]) for p, (x, y) in _CENTROS.items()}

AGS_C = BLUE_C
CTRL_C = GOLD_C
SUMO_C = GREEN_C
TENUE = GREY_B
RESALTE = YELLOW
MALO = RED_C

ETAPAS = ["Población", "Evaluación", "Selección", "Cruce", "Mutación", "Elitismo"]


def texto(t, size=28, color=WHITE, ancho=11.5, **kw):
    """texto de pantalla; una linea demasiado larga se parte en renglones en vez de encogerse"""
    max_c = int(ancho / (0.0046 * size))
    if "\n" not in t and len(t) > max_c:
        t = "\n".join(textwrap.wrap(t, max_c))
        kw.setdefault("alignment", "CENTER")
    return Text(t, font_size=size, fill_color=color, **kw)


def codigo(t, size=24, color=GREY_A):
    return Text(t, font_size=size, font="Consolas", fill_color=color)


def caja(t, color, w=3.2, h=1.2, size=30):
    r = RoundedRectangle(width=w, height=h, corner_radius=0.15, stroke_color=color,
                         stroke_width=3, fill_color=color, fill_opacity=0.12)
    l = texto(t, size, color=color, alignment="CENTER")
    l.set_max_width(w - 0.3)
    l.move_to(r)
    return VGroup(r, l)


def flecha(a, b, color=TENUE, buff=0.15, **kw):
    return Arrow(a, b, buff=buff, fill_color=color, thickness=3, **kw)


def fmt(x, dec=2):
    return f"{x:.{dec}f}"


class Escena(Scene):
    def titular(self, t):
        tit = texto(t, 40).to_edge(UP, buff=0.45).to_edge(LEFT, buff=0.6)
        lin = Line(tit.get_corner(DL) + 0.12 * DOWN, tit.get_corner(DR) + 0.12 * DOWN,
                   stroke_color=RESALTE, stroke_width=2)
        self.play(FadeIn(tit, shift=0.2 * DOWN), ShowCreation(lin))
        self.titulo = VGroup(tit, lin)
        return self.titulo

    def nota(self, t, size=26, color=GREY_A, y=-3.0, espera=None):
        n = texto(t, size, color)
        n.set_max_width(12.8)
        n.move_to(y * UP)
        self.play(FadeIn(n, shift=0.15 * UP))
        self.wait(espera if espera is not None else 1.0 + len(t) / 22)
        return n

    def limpiar(self, run_time=0.8):
        visibles = [m for m in self.mobjects if m is not self.frame]
        if visibles:
            self.play(*[FadeOut(m) for m in visibles], run_time=run_time)

    def mapa(self, activa):
        """cadena de etapas del ciclo en la parte inferior, con la actual resaltada"""
        etiquetas = []
        for e in ETAPAS:
            on = e == activa
            etiquetas.append(texto(e, 20, RESALTE if on else GREY_C))
        fila = VGroup()
        for i, e in enumerate(etiquetas):
            fila.add(e)
            if i < len(etiquetas) - 1:
                fila.add(texto(">", 18, GREY_D))
        fila.arrange(RIGHT, buff=0.22).to_edge(DOWN, buff=0.25)
        marco = SurroundingRectangle(etiquetas[ETAPAS.index(activa)], buff=0.08,
                                     stroke_color=RESALTE, stroke_width=1.5)
        self.add(fila, marco)
        return VGroup(fila, marco)


# ---------------------------------------------------------------- 1
class Introduccion(Escena):
    def construct(self):
        m = datos.meta()
        tit = texto("Un algoritmo genético simple", 54)
        sub = texto("para los semáforos de la zona 1 de la ciudad de Guatemala", 32, GREY_A)
        VGroup(tit, sub).arrange(DOWN, buff=0.3)
        self.play(Write(tit), run_time=1.5)
        self.play(FadeIn(sub, shift=0.2 * UP))
        self.wait(1.5)
        self.play(VGroup(tit, sub).animate.scale(0.6).to_edge(UP, buff=0.5))

        hechos = VGroup(
            caja("110 intersecciones\nsemaforizadas", AGS_C, 3.8, 1.6, 30),
            caja(f"{m['escenario']['demanda']['generados']} vehículos\ncon rutas fijas", SUMO_C, 3.8, 1.6, 30),
            caja("Punto de partida:\nnetconvert, ciclo de 90 s\ny sin desfases", CTRL_C, 3.8, 1.6, 26),
        ).arrange(RIGHT, buff=0.4).shift(0.6 * UP)
        self.play(LaggedStartMap(FadeIn, hechos, shift=0.3 * UP, lag_ratio=0.3))
        self.wait(2)

        pregunta = texto("¿Qué programación semafórica reduce los tiempos de viaje y de espera?", 30, RESALTE)
        pregunta.set_max_width(12.5).next_to(hechos, DOWN, buff=0.7)
        self.play(Write(pregunta))
        self.wait(2.5)
        self.play(FadeOut(hechos), FadeOut(pregunta))

        partes = VGroup(*[texto(t, 30, alignment="LEFT") for t in (
            "1.  Arquitectura: el AGS, el controlador y SUMO",
            "2.  El cromosoma y su decodificación",
            "3.  El ciclo del algoritmo",
            "4.  La simulación y la evaluación: métricas de SUMO y la función J",
            "5.  Selección, cruce, mutación y elitismo",
            "6.  Cómo se obtienen los resultados",
        )]).arrange(DOWN, aligned_edge=LEFT, buff=0.32).shift(0.4 * DOWN)
        self.play(LaggedStartMap(FadeIn, partes, shift=0.2 * RIGHT, lag_ratio=0.25), run_time=3)
        self.wait(3)
        self.limpiar()


# ---------------------------------------------------------------- 2
class Arquitectura(Escena):
    def construct(self):
        m = datos.meta()
        n_veh = m["escenario"]["demanda"]["generados"]
        self.titular("Arquitectura:")

        ags = caja("AGS", AGS_C, 2.6, 1.3, 40).move_to([-5.1, 1.4, 0])
        ctrl = caja("Controlador", CTRL_C, 2.6, 1.3, 32).move_to([0, 1.4, 0])
        sumo = caja("SUMO", SUMO_C, 2.6, 1.3, 40).move_to([5.1, 1.4, 0])
        subs = VGroup(
            texto("PyGAD: población\ny operadores", 22, TENUE).next_to(ags, DOWN, buff=0.2),
            texto("clase Controller:\nfachada y mediador", 22, TENUE).next_to(ctrl, DOWN, buff=0.2),
            texto("simulador microscópico\nde tránsito", 22, TENUE).next_to(sumo, DOWN, buff=0.2),
        )
        self.play(LaggedStartMap(FadeIn, VGroup(ags, ctrl, sumo), shift=0.3 * DOWN, lag_ratio=0.3))
        self.play(FadeIn(subs))
        self.wait(1.5)

        paso = None

        def decir(t, espera=None):
            nonlocal paso
            nuevo = texto(t, 26, GREY_A)
            nuevo.set_max_width(12.8).move_to(2.9 * DOWN)
            self.play(FadeIn(nuevo) if paso is None else FadeTransform(paso, nuevo))
            paso = nuevo
            self.wait(espera if espera is not None else 1.2 + len(t) / 24)

        # 0: lectura inicial por TraCI
        traci_ida = flecha(ctrl[0].get_right() + 0.25 * UP, sumo[0].get_left() + 0.25 * UP, CTRL_C)
        traci_vuelta = flecha(sumo[0].get_left() + 0.25 * DOWN, ctrl[0].get_right() + 0.25 * DOWN, SUMO_C)
        etq_traci = texto("TraCI", 22, CTRL_C).next_to(traci_ida, UP, buff=0.08)
        self.play(GrowArrow(traci_ida), GrowArrow(traci_vuelta), FadeIn(etq_traci))
        decir("Al iniciar, el controlador abre TraCI una sola vez y lee la estructura de los 110 semáforos: "
              "fases, ámbares y mínimos de verde.")
        self.play(FadeOut(VGroup(traci_ida, traci_vuelta, etq_traci)))

        # 1: el AGS pide evaluar un genoma
        f1 = flecha(ags[0].get_right(), ctrl[0].get_left(), AGS_C)
        e1 = texto("evalúa este genoma\n(440 genes)", 18, AGS_C, alignment="CENTER").next_to(f1, UP, buff=0.1)
        self.play(GrowArrow(f1), FadeIn(e1))
        decir("1. El AGS solo pide: evalúa este genoma. No sabe nada de SUMO.")

        # 2: el controlador escribe la red
        red = caja("logics/sid.net.xml", CTRL_C, 3.0, 0.7, 20).move_to([0, -0.9, 0])
        f2 = flecha(subs[1].get_bottom(), red.get_top(), CTRL_C, buff=0.08)
        self.play(GrowArrow(f2), FadeIn(red, shift=0.2 * DOWN))
        decir("2. El controlador decodifica el genoma en 110 planes semafóricos y escribe un archivo de red.")

        # 3: ejecuta SUMO como proceso aparte
        f3 = flecha(red.get_right(), np.array([3.7, -0.9, 0]), CTRL_C)
        e3 = texto("sumo -n red -r rutas\nsin teletransportes, semilla 23", 18, CTRL_C)
        e3.next_to(f3, DOWN, buff=0.05).shift(0.3 * RIGHT)
        self.play(GrowArrow(f3), FadeIn(e3))
        decir("3. Ejecuta SUMO como un proceso independiente, con esa red y las rutas fijas, "
              "hasta que todos llegan o se alcanza el tope de 10 000 s.")

        # 4: SUMO escribe tripinfo
        trip = caja("tripinfo.xml", SUMO_C, 2.6, 0.7, 20).move_to([5.1, -0.9, 0])
        self.play(FadeOut(VGroup(f3, e3)), FadeIn(trip, shift=0.2 * DOWN))
        decir(f"4. SUMO escribe un registro por vehículo: {n_veh} registros con su tiempo de viaje y de espera.")

        # 5: el controlador lee y devuelve
        f5 = flecha(trip.get_left(), red.get_right(), SUMO_C)
        f6 = flecha(ctrl[0].get_left() + 0.35 * DOWN, ags[0].get_right() + 0.35 * DOWN, CTRL_C)
        e6 = texto("tiempos de viaje\ny de espera", 18, CTRL_C, alignment="CENTER").next_to(f6, DOWN, buff=0.1)
        self.play(GrowArrow(f5))
        self.play(GrowArrow(f6), FadeIn(e6))
        decir("5. El controlador lee el tripinfo y devuelve al AGS los tiempos de cada vehículo.")

        calc = texto("J  y  F = 1 / (J + ε)", 24, AGS_C).next_to(subs[0], DOWN, buff=0.35)
        self.play(Write(calc))
        decir("6. El AGS calcula J y la aptitud F. El ciclo se repite para cada individuo.")

        self.play(FadeOut(paso))
        cierre = VGroup(
            texto("El controlador orquesta las dos partes: ni el AGS depende de SUMO ni SUMO del AGS.", 24),
            texto("Cada evaluación es independiente: las de una generación corren en 6 procesos de SUMO a la vez.", 24),
        ).arrange(DOWN, buff=0.2)
        for c in cierre:
            c.set_max_width(12.8)
        cierre.move_to(2.9 * DOWN)
        self.play(FadeIn(cierre[0]))
        self.wait(3)
        self.play(FadeIn(cierre[1]))
        self.wait(3.5)
        self.limpiar()


# ---------------------------------------------------------------- 3
class Cromosoma(Escena):
    def construct(self):
        m = datos.meta()
        self.titular(f"El cromosoma: {m['ga']['num_genes']} genes en tres tramos")

        ancho = 12.0
        tramos = [(110, "110 ciclos", AGS_C, "del mínimo físico\na 120 s"),
                  (220, "220 pesos de reparto", CTRL_C, "de 1 a 100"),
                  (110, "110 desfases", SUMO_C, "de 0 a 100%\ndel ciclo")]
        barra = VGroup()
        for n, nombre, color, rango in tramos:
            r = Rectangle(width=ancho * n / 440, height=0.7, stroke_color=color, stroke_width=2,
                          fill_color=color, fill_opacity=0.35)
            barra.add(r)
        barra.arrange(RIGHT, buff=0).move_to(1.6 * UP)
        nombres = VGroup(*[texto(t[1], 24, t[2]).next_to(r, UP, buff=0.15) for t, r in zip(tramos, barra)])
        rangos = VGroup(*[texto(t[3], 20, TENUE).next_to(r, DOWN, buff=0.15) for t, r in zip(tramos, barra)])
        self.play(LaggedStartMap(GrowFromCenter, barra, lag_ratio=0.3))
        self.play(FadeIn(nombres), FadeIn(rangos))
        self.wait(2)
        n1 = self.nota("Los ámbares no son genes: se copian de la red, porque dependen de la velocidad y no del tránsito.",
                       y=-0.4, espera=4)

        # genes de una interseccion
        genes = VGroup(*[caja(t, c, 2.2, 0.8, 26) for t, c in (
            ("ciclo 45", AGS_C), ("peso 30", CTRL_C), ("peso 12", CTRL_C), ("desfase 25%", SUMO_C))])
        genes.arrange(RIGHT, buff=0.3).move_to(0.4 * DOWN)
        etq = texto("Genes de una intersección de cuatro fases", 24, GREY_A).next_to(genes, UP, buff=0.3)
        self.play(FadeOut(n1), FadeOut(rangos))
        self.play(FadeIn(etq), TransformFromCopy(barra[0], genes[0]),
                  TransformFromCopy(barra[1], genes[1:3]), TransformFromCopy(barra[2], genes[3]))
        self.wait(2)
        self.play(FadeOut(VGroup(barra, nombres, etq)), genes.animate.to_edge(UP, buff=1.4))

        # decodificacion del ciclo
        ciclo, ambar, minimos, pesos = 45, 12, [7, 7], [30, 12]
        verdes = datos.reparto(ciclo, ambar, minimos, pesos)
        extra = ciclo - ambar - sum(minimos)
        esc = 0.26
        pasos = VGroup(
            texto(f"1. Ámbar fijo de la red: {ambar} s", 26),
            texto(f"2. Verde mínimo de seguridad: {minimos[0]} + {minimos[1]} = {sum(minimos)} s", 26),
            texto(f"3. Sobran {ciclo} - {ambar} - {sum(minimos)} = {extra} s, que se reparten en proporción 30 : 12", 26),
            texto(f"4. Por restos mayores, los verdes quedan en {verdes[0]} s y {verdes[1]} s: la suma da {ciclo} s", 26,
                  t2c={f"{verdes[0]} s": GREEN_C, f"{verdes[1]} s": GREEN_C}),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        for p in pasos:
            p.set_max_width(12.5)
        pasos.next_to(genes, DOWN, buff=0.5)
        for p in pasos:
            self.play(FadeIn(p, shift=0.15 * RIGHT))
            self.wait(1.6)

        fases = [(verdes[0], GREEN_C, f"verde {verdes[0]} s"), (6, YELLOW, "6 s"),
                 (verdes[1], GREEN_C, f"verde {verdes[1]} s"), (6, YELLOW, "6 s")]
        plan = VGroup(*[Rectangle(width=d * esc, height=0.7, stroke_width=1, stroke_color=WHITE,
                                  fill_color=c, fill_opacity=0.55) for d, c, _ in fases]).arrange(RIGHT, buff=0)
        plan.next_to(pasos, DOWN, buff=0.45)
        etq_plan = VGroup(*[texto(t, 20).move_to(r) for r, (_, _, t) in zip(plan, fases)])
        self.play(TransformFromCopy(genes[:3], plan), run_time=1.5)
        self.play(FadeIn(etq_plan))
        self.wait(2.5)

        # desfase
        self.play(FadeOut(pasos))
        plan_g = VGroup(plan, etq_plan)
        self.play(plan_g.animate.scale(0.62).move_to(0.5 * UP).align_to(LEFT * 6.0, LEFT))
        esc = esc * 0.62
        reloj = Line(LEFT * 6.0, RIGHT * 6.0, stroke_color=GREY_C, stroke_width=2)
        reloj.next_to(plan_g, DOWN, buff=0.35).align_to(plan_g, LEFT)
        cero = texto("t = 0 (reloj común)", 20, GREY_C).next_to(reloj.get_start(), DOWN, buff=0.15)
        self.play(ShowCreation(reloj), FadeIn(cero))
        d = datos.desfase_segundos(ciclo, 25)
        self.play(plan_g.animate.shift(d * esc * RIGHT), Indicate(genes[3]), run_time=1.5)
        tramo = Arrow(reloj.get_start() + 0.3 * UP, reloj.get_start() + 0.3 * UP + d * esc * RIGHT,
                      buff=0, fill_color=SUMO_C, thickness=3)
        tramo_etq = texto(f"{d} s", 22, SUMO_C).next_to(tramo, UP, buff=0.08)
        marca = texto(f"desfase: 25% de {ciclo} s = {d} s", 24, SUMO_C).next_to(plan_g, UP, buff=0.3)
        self.play(GrowArrow(tramo), FadeIn(tramo_etq), FadeIn(marca))
        n2 = self.nota("El desfase no cambia ninguna duración: solo el instante en que empieza el ciclo. "
                       "Es lo que permite coordinar intersecciones consecutivas.", y=-2.0, espera=5)
        self.play(FadeOut(VGroup(plan_g, reloj, cero, marca, tramo, tramo_etq, n2, genes)))

        # ejemplo real
        antes, despues = datos.tllogic_antes_despues()
        filas = VGroup()
        for nombre, logica, color in (("netconvert", antes, GREY_B), ("algoritmo", despues, AGS_C)):
            dur = [d_ for d_, _ in logica["fases"]]
            barra_r = VGroup(*[Rectangle(width=d_ * 0.085, height=0.6, stroke_width=1, stroke_color=WHITE,
                                         fill_color=GREEN_C if "G" in s else YELLOW, fill_opacity=0.55)
                               for d_, s in logica["fases"]]).arrange(RIGHT, buff=0)
            etqs = VGroup(*[texto(str(d_), 18).move_to(r) for r, d_ in zip(barra_r, dur)])
            info = texto(f"{nombre}: ciclo {sum(dur)} s, desfase {logica['offset']} s", 24, color)
            fila = VGroup(info, VGroup(barra_r, etqs)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
            filas.add(fila)
        filas.arrange(DOWN, aligned_edge=LEFT, buff=0.6).move_to(0.3 * UP).to_edge(LEFT, buff=1.0)
        etq_r = texto("Intersección real 1903163106, antes y después", 26, GREY_A).next_to(filas, UP, buff=0.4).align_to(filas, LEFT)
        self.play(FadeIn(etq_r))
        self.play(LaggedStartMap(FadeIn, filas, shift=0.2 * RIGHT, lag_ratio=0.5))
        self.wait(4)
        self.limpiar()


# ---------------------------------------------------------------- 4
class CicloAG(Escena):
    def construct(self):
        m = datos.meta()
        ga = m["ga"]
        self.titular("El ciclo del algoritmo genético simple")

        centro, rx, ry = 0.25 * DOWN, 4.6, 2.05
        angulos = [150, 90, 30, -30, -90, -150]
        colores = [WHITE, SUMO_C, AGS_C, AGS_C, AGS_C, AGS_C]
        subt = ["30 individuos", "una simulación\npor individuo", f"torneo, τ = {ga['K_tournament']}",
                "uniforme", f"reinicio aleatorio\nPm = {ga['mutation_probability']}", f"{ga['keep_elitism']} individuo"]
        nodos = VGroup()
        for e, a, c, s in zip(ETAPAS, angulos, colores, subt):
            p = centro + np.array([rx * np.cos(np.radians(a)), ry * np.sin(np.radians(a)), 0])
            n = caja(e, c, 2.5, 0.75, 26).move_to(p)
            sub = texto(s, 18, TENUE).next_to(n, DOWN, buff=0.08)
            nodos.add(VGroup(n, sub))
        flujo = ["30 individuos", "30 valores de J", f"{ga['num_parents_mating']} padres", "29 hijos",
                 "29 hijos mutados", "+ 1 élite = 30"]
        flechas, etq_flujo = VGroup(), VGroup()
        for i in range(6):
            a, b = nodos[i][0], nodos[(i + 1) % 6][0]
            if i == 2:    # seleccion, arriba a la derecha, baja a cruce
                f = Arrow(nodos[i].get_bottom(), b.get_top(), buff=0.1, fill_color=GREY_C, thickness=2.5)
            elif i == 5:  # elitismo, abajo a la izquierda, sube a poblacion
                f = Arrow(a.get_top(), nodos[0].get_bottom(), buff=0.1, fill_color=GREY_C, thickness=2.5)
            else:
                f = Arrow(a.get_center(), b.get_center(), buff=0.85, path_arc=-0.35,
                          fill_color=GREY_C, thickness=2.5)
            flechas.add(f)
        trayectos = [Line(nodos[i][0].get_center(), nodos[(i + 1) % 6][0].get_center(), path_arc=-0.35)
                     for i in range(6)]
        for i in range(6):
            t = flujo[i]
            if t:
                e = texto(t, 18, RESALTE)
                if i in (2, 5):
                    e.next_to(flechas[i], RIGHT if i == 2 else LEFT, buff=0.15)
                else:
                    e.move_to(flechas[i].get_center() + 0.42 * (flechas[i].get_center() - centro)
                              / max(np.linalg.norm(flechas[i].get_center() - centro), 1e-6))
                etq_flujo.add(e)

        self.play(LaggedStartMap(FadeIn, nodos, shift=0.2 * UP, lag_ratio=0.15), run_time=2)
        for f in flechas:
            self.play(GrowArrow(f), run_time=0.35)
        self.wait(1)
        self.play(LaggedStartMap(FadeIn, etq_flujo, lag_ratio=0.3), run_time=2.5)
        self.wait(2)

        ini = texto("Generación 0: el individuo 0 es la configuración de netconvert; los otros 29 son aleatorios.",
                    22, GREY_A)
        ini.set_max_width(12.8).to_edge(DOWN, buff=0.35)
        self.play(FadeIn(ini))
        self.wait(4)

        gen = Integer(0, font_size=40, color=RESALTE)
        etq_gen = VGroup(texto("Generación", 28), gen).arrange(RIGHT, buff=0.2).move_to(centro)
        self.play(FadeIn(etq_gen))
        punto = Dot(radius=0.12, fill_color=RESALTE)
        punto.move_to(nodos[0][0].get_center())
        self.add(punto)
        for vuelta in range(3):
            for i in range(6):
                self.play(MoveAlongPath(punto, trayectos[i]), run_time=0.3, rate_func=linear)
            self.play(ChangeDecimalToValue(gen, vuelta + 1), run_time=0.2)
        self.play(ChangeDecimalToValue(gen, ga["num_generations"]), run_time=2)
        self.remove(punto)

        resumen = texto(f"{ga['num_generations']} generaciones · {m['resultado']['evaluaciones']} evaluaciones "
                        f"(30 iniciales + 29 por generación)", 22, GREY_A)
        resumen.set_max_width(12.8).to_edge(DOWN, buff=0.35)
        self.play(FadeTransform(ini, resumen))
        self.wait(3.5)
        self.limpiar()

# ---------------------------------------------------------------- simulacion
# los paneles donde se insertan los clips de SUMO-GUI se definen en disposicion.py


class Simulacion(Escena):
    def construct(self):
        m = datos.meta()
        n_veh = m["escenario"]["demanda"]["generados"]
        w2 = m["fitness"]["w2"]
        planes = [("netconvert", "netconvert", GREY_B), ("algoritmo", "mejor solución del algoritmo", AGS_C)]
        clips = {p: datos.clip_sumo(p) for p, _, _ in planes}
        self.titular("La simulación: qué se mide para calcular la aptitud")

        marcos, etiquetas = VGroup(), VGroup()
        for p, nombre, color in planes:
            marco = Rectangle(width=SIM_ANCHO + 0.1, height=SIM_ALTO + 0.1, stroke_color=color,
                              stroke_width=3).move_to(SIM_CENTROS[p])
            relleno = texto("SUMO", 44, GREY_D).move_to(SIM_CENTROS[p])
            marcos.add(VGroup(marco, relleno))
            etiquetas.add(texto(nombre, 24, color).next_to(marco, UP, buff=0.12))
        self.play(FadeIn(marcos), FadeIn(etiquetas))

        subt = None

        def decir(t, espera=0.0):
            nonlocal subt
            nuevo = texto(t, 24, GREY_A).move_to(3.2 * DOWN)
            self.play(FadeIn(nuevo) if subt is None else FadeTransform(subt, nuevo), run_time=0.6)
            subt = nuevo
            if espera:
                self.wait(espera)

        decir(f"Para evaluar un individuo, SUMO simula los {n_veh} vehículos con su plan semafórico. "
              "Aquí, el mismo corredor con dos planes distintos.")
        self.wait(max(0.0, SIM_INICIO_CLIP - self.time))

        # reloj de la escena = tiempo del clip: los contadores siguen al video de SUMO
        reloj = ValueTracker(0.0)
        reloj.add_updater(lambda mob, dt: mob.increment_value(dt))
        self.add(reloj)

        def cuadro(p):
            c = clips[p]
            i = min(int(reloj.get_value() * c["fps"]), len(c["cuadros"]) - 1)
            return c["cuadros"][i]

        tiempo = always_redraw(lambda: texto(f"tiempo simulado: {cuadro('netconvert')['t']} s", 24, RESALTE)
                               .move_to(etiquetas.get_center()[1] * UP))
        contadores = VGroup(*[
            always_redraw(lambda p=p, color=color, i=i: texto(
                f"detenidos: {cuadro(p)['detenidos']}   espera acumulada: {cuadro(p)['espera_h']:.1f} h",
                22, color).next_to(marcos[i][0], DOWN, buff=0.18))
            for i, (p, _, color) in enumerate(planes)])
        self.add(tiempo, contadores)

        decir("Cada vehículo sigue su ruta fija: en azul se mueve; en rojo está detenido, a 0.1 m/s o menos.", 5.4)
        decir("Los semáforos aplican el plan del individuo. Con netconvert, las colas crecen y no alcanzan a disiparse.", 5.4)
        decir("Cada segundo que un vehículo pasa detenido se suma a su tiempo de espera.", 4.4)
        decir("La simulación continúa hasta que llega el último vehículo.")
        fin_clip = SIM_INICIO_CLIP + max(c["duracion_clip_s"] for c in clips.values())
        self.wait(max(0.0, fin_clip - self.time))
        reloj.clear_updaters()

        # resultado de cada simulacion completa
        finales = VGroup()
        for i, (p, _, color) in enumerate(planes):
            r = datos.medias_tripinfo(p)
            espera_total = r["espera"] * r["vehiculos"] / 3600  # horas-vehiculo, como en la tesis
            finales.add(texto(f"llega el último a los {clips[p]['fin_simulacion_s']} s   "
                              f"espera total: {espera_total:.1f} h", 22, color)
                        .next_to(marcos[i][0], DOWN, buff=0.18))
        self.remove(tiempo)
        self.play(*[FadeTransform(a, b) for a, b in zip(contadores, finales)])
        decir(f"Al terminar, el archivo tripinfo da el tiempo de viaje y de espera de los {n_veh} vehículos.", 3.2)

        cuentas = VGroup()
        for i, (p, _, color) in enumerate(planes):
            r = datos.medias_tripinfo(p)
            cuentas.add(texto(f"J = {fmt(r['viaje'])} + {w2} · {fmt(r['espera'])} = {fmt(r['J'])} s", 26, color)
                        .next_to(marcos[i][0], DOWN, buff=0.18))
        self.play(*[FadeTransform(a, b) for a, b in zip(finales, cuentas)])
        decir("Esa J, convertida en aptitud F = 1 / (J + ε), es lo que el algoritmo usa para comparar individuos.", 4.5)
        self.limpiar(run_time=SIM_FUNDIDO)



# ---------------------------------------------------------------- 5
class Evaluacion(Escena):
    def construct(self):
        a = datos.analisis()
        m = datos.meta()
        w1, w2 = m["fitness"]["w1"], m["fitness"]["w2"]
        n_veh = m["escenario"]["demanda"]["generados"]
        self.titular("Evaluación: de la simulación a J")
        self.mapa("Evaluación")

        t = datos.tripinfo_ejemplo()
        reg = VGroup(*[codigo(l, 22) for l in (
            f'<tripinfo id="{t["id"]}"',
            f'    depart="{t["depart"]}" arrival="{t["arrival"]}"',
            f'    duration="{t["duration"]}" routeLength="{t["routeLength"]}"',
            f'    waitingTime="{t["waitingTime"]}" timeLoss="{t["timeLoss"]}" ... />',
        )]).arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to(1.45 * UP)
        etq = texto("Un registro del archivo tripinfo (vehículo 0, mejor solución)", 22, TENUE).next_to(reg, UP, buff=0.25)
        self.play(FadeIn(etq), Write(reg), run_time=2)
        self.wait(1.5)

        defs = VGroup(
            texto("duration: tiempo de viaje, de la salida a la llegada", 24, t2c={"duration": AGS_C}),
            texto("waitingTime: tiempo de espera, con velocidad de 0.1 m/s o menos", 24, t2c={"waitingTime": CTRL_C}),
            texto("timeLoss: tiempo perdido frente a la velocidad ideal; no entra en J", 24, t2c={"timeLoss": TENUE}),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).next_to(reg, DOWN, buff=0.45)
        for d_ in defs:
            self.play(FadeIn(d_, shift=0.15 * RIGHT))
            self.wait(1.8)

        dur, esp = float(t["duration"]), float(t["waitingTime"])
        esc = 0.16
        barra = VGroup(
            Rectangle(width=(dur - esp) * esc, height=0.55, fill_color=AGS_C, fill_opacity=0.5, stroke_width=1),
            Rectangle(width=esp * esc, height=0.55, fill_color=CTRL_C, fill_opacity=0.6, stroke_width=1),
        ).arrange(RIGHT, buff=0).next_to(defs, DOWN, buff=0.45)
        etq_b = VGroup(texto(f"en movimiento {dur - esp:.0f} s", 18).move_to(barra[0]),
                       texto(f"espera {esp:.0f} s", 18).move_to(barra[1]))
        total = texto(f"viaje {dur:.0f} s", 20, AGS_C).next_to(barra, RIGHT, buff=0.3)
        self.play(GrowFromEdge(barra, LEFT), FadeIn(etq_b), FadeIn(total))
        self.wait(3)
        self.play(FadeOut(VGroup(reg, etq, defs, barra, etq_b, total)))

        # promedios y penalizacion
        prom = VGroup(
            texto(f"Viaje medio y espera media: promedios sobre los {n_veh} vehículos", 28),
            texto("Un vehículo que no llega antes de 10 000 s cuenta con 10 000 s de viaje y de espera:", 24, GREY_A),
            texto("una solución que traba la red recibe una aptitud muy baja.", 24, GREY_A),
        ).arrange(DOWN, buff=0.2).move_to(1.6 * UP)
        self.play(FadeIn(prom[0]))
        self.wait(2)
        self.play(FadeIn(prom[1:]))
        self.wait(4)

        formula = texto(f"J = {w1} · viaje medio + {w2} · espera media", 36,
                        t2c={"viaje medio": AGS_C, "espera media": CTRL_C}).move_to(0.1 * UP)
        apt = texto("F = 1 / (J + ε),   ε = 0.000001", 28, GREY_A).next_to(formula, DOWN, buff=0.3)
        self.play(Write(formula), run_time=1.5)
        self.play(FadeIn(apt))
        self.wait(1)
        expl = texto("PyGAD maximiza F; los resultados se reportan con J, en segundos (menor es mejor).", 24, TENUE)
        expl.next_to(apt, DOWN, buff=0.3)
        self.play(FadeIn(expl))
        self.wait(3)

        v, e_ = a["viaje"], a["espera"]
        ejemplos = VGroup(
            texto(f"netconvert:  {fmt(v['base']['media'])} + {w2} · {fmt(e_['base']['media'])} = {fmt(a['J']['base'])} s", 28),
            texto(f"mejor solución:  {fmt(v['mejor']['media'])} + {w2} · {fmt(e_['mejor']['media'])} = {fmt(a['J']['mejor'])} s",
                  28, t2c={fmt(a['J']['mejor']) + " s": RESALTE}),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25).next_to(expl, DOWN, buff=0.45)
        self.play(FadeIn(ejemplos[0]))
        self.wait(2)
        self.play(FadeIn(ejemplos[1]))
        self.wait(3)
        self.play(FadeOut(VGroup(prom, apt, expl, ejemplos)), formula.animate.move_to(1.2 * UP))
        doble = texto("El viaje ya incluye la espera, así que J = movimiento + 2.1 · espera:", 26)
        doble2 = texto("la espera pesa 2.1, la parte de la demora que el semáforo controla.", 26, GREY_A)
        VGroup(doble, doble2).arrange(DOWN, buff=0.2).next_to(formula, DOWN, buff=0.6)
        self.play(FadeIn(doble))
        self.wait(2)
        self.play(FadeIn(doble2))
        self.wait(3.5)
        self.limpiar()


# ---------------------------------------------------------------- 6
class Seleccion(Escena):
    def construct(self):
        ga = datos.meta()["ga"]
        k = ga["K_tournament"]
        self.titular("Selección por torneo")
        self.mapa("Selección")

        J = [e["J"] for e in datos.evaluaciones() if e["gen"] == 0]
        jmin = min(J)
        barras = VGroup()
        for j in J:
            h = 2.2 * jmin / j
            barras.add(Rectangle(width=0.32, height=max(h, 0.05), stroke_width=0,
                                 fill_color=interpolate_color(MALO, GREEN_C, jmin / j), fill_opacity=0.85))
        barras.arrange(RIGHT, buff=0.08, aligned_edge=DOWN).move_to(1.45 * UP)
        base = Line(barras.get_corner(DL) + 0.1 * LEFT, barras.get_corner(DR) + 0.1 * RIGHT,
                    stroke_color=GREY_C, stroke_width=1.5)
        etq = texto("Población de la generación 0: altura = aptitud F (proporcional a 1/J)", 22, TENUE)
        etq.next_to(base, DOWN, buff=0.2)
        self.play(ShowCreation(base), LaggedStart(*[GrowFromEdge(b, DOWN) for b in barras], lag_ratio=0.04), run_time=2)
        self.play(FadeIn(etq))
        mejor = SurroundingRectangle(barras[int(np.argmin(J))], buff=0.05, stroke_color=RESALTE, stroke_width=2)
        etq_m = texto("netconvert", 18, RESALTE).next_to(mejor, UP, buff=0.08)
        self.play(ShowCreation(mejor), FadeIn(etq_m))
        self.wait(2)

        rng = np.random.RandomState(7)
        padres = VGroup()
        zona_t = texto("Torneo", 24, GREY_A).move_to([-5.6, -1.75, 0])
        zona_p = texto("Padres", 24, GREY_A).move_to([-5.6, -3.0, 0])
        self.play(FadeIn(zona_t), FadeIn(zona_p))
        regla = texto(f"Se sortean {k} individuos con reemplazo; el de mayor aptitud gana y pasa a ser padre.", 24)
        regla.set_max_width(12.8).next_to(etq, DOWN, buff=0.25)
        self.play(FadeIn(regla))

        for n_torneo in range(ga["num_parents_mating"]):
            idx = rng.randint(0, len(J), size=k)
            ganador = idx[int(np.argmin([J[i] for i in idx]))]
            rapido = n_torneo >= 2
            rt = 0.35 if rapido else 1.0
            copias = VGroup(*[barras[i].copy() for i in idx])
            destino = VGroup(*[b.copy().scale(0.45, about_edge=DOWN) for b in copias])
            destino.arrange(RIGHT, buff=0.15, aligned_edge=DOWN)
            destino.next_to(zona_t, RIGHT, buff=0.6).align_to(zona_t, DOWN)
            self.play(*[Indicate(barras[i], scale_factor=1.15, color=RESALTE) for i in sorted(set(idx))], run_time=rt)
            self.play(*[Transform(c, d) for c, d in zip(copias, destino)], run_time=rt)
            gan = copias[list(idx).index(ganador)]
            if not rapido:
                marco_g = SurroundingRectangle(gan, buff=0.06, stroke_color=RESALTE, stroke_width=2)
                gana = texto("gana", 20, RESALTE).next_to(marco_g, UP, buff=0.08)
                self.play(ShowCreation(marco_g), FadeIn(gana), run_time=0.6)
                self.wait(0.6)
                self.play(FadeOut(marco_g), FadeOut(gana), run_time=0.3)
            pos = zona_p.get_right() + RIGHT * (0.6 + 0.45 * len(padres))
            self.play(gan.animate.move_to(pos, aligned_edge=LEFT).align_to(zona_p, DOWN),
                      FadeOut(VGroup(*[c for c in copias if c is not gan])), run_time=rt)
            padres.add(gan)
            if n_torneo == 1:
                self.wait(1)
        self.wait(1)

        self.play(FadeOut(regla), FadeOut(zona_t))
        notas = VGroup(
            texto("Un mismo individuo puede ganar varios torneos: los 12 padres pueden repetirse.", 22, GREY_A),
            texto("El torneo solo compara aptitudes, así que no importa la escala de F.", 22, GREY_A),
            texto("Con τ = 5 la presión es alta: actuando sola, la selección llenaría la población "
                  "con el mejor en unas 3 generaciones.", 22, GREY_A),
        ).arrange(DOWN, buff=0.15)
        for n in notas:
            n.set_max_width(12.8)
        notas.next_to(etq, DOWN, buff=0.25)
        for n in notas:
            self.play(FadeIn(n))
            self.wait(2.8)
        self.wait(1.5)
        self.limpiar()


# ---------------------------------------------------------------- 7
class Cruce(Escena):
    def construct(self):
        self.titular("Cruce uniforme")
        self.mapa("Cruce")

        # emparejamiento en anillo
        n = 12
        anillo = VGroup()
        for i in range(n):
            ang = PI / 2 - TAU * i / n
            p = np.array([np.cos(ang), np.sin(ang), 0]) * 1.5 + np.array([-4.0, 0.6, 0])
            c = Circle(radius=0.24, stroke_color=AGS_C, fill_color=AGS_C, fill_opacity=0.25).move_to(p)
            anillo.add(VGroup(c, texto(str(i), 18).move_to(p)))
        etq_a = texto("12 padres en anillo", 22, TENUE).next_to(anillo, DOWN, buff=0.3)
        self.play(LaggedStartMap(FadeIn, anillo, lag_ratio=0.08), FadeIn(etq_a))
        pares = VGroup()
        for i in range(3):
            pares.add(Line(anillo[i][0].get_center(), anillo[(i + 1) % n][0].get_center(),
                           stroke_color=RESALTE, stroke_width=4))
        expl_a = texto("Cada hijo sale de dos padres\nconsecutivos: 0 con 1, 1 con 2...\nhasta completar 29 hijos.", 22, GREY_A)
        expl_a.next_to(anillo, RIGHT, buff=0.6).shift(0.4 * UP)
        for p in pares:
            self.play(ShowCreation(p), run_time=0.5)
        self.play(FadeIn(expl_a))
        self.wait(3)
        self.play(FadeOut(VGroup(anillo, etq_a, pares, expl_a)))

        # mezcla gen a gen
        rng = np.random.RandomState(3)
        n_g = 14
        va = [45, 60, 38, 90, 72, 30, 12, 55, 41, 88, 23, 67, 5, 50]
        vb = [70, 33, 95, 51, 26, 84, 47, 18, 62, 39, 76, 29, 58, 11]

        def fila(valores, color):
            g = VGroup()
            for v in valores:
                r = Square(side_length=0.62, stroke_color=color, stroke_width=2, fill_color=color, fill_opacity=0.2)
                g.add(VGroup(r, texto(str(v), 20).move_to(r)))
            return g.arrange(RIGHT, buff=0.08)

        A, B = fila(va, AGS_C), fila(vb, ORANGE)
        A.move_to(1.6 * UP)
        B.next_to(A, DOWN, buff=0.35)
        etqA = texto("Padre A", 22, AGS_C).next_to(A, LEFT, buff=0.3)
        etqB = texto("Padre B", 22, ORANGE).next_to(B, LEFT, buff=0.3)
        resto = texto(f"14 de los 440 genes", 20, TENUE).next_to(A, UP, buff=0.2)
        self.play(FadeIn(VGroup(A, B, etqA, etqB, resto)))
        self.wait(1)

        monedas = rng.rand(n_g) < 0.5
        hijo = VGroup()
        etqH = texto("Hijo", 22, RESALTE)
        moneda_fila = VGroup()
        for i in range(n_g):
            de_a = bool(monedas[i])
            m_ = Circle(radius=0.17, stroke_color=WHITE, stroke_width=1.5,
                        fill_color=AGS_C if de_a else ORANGE, fill_opacity=0.8)
            m_.next_to(B[i], DOWN, buff=0.22)
            moneda_fila.add(m_)
        self.play(LaggedStartMap(GrowFromCenter, moneda_fila, lag_ratio=0.06), run_time=1.5)
        for i in range(n_g):
            fuente = A[i] if monedas[i] else B[i]
            hijo.add(fuente.copy())
        destino = hijo.copy().arrange(RIGHT, buff=0.08).next_to(moneda_fila, DOWN, buff=0.35)
        destino.align_to(A, LEFT)
        etqH.next_to(destino, LEFT, buff=0.3)
        self.play(*[TransformFromCopy(A[i] if monedas[i] else B[i], destino[i]) for i in range(n_g)],
                  FadeIn(etqH), run_time=2)
        self.wait(1.5)
        notas = VGroup(
            texto("Una moneda por gen: cada gen viene de A o de B con probabilidad 1/2.", 24),
            texto("La herencia no depende de la posición, así que el orden de los 440 genes no importa.", 22, GREY_A),
            texto("Se cruzan todos los descendientes: probabilidad de cruce igual a 1.", 22, GREY_A),
        ).arrange(DOWN, buff=0.15)
        for n_ in notas:
            n_.set_max_width(12.8)
        notas.next_to(destino, DOWN, buff=0.4)
        for n_ in notas:
            self.play(FadeIn(n_))
            self.wait(2.6)
        self.wait(1)
        self.limpiar()


# ---------------------------------------------------------------- 8
class Mutacion(Escena):
    def construct(self):
        ga = datos.meta()["ga"]
        pm = ga["mutation_probability"]
        self.titular("Mutación por reinicio aleatorio")
        self.mapa("Mutación")

        valores = [45, 33, 95, 90, 26, 30, 47, 55, 62, 88, 76, 67, 5, 11]
        tipos = ["ciclo"] * 5 + ["peso"] * 6 + ["desfase"] * 3
        colores = {"ciclo": AGS_C, "peso": CTRL_C, "desfase": SUMO_C}
        hijo = VGroup()
        for v, t in zip(valores, tipos):
            r = Square(side_length=0.66, stroke_color=colores[t], stroke_width=2,
                       fill_color=colores[t], fill_opacity=0.2)
            hijo.add(VGroup(r, texto(str(v), 20).move_to(r)))
        hijo.arrange(RIGHT, buff=0.1).move_to(1.4 * UP)
        etq = texto("Hijo después del cruce (14 de 440 genes)", 22, TENUE).next_to(hijo, UP, buff=0.25)
        self.play(FadeIn(hijo), FadeIn(etq))

        rng = np.random.RandomState(11)
        u = rng.uniform(0.05, 1.0, len(valores))
        u[0], u[9] = 0.013, 0.007  # los dos genes que mutan en el ejemplo
        sorteos = VGroup(*[texto(f"{x:.3f}" if x < 0.1 else f"{x:.2f}", 18,
                                 MALO if x < pm else GREY_B).next_to(g, DOWN, buff=0.2)
                           for x, g in zip(u, hijo)])
        regla = texto(f"Cada gen sortea un número entre 0 y 1; si sale menor que Pm = {pm}, el gen se reemplaza.", 24)
        regla.set_max_width(12.8).next_to(sorteos, DOWN, buff=0.4)
        self.play(FadeIn(regla))
        self.play(LaggedStartMap(FadeIn, sorteos, lag_ratio=0.08), run_time=1.5)
        self.wait(1.5)

        nuevos = {0: 83, 9: 14}
        for i, nv in nuevos.items():
            g = hijo[i]
            self.play(Indicate(g, color=MALO), run_time=0.8)
            nuevo = texto(str(nv), 20, RESALTE).move_to(g[1])
            self.play(Transform(g[1], nuevo))
        ej = texto("El gen de ciclo 45 s se reemplaza por 83 s, sorteado entre el mínimo físico y 120 s.", 24, GREY_A)
        ej.set_max_width(12.8).next_to(regla, DOWN, buff=0.3)
        self.play(FadeIn(ej))
        self.wait(3)
        notas = VGroup(
            texto(f"Con Pm = {pm}, en promedio cambian unos 9 de los 440 genes de cada hijo.", 24),
            texto("Es un salto dentro de todo el rango del gen, no un ajuste pequeño: por eso Pm se mantiene baja,", 22, GREY_A),
            texto("entre 1/440 y 1/30, como recomienda la literatura.", 22, GREY_A),
        ).arrange(DOWN, buff=0.15)
        for n_ in notas:
            n_.set_max_width(12.8)
        notas.next_to(ej, DOWN, buff=0.4)
        for n_ in notas:
            self.play(FadeIn(n_))
            self.wait(2.5)
        self.wait(1)
        self.limpiar()


# ---------------------------------------------------------------- 9
class Elitismo(Escena):
    def construct(self):
        self.titular("Elitismo: la nueva generación")
        self.mapa("Elitismo")

        def individuo(color, op=0.5):
            return Circle(radius=0.2, stroke_color=color, stroke_width=2, fill_color=color, fill_opacity=op)

        vieja = VGroup(*[individuo(GREY_B, 0.3) for _ in range(30)]).arrange_in_grid(3, 10, buff=0.18)
        vieja.move_to([-3.6, 0.9, 0])
        mejor = vieja[0]
        mejor.set_fill(RESALTE, 0.9).set_stroke(RESALTE)
        etq_v = texto("Generación g", 24, GREY_A).next_to(vieja, UP, buff=0.3)
        hijos = VGroup(*[individuo(AGS_C) for _ in range(29)]).arrange_in_grid(3, 10, buff=0.18)
        hijos.move_to([3.6, 0.9, 0])
        etq_h = texto("29 hijos mutados", 24, AGS_C).next_to(hijos, UP, buff=0.3)
        self.play(FadeIn(vieja), FadeIn(etq_v))
        self.play(FadeIn(hijos), FadeIn(etq_h))
        self.wait(1)

        nueva_pos = VGroup(*[individuo(GREY_B, 0) for _ in range(30)]).arrange_in_grid(3, 10, buff=0.18)
        nueva_pos.move_to([0, -1.5, 0])
        etq_n = texto("Generación g + 1", 24, RESALTE).next_to(nueva_pos, UP, buff=0.25)
        self.play(FadeIn(etq_n))
        elite = mejor.copy()
        self.play(elite.animate.move_to(nueva_pos[0]), run_time=1.2)
        self.play(*[h.animate.move_to(p) for h, p in zip(hijos, nueva_pos[1:])], run_time=1.5)
        self.play(FadeOut(vieja), FadeOut(etq_v), FadeOut(etq_h))
        self.wait(0.5)

        notas = VGroup(
            texto("El mejor individuo pasa sin cambios: la mejor aptitud nunca empeora de una generación a otra.", 24),
            texto("No garantiza el óptimo global en 150 generaciones: esa convergencia solo es asintótica.", 22, GREY_A),
            texto("La nueva población de 30 vuelve a la evaluación, y el ciclo se repite.", 22, GREY_A),
        ).arrange(DOWN, buff=0.15)
        for n_ in notas:
            n_.set_max_width(12.8)
        notas.move_to(2.2 * UP)
        for n_ in notas:
            self.play(FadeIn(n_))
            self.wait(2.8)
        self.wait(1)
        self.limpiar()


# ---------------------------------------------------------------- 10
class Evolucion(Escena):
    def construct(self):
        a = datos.analisis()
        conv = a["convergencia"]
        self.titular("Cómo avanza la búsqueda")

        J0 = 400  # el eje x se dibuja en J = 0; se grafica J - J0 y se rotula con J
        ejes = Axes(x_range=(0, 150, 25), y_range=(0, 500, 100), width=10.5, height=4.6,
                    axis_config=dict(stroke_color=GREY_C, include_tip=False))
        ejes.x_axis.add_numbers(font_size=20, excluding=[])
        for v in range(0, 501, 100):
            ejes.add(texto(str(v + J0), 20).next_to(ejes.y_axis.n2p(v), LEFT, buff=0.15))
        ejes.move_to(0.05 * UP + 0.4 * RIGHT)
        tx = texto("generación", 22, TENUE).next_to(ejes.x_axis, DOWN, buff=0.45)
        ty = texto("J del mejor (s)", 22, TENUE).rotate(PI / 2).next_to(ejes.y_axis, LEFT, buff=0.75)
        self.play(ShowCreation(ejes), FadeIn(tx), FadeIn(ty))

        curva = datos.curva_mejor()
        puntos = []
        for (g0, j0), (g1, _) in zip(curva, curva[1:]):
            puntos += [ejes.c2p(g0, min(j0, 900) - J0), ejes.c2p(g1, min(j0, 900) - J0)]
        puntos.append(ejes.c2p(curva[-1][0], curva[-1][1] - J0))
        linea = VMobject(stroke_color=AGS_C, stroke_width=4).set_points_as_corners(puntos)
        self.play(ShowCreation(linea), run_time=5, rate_func=linear)

        def marca(g, j, t, dir_):
            d = Dot(ejes.c2p(g, j - J0), radius=0.07, fill_color=RESALTE)
            l = texto(t, 20, RESALTE).next_to(d, dir_, buff=0.15)
            return VGroup(d, l)

        js = conv["J_por_generacion"]
        g_mejor = conv["generacion_del_mejor"]
        marcas = [marca(0, js["0"], f"{js['0']} s: netconvert", RIGHT),
                  marca(50, js["50"], f"generación 50: {js['50']} s", UP),
                  marca(g_mejor, conv["mejor_J"], f"mejor, generación {g_mejor}: {conv['mejor_J']} s", UP)]
        for mk in marcas:
            self.play(FadeIn(mk))
            self.wait(1.2)
        frac = round(100 * conv["mejora_0_50"] / (js["0"] - conv["mejor_J"]))
        n1 = texto(f"El {frac}% de la mejora se obtiene en las primeras 50 generaciones; "
                   f"en las últimas 50, solo {conv['mejora_ultimas_50']} s.", 22, GREY_A)
        n1.set_max_width(12.8).to_edge(DOWN, buff=0.25)
        self.play(FadeIn(n1))
        self.wait(4)
        tb = datos.trabadas_por_bloque()
        pct = [100 * b["trabadas"] / b["total"] for b in tb[1:]]
        n2 = texto(f"Traban la red 18 de los 29 individuos aleatorios iniciales; después, "
                   f"{pct[0]:.1f}%, {pct[1]:.1f}% y {pct[2]:.1f}% por bloque de 50 generaciones.", 22, GREY_A)
        n2.set_max_width(12.8).to_edge(DOWN, buff=0.25)
        self.play(FadeTransform(n1, n2))
        self.wait(4.5)
        self.limpiar()


# ---------------------------------------------------------------- 11
class Resultados(Escena):
    def construct(self):
        a = datos.analisis()
        self.titular("Cómo se obtienen los resultados")
        intro = texto("Al terminar, se vuelven a simular netconvert y la mejor solución pidiendo a SUMO\n"
                      "todas sus salidas: por vehículo, por arista y agregadas.", 26, GREY_A)
        intro.move_to(2.2 * UP)
        self.play(FadeIn(intro))
        self.wait(4)

        metricas = [("Viaje medio", a["viaje"]["base"]["media"], a["viaje"]["mejor"]["media"]),
                    ("Espera media", a["espera"]["base"]["media"], a["espera"]["mejor"]["media"]),
                    ("Tiempo perdido", a["tiempo_perdido_media"]["base"], a["tiempo_perdido_media"]["mejor"]),
                    ("J", a["J"]["base"], a["J"]["mejor"])]
        esc = 3.2 / max(b for _, b, _ in metricas)
        grupos = VGroup()
        for nombre, b, mj in metricas:
            rb = Rectangle(width=0.7, height=b * esc, stroke_width=0, fill_color=GREY_B, fill_opacity=0.8)
            rm = Rectangle(width=0.7, height=mj * esc, stroke_width=0, fill_color=AGS_C, fill_opacity=0.9)
            par = VGroup(rb, rm).arrange(RIGHT, buff=0.12, aligned_edge=DOWN)
            vb = texto(fmt(b), 18, GREY_B).next_to(rb, UP, buff=0.08)
            vm = texto(fmt(mj), 18, AGS_C).next_to(rm, UP, buff=0.08)
            cambio = texto(f"{100 * (mj - b) / b:+.2f}%", 22, RESALTE)
            n = texto(nombre, 22).next_to(par, DOWN, buff=0.15)
            cambio.next_to(n, DOWN, buff=0.1)
            grupos.add(VGroup(par, vb, vm, n, cambio))
        grupos.arrange(RIGHT, buff=1.0, aligned_edge=DOWN).to_edge(DOWN, buff=0.4)
        ley = VGroup(
            VGroup(Square(0.25, fill_color=GREY_B, fill_opacity=0.8, stroke_width=0), texto("netconvert", 20)).arrange(RIGHT, buff=0.15),
            VGroup(Square(0.25, fill_color=AGS_C, fill_opacity=0.9, stroke_width=0), texto("algoritmo", 20)).arrange(RIGHT, buff=0.15),
        ).arrange(RIGHT, buff=0.5).next_to(intro, DOWN, buff=0.3)
        self.play(FadeIn(ley))
        for g in grupos:
            self.play(GrowFromEdge(g[0], DOWN), FadeIn(g[1:]), run_time=0.9)
        self.wait(4)
        self.play(FadeOut(VGroup(intro, ley, grupos)))

        r = datos.robustez_resumen()
        pregunta = texto(f"¿Y con otras demandas y otras semillas del simulador? {r['casos']} combinaciones", 28)
        pregunta.set_max_width(12.8).move_to(2.3 * UP)
        self.play(FadeIn(pregunta))
        planes = [("netconvert", GREY_B), ("algoritmo", AGS_C), ("uniforme", CTRL_C)]
        nombres = {"netconvert": "netconvert", "algoritmo": "algoritmo", "uniforme": "ciclo uniforme de 51 s"}
        esc2 = 2.6 / max(r["mediana_J"].values())
        cols = VGroup()
        for p, c in planes:
            rr = Rectangle(width=1.1, height=r["mediana_J"][p] * esc2, stroke_width=0, fill_color=c, fill_opacity=0.85)
            v = texto(f"{r['mediana_J'][p]} s", 22, c).next_to(rr, UP, buff=0.1)
            n = texto(nombres[p], 22).next_to(rr, DOWN, buff=0.15)
            tr = texto(f"trabó la red en {r['trabadas'][p]} de {r['casos']}", 20,
                       MALO if r["trabadas"][p] else GREEN_C).next_to(n, DOWN, buff=0.1)
            cols.add(VGroup(rr, v, n, tr))
        cols.arrange(RIGHT, buff=1.6, aligned_edge=DOWN).move_to(0.5 * DOWN)
        tit_c = texto("Mediana de J en las 35 combinaciones", 22, TENUE).next_to(pregunta, DOWN, buff=0.3)
        self.play(FadeIn(tit_c))
        for c in cols:
            self.play(GrowFromEdge(c[0], DOWN), FadeIn(c[1:]), run_time=0.9)
        self.wait(2)
        conc = VGroup(
            texto(f"El algoritmo supera a netconvert en las {r['mejor_que_netconvert']} combinaciones; "
                  f"la mediana de las reducciones por combinación es {r['reduccion_vs_netconvert']}%.", 22),
            texto(f"El {a['J']['mejor']} s de la optimización es el mejor de los 35 casos: parte del 51.17% "
                  "es ajuste a esa realización.", 22, GREY_A),
        ).arrange(DOWN, buff=0.15)
        for c in conc:
            c.set_max_width(12.8)
        conc.to_edge(DOWN, buff=0.35)
        for c in conc:
            self.play(FadeIn(c))
            self.wait(3.5)
        self.wait(1)
        self.limpiar()


# ---------------------------------------------------------------- 12
class Cierre(Escena):
    def construct(self):
        a = datos.analisis()
        r = datos.robustez_resumen()
        reduccion = round(100 * (a["J"]["base"] - a["J"]["mejor"]) / a["J"]["base"], 2)
        self.titular("En resumen")
        puntos = VGroup(*[texto(t, 28, alignment="LEFT") for t in (
            "El controlador separa al algoritmo del simulador y orquesta cada evaluación.",
            "Cada individuo es un plan para 110 semáforos: ciclos, repartos y desfases.",
            "Selección, cruce, mutación y elitismo transforman la población generación tras generación.",
            "J resume el viaje y la espera de los 2002 vehículos de cada simulación.",
            f"La mejor solución reduce J en {reduccion}%; con otras realizaciones, la mediana "
            f"de las reducciones es {r['reduccion_vs_netconvert']}% y nunca traba la red.",
        )]).arrange(DOWN, aligned_edge=LEFT, buff=0.38)
        for p in puntos:
            p.set_max_width(12.6)
        puntos.next_to(self.titulo, DOWN, buff=0.7).align_to(self.titulo, LEFT)
        for p in puntos:
            self.play(FadeIn(p, shift=0.2 * RIGHT))
            self.wait(2.6)
        self.wait(2)
        self.limpiar()

