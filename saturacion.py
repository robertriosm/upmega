"""
diagrama fundamental de la red: flujo Q contra densidad K, medido solo con TraCI.

Barre varios niveles de demanda sobre la misma red y, en cada uno, mide en
intervalos fijos la densidad y el flujo de toda la red con las definiciones
generalizadas de Edie:

    K = vehiculos-hora en la red      / (duracion del intervalo x km de carril)
    Q = vehiculos-km recorridos       / (duracion del intervalo x km de carril)

La densidad critica se estima solo con la rama de carga (los intervalos dentro
de la ventana en que entran vehiculos): es el inicio de la meseta de capacidad,
donde agregar vehiculos deja de aumentar el flujo. Los intervalos posteriores
(descarga o bloqueo) se grafican aparte, porque por histeresis no pertenecen a
la curva. Con eso se responde cuantos vehiculos soporta la red antes de
saturarse, que es lo que hace falta para correr el GA en su condicion mas
exigente.

La demanda se genera con demand.generate, la misma que usa main.py, asi que el
numero de vehiculos solicitados aqui es directamente el valor de --num-of-cars.
La simulacion usa las banderas de Controller.sim_flags, de modo que se mide
bajo las mismas condiciones que las evaluaciones del GA (sin teletransportes).

Uso:
    python saturacion.py
    python saturacion.py --cars 500 1000 2000 4000 --period 120
    python saturacion.py --net logics/4226.net.xml    (otra configuracion semaforica)
    python saturacion.py --solo-analisis              (recalcular y graficar sin simular)

Escribe en saturacion/:
    {tag}.intervalos.csv   un renglon por intervalo y nivel de demanda
    {tag}.resumen.csv      un renglon por nivel de demanda
    {tag}.meta.json        configuracion, densidad critica y recomendacion
    {tag}.qk.png           Q contra K, y densidad maxima por nivel de demanda
"""

import argparse
import csv
import inspect
import json
import os
import subprocess
import xml.etree.ElementTree as ET
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime

import numpy as np
import traci
import traci.constants as tc
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

import demand
from controller import Controller


DIR = "saturacion"
CARS = [250, 500, 1000, 1500, 2000, 3000, 4000, 6000, 8000]
PUERTO_BASE = 8900  # uno por nivel de demanda, lejos del 8813 que usa main.py
# ventana en que entran vehiculos, la misma que usa demand.generate por defecto:
# los intervalos que terminan dentro de ella son la rama de carga
VENTANA = inspect.signature(demand.generate).parameters["end"].default

# misma paleta que graficas.py. La rampa de demanda es la azul ordinal de la
# paleta validada: no baja de 250 para que el nivel mas bajo siga visible
AZUL = "#2a78d6"
TINTA, TINTA_2, APAGADO = "#0b0b0b", "#52514e", "#898781"
REJILLA, EJE, FONDO = "#e1e0d9", "#c3c2b7", "#fcfcfb"
RAMPA = LinearSegmentedColormap.from_list("demanda", ["#86b6ef", "#2a78d6", "#0d366b"])

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
    "figure.facecolor": FONDO,
    "axes.facecolor": FONDO,
})


def parse_args():
    base = Controller()
    parser = argparse.ArgumentParser(
        description="Diagrama fundamental (Q contra K) de la red para encontrar su saturacion")
    parser.add_argument("--cars", type=int, nargs="+", default=CARS, metavar="N",
                        help="vehiculos solicitados por nivel de demanda, como en --num-of-cars "
                             f"de main.py (default {' '.join(map(str, CARS))})")
    parser.add_argument("--net", default=base.NETWORK,
                        help=f"red a medir (default {base.NETWORK}, la de netconvert). "
                             "La demanda siempre se genera sobre la red base")
    parser.add_argument("--demand-seed", type=int, default=42, metavar="S",
                        help="semilla de randomTrips, la misma de main.py (default 42)")
    parser.add_argument("--period", type=float, default=120, metavar="T",
                        help="duracion de cada intervalo de medicion en segundos (default 120). "
                             "Conviene que no sea menor que el ciclo mas largo de la red, "
                             "para que cada punto promedie ciclos completos")
    parser.add_argument("--workers", type=int, default=6, metavar="W",
                        help="simulaciones en paralelo (default 6)")
    parser.add_argument("--max-steps", type=int, default=base.MAX_STEPS,
                        help=f"tope de pasos por simulacion (default {base.MAX_STEPS}, el del GA)")
    parser.add_argument("--max-quiet", type=int, default=base.MAX_QUIET,
                        help=f"pasos seguidos sin llegadas para dar la red por trabada "
                             f"(default {base.MAX_QUIET}, el del GA)")
    parser.add_argument("--out", default=DIR, help=f"carpeta de resultados (default {DIR})")
    parser.add_argument("--solo-analisis", action="store_true",
                        help="no simular: recalcular densidad critica, recomendacion y grafica "
                             "a partir de los CSV que ya estan en --out")
    return parser.parse_args()


