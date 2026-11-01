"""
aceleracion de la evaluacion en paralelo: el mismo lote de simulaciones con
distinta cantidad de procesos simultaneos, medido en tiempo de reloj.

Cada simulacion es la configuracion de netconvert con la demanda de la corrida,
bajo las mismas banderas que usa el GA, asi que el lote es representativo de
una generacion.

Una misma cantidad de procesos puede repetirse en --workers (p. ej. 1 al inicio
y al final, para detectar una medicion secuencial anomala): se guardan todas
las repeticiones, en el orden en que se midieron, y la aceleracion se calcula
contra la media de las mediciones secuenciales.

Escribe robustez/aceleracion_lote{lote}.json e imprime un resumen.

Uso:
    python aceleracion.py g150p30m12touuniP2c2600s42 --lote 6 --workers 1 6 3 1
"""

import argparse
import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

from controller import Controller


def parse_args():
    parser = argparse.ArgumentParser(description="Aceleracion de la evaluacion en paralelo")
    parser.add_argument("run", help="nombre de la corrida")
    parser.add_argument("--lote", type=int, default=12, help="simulaciones por medicion")
    parser.add_argument("--workers", type=int, nargs="+", default=[1, 2, 4, 6, 8])
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    meta = json.load(open(f"{args.run}.meta.json", encoding="utf-8"))
    esc = meta["escenario"]
    ctrl = Controller(network=esc["network"], routes=esc["routes"])

    def una(i):
        sid = f"acel_{i}"
        cmd = [ctrl.SUMO_BINARY, "-n", esc["network"], "-r", esc["routes"],
               "--tripinfo-output", f"outputs/{sid}.xml",
               "--statistic-output", f"outputs/{sid}.stats.xml",
               "--end", str(ctrl.MAX_STEPS)] + ctrl.sim_flags()
        subprocess.run(cmd, check=True, capture_output=True, text=True)

    # lista y no diccionario: una cantidad de procesos repetida no debe
    # sobrescribir la medicion anterior
    mediciones = []
    for w in args.workers:
        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=w) as pool:
            list(pool.map(una, range(args.lote)))
        mediciones.append({"procesos": w, "tiempo_s": round(time.perf_counter() - t0, 1)})
        print(f"{w} procesos: {mediciones[-1]['tiempo_s']:.1f} s", flush=True)

    por_procesos = {}
    for m in mediciones:
        por_procesos.setdefault(m["procesos"], []).append(m["tiempo_s"])
    minimo = min(por_procesos)
    base = sum(por_procesos[minimo]) / len(por_procesos[minimo])
    salida = {"run": args.run, "lote": args.lote, "nucleos_logicos": os.cpu_count(),
              "mediciones": mediciones,
              "aceleracion_contra_media_secuencial": {
                  str(w): round(base / (sum(t) / len(t)), 2) for w, t in sorted(por_procesos.items())}}
    os.makedirs("robustez", exist_ok=True)
    with open(f"robustez/aceleracion_lote{args.lote}.json", "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)
    print(json.dumps(salida, ensure_ascii=False, indent=2))
