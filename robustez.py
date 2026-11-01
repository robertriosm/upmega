"""
robustez de la mejor solucion de una corrida frente a la realizacion del
escenario.

El GA optimiza sobre una sola demanda (semilla de randomTrips) y una sola
semilla de SUMO, asi que su mejor solucion puede estar ajustada a esa
realizacion. Aqui se vuelven a simular tres planes con otras semillas:
- netconvert: la red original
- algoritmo: la mejor solucion de la corrida
- uniforme: un mismo ciclo en todas las intersecciones (el mejor del barrido
  de analisis_corrida.py), con los repartos originales

Cada combinacion (semilla de demanda, semilla de SUMO) se simula con los tres
planes bajo las mismas banderas que usa el GA, y se reporta media y
dispersion de J por plan, ademas de las diferencias pareadas.

Escribe robustez/{run}.json e imprime un resumen.

Uso:
    python robustez.py g150p30m12touuniP2c2600s42
    python robustez.py g150p30m12touuniP2c2600s42 --demanda 42 1 2 3 4 --sumo 23 1 2 3 4 5 6
"""

import argparse
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import cloudpickle

import demand
from controller import Controller
from analisis_corrida import J, Laboratorio


def parse_args():
    parser = argparse.ArgumentParser(description="Robustez de la mejor solucion frente a otras semillas")
    parser.add_argument("run", help="nombre de la corrida, p. ej. g150p30m12touuniP2c2600s42")
    parser.add_argument("--demanda", type=int, nargs="+", default=[42, 1, 2, 3, 4],
                        help="semillas de randomTrips (default 42 1 2 3 4)")
    parser.add_argument("--sumo", type=int, nargs="+", default=[23, 1, 2, 3, 4, 5, 6],
                        help="semillas de SUMO (default 23 1 2 3 4 5 6)")
    parser.add_argument("--workers", type=int, default=6, help="simulaciones en paralelo")
    parser.add_argument("--port", type=int, default=8815, help="puerto TraCI (default 8815)")
    return parser.parse_args()


def simular(ctrl, red, rutas, semilla, sid):
    """una simulacion con las banderas del GA pero otra semilla de SUMO"""
    flags = ctrl.sim_flags()
    flags[flags.index("--seed") + 1] = str(semilla)
    cmd = [ctrl.SUMO_BINARY, "-n", red, "-r", rutas,
           "--tripinfo-output", f"outputs/{sid}.xml",
           "--statistic-output", f"outputs/{sid}.stats.xml",
           "--end", str(ctrl.MAX_STEPS)] + flags
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    d, w, stats = ctrl.read_results(sid)
    return {"J": round(J(d, w), 2), "vehiculos": len(d), "sin_terminar": stats.get("sin_terminar", 0),
            "tiempo_perdido_medio": stats.get("timeLoss")}


def resumen(valores):
    v = np.array(valores, dtype=float)
    return {"media": round(float(v.mean()), 1), "desviacion": round(float(v.std(ddof=1)), 1),
            "min": round(float(v.min()), 1), "max": round(float(v.max()), 1)}


if __name__ == "__main__":
    args = parse_args()
    run = args.run
    meta = json.load(open(f"{run}.meta.json", encoding="utf-8"))
    escenario = meta["escenario"]
    analisis = json.load(open(f"{run}.analisis.json", encoding="utf-8"))
    ciclo_uniforme = analisis["referencia_uniforme"]["ciclo_optimo_s"]

    solicitados = escenario["demanda"]["solicitados"]
    rutas = {}
    for s in args.demanda:
        archivo, info = demand.generate(solicitados, net=escenario["network"], seed=s)
        rutas[s] = (archivo, info["generados"])
        print(f"demanda semilla {s}: {info['generados']} vehiculos")

    with open(f"{run}.pkl", "rb") as f:
        ga = cloudpickle.load(f)
    mejor = list(ga.population[int(np.argmax(ga.last_generation_fitness))])

    lab = Laboratorio(escenario["routes"], args.port, args.workers)
    try:
        lab.ctrl.apply_solution(mejor, f"rb_{run}_algoritmo", lab.tls, lab.slices)
        lab.ctrl.apply_solution(lab.uniforme(ciclo_uniforme), f"rb_{run}_uniforme", lab.tls, lab.slices)
    finally:
        lab.cerrar()

    ctrl = lab.ctrl
    redes = {"netconvert": escenario["network"],
             "algoritmo": f"logics/rb_{run}_algoritmo.net.xml",
             "uniforme": f"logics/rb_{run}_uniforme.net.xml"}

    tareas = [(plan, ds, ss) for ds in args.demanda for ss in args.sumo for plan in redes]

    def una(t):
        plan, ds, ss = t
        sid = f"rb_{run}_{plan}_d{ds}_s{ss}"
        r = simular(ctrl, redes[plan], rutas[ds][0], ss, sid)
        print(f"{plan:10s} demanda {ds:3d} sumo {ss:3d}  J={r['J']:8.2f}  sin terminar={r['sin_terminar']}",
              flush=True)
        return {"plan": plan, "semilla_demanda": ds, "semilla_sumo": ss, **r}

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        filas = list(pool.map(una, tareas))

    tabla = {(f["plan"], f["semilla_demanda"], f["semilla_sumo"]): f for f in filas}
    casos = [(ds, ss) for ds in args.demanda for ss in args.sumo]

    def serie(plan):
        return [tabla[(plan, ds, ss)]["J"] for ds, ss in casos]

    ga_, nc, un = np.array(serie("algoritmo")), np.array(serie("netconvert")), np.array(serie("uniforme"))
    salida = {
        "run": run,
        "ciclo_uniforme_s": ciclo_uniforme,
        "semillas_demanda": args.demanda,
        "semillas_sumo": args.sumo,
        "vehiculos_por_demanda": {str(s): rutas[s][1] for s in args.demanda},
        "simulaciones": len(filas),
        "J_por_plan": {p: resumen(serie(p)) for p in redes},
        "J_por_plan_y_demanda": {p: {str(ds): resumen([tabla[(p, ds, ss)]["J"] for ss in args.sumo])
                                     for ds in args.demanda} for p in redes},
        "casos_con_vehiculos_sin_terminar": {p: sum(1 for ds, ss in casos
                                                    if tabla[(p, ds, ss)]["sin_terminar"] > 0) for p in redes},
        "mejora_algoritmo_vs_netconvert_pct": resumen(100 * (nc - ga_) / nc),
        "mejora_algoritmo_vs_uniforme_pct": resumen(100 * (un - ga_) / un),
        "casos_algoritmo_mejor_que_netconvert": int((ga_ < nc).sum()),
        "casos_algoritmo_mejor_que_uniforme": int((ga_ < un).sum()),
        "casos": len(casos),
        "filas": filas,
    }

    os.makedirs("robustez", exist_ok=True)
    with open(f"robustez/{run}.json", "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in salida.items() if k != "filas"}, ensure_ascii=False, indent=2))