def admite_autos(lane):
    """
    las aceras y ciclovias que importa netconvert son carriles de la arista,
    pero un auto no puede ocuparlos: si se contaran, inflarian los km de
    carril y bajarian artificialmente la densidad
    """
    if "passenger" in traci.lane.getDisallowed(lane):
        return False
    permitidos = traci.lane.getAllowed(lane)
    return not permitidos or "passenger" in permitidos


def geometria():
    """
    km de carril utiles de cada arista.

    Se excluyen las aristas internas (las que empiezan con ':'), que son el
    recorrido dentro de cada interseccion: un vehiculo detenido en rojo esta
    en la arista de aproximacion, no ahi.
    """
    km = {}
    for arista in traci.edge.getIDList():
        if arista.startswith(":"):
            continue
        carriles = [f"{arista}_{i}" for i in range(traci.edge.getLaneNumber(arista))]
        utiles = [c for c in carriles if admite_autos(c)]
        if utiles:
            km[arista] = len(utiles) * traci.lane.getLength(utiles[0]) / 1000
    return km


def salidas_programadas(rutas):
    """
    instantes de salida de cada vehiculo segun el archivo de rutas, ordenados.
    Comparados con las salidas reales dan la cola de insercion: vehiculos que
    ya debian entrar a la red y no caben, la senal mas temprana de saturacion
    """
    return np.sort([float(v.get("depart")) for v in ET.parse(rutas).getroot().iter("vehicle")])


def medir(trabajo):
    """
    corre una simulacion por TraCI y devuelve (intervalos, resumen).

    Usa suscripciones: SUMO manda el conteo y la velocidad media de todas las
    aristas junto con la respuesta de cada paso, en vez de dos consultas por
    arista y por paso, que con cientos de aristas haria la medicion muy lenta.
    """
    cars, generados, rutas, red, periodo, max_pasos, max_silencio, puerto = trabajo

    ctrl = Controller(network=red, routes=rutas)
    traci.start([ctrl.SUMO_BINARY, "-n", red, "-r", rutas] + ctrl.sim_flags(),
                port=puerto, stdout=subprocess.DEVNULL)

    try:
        version = traci.getVersion()[1]
        dt = traci.simulation.getDeltaT()
        km = geometria()
        km_total = sum(km.values())
        programadas = salidas_programadas(rutas)

        for arista in km:
            traci.edge.subscribe(arista, [tc.LAST_STEP_VEHICLE_NUMBER, tc.LAST_STEP_MEAN_SPEED])
        traci.simulation.subscribe([tc.VAR_ARRIVED_VEHICLES_NUMBER,
                                    tc.VAR_DEPARTED_VEHICLES_NUMBER,
                                    tc.VAR_TELEPORT_STARTING_VEHICLES_NUMBER,
                                    tc.VAR_MIN_EXPECTED_VEHICLES])

        pasos_intervalo = max(1, int(round(periodo / dt)))
        duracion = pasos_intervalo * dt
        intervalos = []

        def vacio():
            return {"veh_s": 0.0, "veh_m": 0.0, "llegadas": 0, "salidas": 0,
                    "teleports": 0, "cola_max": 0}

        acc = vacio()
        pasos, silencio, salidas_total, llegadas_total, teleports_total = 0, 0, 0, 0, 0
        esperados = traci.simulation.getMinExpectedNumber()

        while esperados > 0 and pasos < max_pasos:
            traci.simulationStep()
            pasos += 1
            t = pasos * dt

            sim = traci.simulation.getSubscriptionResults()
            llegadas = sim[tc.VAR_ARRIVED_VEHICLES_NUMBER]
            salidas = sim[tc.VAR_DEPARTED_VEHICLES_NUMBER]
            teleports = sim[tc.VAR_TELEPORT_STARTING_VEHICLES_NUMBER]
            esperados = sim[tc.VAR_MIN_EXPECTED_VEHICLES]

            salidas_total += salidas
            llegadas_total += llegadas
            teleports_total += teleports
            cola = int(np.searchsorted(programadas, t, side="right")) - salidas_total

            # la velocidad media de una arista vacia es su velocidad maxima, no
            # un dato: solo se acumula donde hay vehiculos
            for r in traci.edge.getAllSubscriptionResults().values():
                n = r[tc.LAST_STEP_VEHICLE_NUMBER]
                if n:
                    acc["veh_s"] += n * dt
                    acc["veh_m"] += n * r[tc.LAST_STEP_MEAN_SPEED] * dt

            acc["llegadas"] += llegadas
            acc["salidas"] += salidas
            acc["teleports"] += teleports
            acc["cola_max"] = max(acc["cola_max"], cola)

            # el ultimo intervalo incompleto se descarta: promediar menos tiempo
            # que el periodo mezclaria puntos con distinto soporte
            if pasos % pasos_intervalo == 0:
                K = acc["veh_s"] / duracion / km_total
                Q = acc["veh_m"] / 1000 / (duracion / 3600) / km_total
                intervalos.append({
                    "solicitados": cars,
                    "generados": generados,
                    "t_ini": round(t - duracion, 3),
                    "t_fin": round(t, 3),
                    "K_veh_km_carril": round(K, 4),
                    "Q_veh_h_carril": round(Q, 3),
                    "V_km_h": round(Q / K, 3) if K > 0 else None,
                    "vehiculos_en_red": round(acc["veh_s"] / duracion, 2),
                    "llegadas": acc["llegadas"],
                    "salidas": acc["salidas"],
                    "cola_insercion_max": acc["cola_max"],
                    "teleports": acc["teleports"],
                })
                acc = vacio()

            # mismo guardia que Controller.step_until_done: sin llegadas durante
            # varios minutos simulados, la red esta trabada
            silencio = 0 if llegadas > 0 else silencio + 1
            if silencio >= max_silencio:
                break

        K_max = max((i["K_veh_km_carril"] for i in intervalos), default=0.0)
        Q_max = max((i["Q_veh_h_carril"] for i in intervalos), default=0.0)

        resumen = {
            "solicitados": cars,
            "generados": generados,
            "duracion_s": round(pasos * dt, 1),
            "llegaron": llegadas_total,
            "sin_terminar": esperados,
            "trabada": esperados > 0,
            "teleports": teleports_total,
            "cola_insercion_max": max((i["cola_insercion_max"] for i in intervalos), default=0),
            "K_max": K_max,
            "Q_max": Q_max,
            "intervalos": len(intervalos),
            "km_carril": round(km_total, 3),
            "aristas": len(km),
            "sumo": version,
        }
        return intervalos, resumen

    finally:
        traci.close()


def es_carga(intervalo, ventana):
    """
    un intervalo es de carga si termina dentro de la ventana en que entran
    vehiculos. Los posteriores son la descarga de la red o escenarios ya trabados
    """
    return intervalo["t_fin"] <= ventana


def curva_mediana(K, Q, por_grupo=8):
    """
    mediana de K y de Q por grupos de intervalos consecutivos en densidad. Los
    grupos de tamano fijo se adaptan a donde hay puntos: con franjas de ancho
    fijo, la rama congestionada, que tiene pocos intervalos, quedaria con huecos.
    Con grupos de 6, tres o cuatro intervalos transitorios de las demandas que
    despues traban la red formaban un pico falso cerca de K = 32; con 8 la curva
    muestra la meseta sin ese artefacto
    """
    orden = np.argsort(K)
    grupos = np.array_split(orden, max(1, int(np.ceil(len(K) / por_grupo))))
    return ([round(float(np.median(K[g])), 3) for g in grupos],
            [round(float(np.median(Q[g])), 2) for g in grupos])


def densidad_critica(intervalos, ventana, ancho=2.5, minimo=5, umbral=0.95):
    """
    inicio de la meseta de capacidad de la rama de carga.

    Solo se usan los intervalos de carga. Los posteriores son la descarga de la
    red o escenarios ya trabados: por histeresis tienen menos flujo para la misma
    densidad y, mezclados con la carga, forman una nube que no es la curva de la
    red. Medido en esta red, la rama de carga sola sube casi en linea recta,
    forma una meseta y luego cae: la forma trapezoidal de una red con semaforos.

    Los intervalos de carga se agrupan en franjas de 'ancho' veh/km/carril y se
    toma la mediana de Q de cada franja con al menos 'minimo' intervalos. La
    mediana no se deja arrastrar por los pocos intervalos transitorios de flujo
    muy alto de las demandas que despues traban la red. El flujo de capacidad es
    la mayor de esas medianas, y la densidad critica es la primera franja cuya
    mediana alcanza 'umbral' (95%) de ese flujo: el punto donde agregar
    vehiculos deja de aumentar el flujo. Medido en esta red, con franjas de 1.5
    a 3 veh/km/carril y umbrales de 90 o 95% el resultado queda entre 9.8 y 11.3.

    La saturacion se da por alcanzada si se observo la rama congestionada: al
    menos 'minimo' intervalos de carga con mas del doble de la densidad critica
    y una mediana de flujo por debajo del umbral.
    """
    carga = [i for i in intervalos if es_carga(i, ventana)]
    if not carga:
        return None
    K = np.array([i["K_veh_km_carril"] for i in carga])
    Q = np.array([i["Q_veh_h_carril"] for i in carga])

    bordes = np.arange(0, K.max() + ancho, ancho)
    franjas = []
    for a, b in zip(bordes[:-1], bordes[1:]):
        dentro = (K >= a) & (K < b)
        if dentro.sum() >= minimo:
            franjas.append((float((a + b) / 2), float(np.median(Q[dentro]))))
    if not franjas:
        return None

    q_cap = max(q for _, q in franjas)
    k_c = next(k for k, q in franjas if q >= umbral * q_cap)
    congestion = Q[K > 2 * k_c]
    alcanzada = len(congestion) >= minimo and float(np.median(congestion)) < umbral * q_cap
    curva_K, curva_Q = curva_mediana(K, Q)

    return {
        "k_c": round(k_c, 3),
        "q_capacidad": round(q_cap, 2),
        "saturacion_alcanzada": bool(alcanzada),
        "metodo": f"rama de carga (t_fin <= {ventana} s); mediana de Q por franjas de {ancho} "
                  f"veh/km/carril con al menos {minimo} intervalos; k_c = primera franja que "
                  f"alcanza el {int(umbral * 100)}% del flujo de capacidad",
        "intervalos_de_carga": len(carga),
        "curva_K": curva_K,
        "curva_Q": curva_Q,
    }


def recomendar(resumenes, critica):
    """
    dos lecturas de la saturacion, de menos a mas exigente:

    - capacidad: la mayor demanda cuya densidad maxima no pasa de la critica y
      que no traba la red. La red opera en la rama libre, en su capacidad o
      por debajo.
    - limite: la mayor demanda que la red todavia logra despejar, aunque pase
      por la rama congestionada. Por encima de esta, la red se traba.
    """
    orden = sorted(resumenes, key=lambda r: r["solicitados"])
    sanas = [r for r in orden if not r["trabada"]]

    capacidad = None
    if critica and critica["saturacion_alcanzada"]:
        bajo = [r for r in sanas if r["K_max"] <= critica["k_c"]]
        capacidad = bajo[-1]["solicitados"] if bajo else None

    trabadas = [r["solicitados"] for r in orden if r["trabada"]]
    return {
        "capacidad_solicitados": capacidad,
        "limite_solicitados": sanas[-1]["solicitados"] if sanas else None,
        "primera_trabada_solicitados": trabadas[0] if trabadas else None,
    }


def estilo(ax):
    ax.set_axisbelow(True)
    ax.grid(True, color=REJILLA, linewidth=0.8)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color(EJE)
    ax.tick_params(colors=APAGADO, length=0, labelsize=10)


def graficar(intervalos, resumenes, critica, destino, red, ventana):
    niveles = sorted(r["solicitados"] for r in resumenes)
    generados = {r["solicitados"]: r["generados"] for r in resumenes}
    trabo = {r["solicitados"]: r["trabada"] for r in resumenes}
    tono = {n: RAMPA(i / (len(niveles) - 1) if len(niveles) > 1 else 1.0)
            for i, n in enumerate(niveles)}

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5),
                                   gridspec_kw={"width_ratios": [1.6, 1]})
    estilo(ax1)
    estilo(ax2)

    # panel 1: los intervalos posteriores a la ventana de demanda (descarga o
    # bloqueo) van primero, en gris y huecos: son la nube que no pertenece a la
    # curva, y asi quedan detras sin competir con la rama de carga
    posteriores = [i for i in intervalos if not es_carga(i, ventana)]
    ax1.scatter([p["K_veh_km_carril"] for p in posteriores],
                [p["Q_veh_h_carril"] for p in posteriores],
                s=30, marker="o", facecolors="none", edgecolors=EJE, linewidths=1.0, zorder=2,
                label="después de la ventana de demanda (descarga o bloqueo)")

    # intervalos de carga, coloreados por nivel de demanda. Los niveles que
    # traban la red van con triangulo, para no depender solo del color
    for n in niveles:
        pts = [i for i in intervalos if i["solicitados"] == n and es_carga(i, ventana)]
        ax1.scatter([p["K_veh_km_carril"] for p in pts], [p["Q_veh_h_carril"] for p in pts],
                    s=46 if trabo[n] else 40, marker="^" if trabo[n] else "o",
                    color=tono[n], edgecolors=FONDO, linewidths=1.2, zorder=3,
                    label=f"{n} ({generados[n]})" + (", trabada" if trabo[n] else ""))

    if critica:
        ax1.plot(critica["curva_K"], critica["curva_Q"], color=TINTA_2, linewidth=2,
                 solid_capstyle="round", zorder=4, label="medianas de grupos de 8 intervalos de carga (referencia visual)")

    if critica and critica["saturacion_alcanzada"]:
        ax1.axvline(critica["k_c"], color=APAGADO, linewidth=1, zorder=2)
        # a la izquierda de la linea: arriba de la rama libre no hay puntos,
        # a la derecha los escenarios trabados alcanzan los flujos mas altos
        ax1.annotate(f"densidad crítica\nK = {critica['k_c']:.2f}",
                     (critica["k_c"], 0.97), xycoords=ax1.get_xaxis_transform(),
                     xytext=(-6, 0), textcoords="offset points", ha="right", va="top",
                     fontsize=9.5, color=TINTA_2)

    ax1.set_xlabel("densidad K (veh/km/carril)", fontsize=10, color=TINTA_2)
    ax1.set_ylabel("flujo Q (veh/h/carril)", fontsize=10, color=TINTA_2)
    ax1.set_xlim(left=0)
    ax1.set_ylim(bottom=0)
    ax1.set_title(f"Diagrama fundamental de la red ({red})", fontsize=12.5,
                  color=TINTA, pad=14, loc="left")

    # panel 2: densidad maxima alcanzada por nivel de demanda
    orden = sorted(resumenes, key=lambda r: r["solicitados"])
    x = [r["solicitados"] for r in orden]
    y = [r["K_max"] for r in orden]
    ax2.plot(x, y, color=AZUL, linewidth=2, solid_capstyle="round", zorder=3)
    ax2.scatter(x, y, s=40, color=AZUL, edgecolors=FONDO, linewidths=1.2, zorder=4)

    trabadas = [r for r in orden if r["trabada"]]
    if trabadas:
        ax2.scatter([r["solicitados"] for r in trabadas], [r["K_max"] for r in trabadas],
                    s=70, marker="X", color=TINTA, edgecolors=FONDO, linewidths=1.2,
                    zorder=5, label="red trabada")
    if critica and critica["saturacion_alcanzada"]:
        ax2.axhline(critica["k_c"], color=APAGADO, linewidth=1, zorder=2)
        ax2.annotate("densidad crítica", (x[0], critica["k_c"]), xytext=(0, 6),
                     textcoords="offset points", fontsize=9.5, color=TINTA_2)

    ax2.set_xlabel("vehículos solicitados", fontsize=10, color=TINTA_2)
    ax2.set_ylabel("K máxima del escenario (veh/km/carril)", fontsize=10, color=TINTA_2)
    ax2.set_ylim(bottom=0)
    ax2.set_title("Densidad máxima por nivel de demanda", fontsize=12.5,
                  color=TINTA, pad=14, loc="left")
    if trabadas:
        ax2.legend(frameon=False, fontsize=9.5, labelcolor=TINTA_2, loc="upper left")

    handles, labels = ax1.get_legend_handles_labels()
    fig.tight_layout()
    # despues de tight_layout y colgada de abajo de la figura, para que no
    # se encime con la etiqueta del eje x
    fig.legend(handles, labels, loc="upper center", ncol=min(len(labels), 5), frameon=False,
               fontsize=9.5, labelcolor=TINTA_2, bbox_to_anchor=(0.5, 0.0),
               title="vehículos solicitados (generados)", title_fontsize=9.5)

    fig.savefig(destino, dpi=200, facecolor=FONDO, bbox_inches="tight")
    plt.close(fig)


def escribir_csv(path, filas):
    if not filas:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)


def valor(texto):
    """convierte una celda del CSV de vuelta a su tipo original"""
    if texto in ("True", "False"):
        return texto == "True"
    if texto == "":
        return None
    for tipo in (int, float):
        try:
            return tipo(texto)
        except ValueError:
            pass
    return texto


def leer_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return [{k: valor(v) for k, v in fila.items()} for fila in csv.DictReader(f)]


def simular(args):
    """genera la demanda de cada nivel y corre las simulaciones en paralelo"""
    # la demanda se genera antes y en serie: randomTrips escribe archivos y
    # no conviene que varios procesos lo llamen a la vez
    trabajos = []
    for k, n in enumerate(sorted(set(args.cars))):
        rutas, info = demand.generate(n, seed=args.demand_seed)
        trabajos.append((n, info["generados"], rutas, args.net, args.period,
                         args.max_steps, args.max_quiet, PUERTO_BASE + k))
        print(f"demanda: {info['generados']} vehiculos de {n} solicitados -> {rutas}")

    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        resultados = list(pool.map(medir, trabajos))

    return [i for filas, _ in resultados for i in filas], [r for _, r in resultados]


if __name__ == "__main__":
    args = parse_args()
    os.makedirs(args.out, exist_ok=True)

    red = os.path.basename(args.net).replace(".net.xml", "")
    tag = f"{red}_s{args.demand_seed}"
    base = os.path.join(args.out, tag)

    if args.solo_analisis:
        intervalos = leer_csv(f"{base}.intervalos.csv")
        resumenes = leer_csv(f"{base}.resumen.csv")
    else:
        intervalos, resumenes = simular(args)
        escribir_csv(f"{base}.intervalos.csv", intervalos)
        escribir_csv(f"{base}.resumen.csv", sorted(resumenes, key=lambda r: r["solicitados"]))

    critica = densidad_critica(intervalos, VENTANA)
    q_capacidad = critica["q_capacidad"] if critica else None
    recomendacion = recomendar(resumenes, critica)

    with open(f"{base}.meta.json", "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "origen": "csv (--solo-analisis)" if args.solo_analisis else "simulacion",
            "red": args.net,
            "demanda": {"generador": "demand.generate", "seed": args.demand_seed,
                        "ventana_s": VENTANA,
                        "solicitados": sorted(r["solicitados"] for r in resumenes)},
            "medicion": {"fuente": "TraCI (suscripciones por arista)",
                         "periodo_s": args.period,
                         "definiciones": "Edie: K = veh-h / (T x km carril), "
                                         "Q = veh-km / (T x km carril)",
                         "aristas_internas": "excluidas",
                         "carriles": "solo los que admiten 'passenger'"},
            "simulacion": {"flags": Controller().sim_flags(),
                           "max_steps": args.max_steps, "max_quiet": args.max_quiet},
            "densidad_critica": critica,
            "flujo_en_capacidad_veh_h_carril": q_capacidad,
            "recomendacion": recomendacion,
        }, f, ensure_ascii=False, indent=2)

    # la red base se nombra por lo que es y no por su archivo (test.net.xml)
    es_base = os.path.normpath(args.net) == os.path.normpath(Controller().NETWORK)
    graficar(intervalos, resumenes, critica, f"{base}.qk.png",
             "configuración de netconvert" if es_base else red, VENTANA)

    print(f"\n{'solicitados':>11} {'generados':>9} {'K_max':>7} {'Q_max':>8} "
          f"{'cola_max':>8} {'trabada':>7} {'duracion_s':>10}")
    for r in sorted(resumenes, key=lambda r: r["solicitados"]):
        print(f"{r['solicitados']:>11} {r['generados']:>9} {r['K_max']:>7.2f} {r['Q_max']:>8.1f} "
              f"{r['cola_insercion_max']:>8} {str(r['trabada']):>7} {r['duracion_s']:>10}")

    if critica:
        estado = "alcanzada" if critica["saturacion_alcanzada"] else \
                 "NO alcanzada: el flujo seguia subiendo, pruebe demandas mayores"
        print(f"\ndensidad critica K = {critica['k_c']} veh/km/carril ({estado})")
        print(f"flujo de capacidad (meseta de la rama de carga) = {q_capacidad} veh/h/carril")
    print(f"capacidad (mayor demanda sin pasar la densidad critica): "
          f"{recomendacion['capacidad_solicitados']}")
    print(f"limite (mayor demanda que la red todavia despeja): "
          f"{recomendacion['limite_solicitados']}")
    print(f"resultados en {args.out}/")
