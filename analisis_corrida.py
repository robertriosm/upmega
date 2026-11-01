"""
cifras del capitulo de resultados para una corrida del GA, calculadas desde sus
archivos y no copiadas a mano.

Lee lo que deja una corrida (pkl, meta.json, evaluations.csv y detail/) y corre
las simulaciones extra que piden dos de los analisis:
- desfases anulados: la mejor solucion con todos los offsets en cero
- referencia uniforme: un mismo ciclo en todas las intersecciones, con los
  repartos originales, barriendo el valor del ciclo

Escribe {run}.analisis.json e imprime un resumen.

Uso:
    python analisis_corrida.py g150p30m12touuniP2c2600s42
    python analisis_corrida.py g150p30m12touuniP2c1000s42 --workers 2
"""

import argparse
import json
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import cloudpickle

from controller import Controller


W1, W2 = 1.0, 1.1


def parse_args():
    parser = argparse.ArgumentParser(description="Cifras de resultados de una corrida del GA")
    parser.add_argument("run", help="nombre de la corrida, p. ej. g150p30m12touuniP2c2600s42")
    parser.add_argument("--workers", type=int, default=6, help="simulaciones en paralelo")
    parser.add_argument("--port", type=int, default=8814,
                        help="puerto TraCI (default 8814, distinto del 8813 de main.py)")
    parser.add_argument("--ciclos", type=int, nargs=3, default=[20, 120, 5],
                        metavar=("DESDE", "HASTA", "PASO"),
                        help="barrido grueso del ciclo uniforme (default 20 120 5); "
                             "despues se refina de 1 en 1 alrededor del mejor")
    return parser.parse_args()


def J(durations, waiting):
    return W1 * float(np.mean(durations)) + W2 * float(np.mean(waiting))


def tripinfo(path):
    """duracion, espera y tiempo perdido de cada vehiculo, mas cuantos no llegaron"""
    root = ET.parse(path).getroot()
    d, w, tl, sin = [], [], [], 0
    for t in root.findall("tripinfo"):
        if float(t.get("arrival", 0)) < 0:
            sin += 1
        d.append(float(t.get("duration")))
        w.append(float(t.get("waitingTime")))
        tl.append(float(t.get("timeLoss")))
    return np.array(d), np.array(w), np.array(tl), sin


def distribucion(v):
    return {"media": round(float(v.mean()), 2), "min": float(v.min()),
            "p25": float(np.percentile(v, 25)), "p50": float(np.percentile(v, 50)),
            "p75": float(np.percentile(v, 75)), "p90": round(float(np.percentile(v, 90)), 1),
            "max": float(v.max())}


def cambio(antes, despues):
    return round(100 * (despues - antes) / antes, 2)


def stats_xml(path):
    root = ET.parse(path).getroot()
    v = root.find("vehicleTripStatistics")
    return {"speed": float(v.get("speed")), "timeLoss": float(v.get("timeLoss"))}


def aristas(path):
    """tiempo perdido total de cada arista en toda la simulacion"""
    out = {}
    for e in ET.parse(path).getroot().iter("edge"):
        if e.get("timeLoss") is not None:
            out[e.get("id")] = out.get(e.get("id"), 0.0) + float(e.get("timeLoss"))
    return out


def via(arista):
    """
    via de OpenStreetMap a la que pertenece una arista. La red no trae nombres
    de calle, pero netconvert arma el id como [-]<id de la via>#<tramo>: el
    signo indica el sentido, asi que sin el se juntan los dos sentidos de una
    misma calle en un corredor
    """
    return arista.split("#")[0].lstrip("-")


def analisis_espacial(run):
    base = aristas(f"detail/{run}.baseline.edgedata.xml")
    mejor = aristas(f"detail/{run}.best.edgedata.xml")
    ids = sorted(set(base) | set(mejor))
    ahorro = {e: base.get(e, 0.0) - mejor.get(e, 0.0) for e in ids}
    total_base, total_mejor = sum(base.values()), sum(mejor.values())
    neto = total_base - total_mejor
    # ahorro bruto: lo que suman las aristas que mejoran, sin descontar las que empeoran
    positivos = sorted((v for v in ahorro.values() if v > 0), reverse=True)
    bruto = sum(positivos)

    # cuantas aristas, de la que mas ahorra hacia abajo, hacen falta para la mitad del ahorro bruto
    acumulado, n_mitad = 0.0, 0
    for valor in positivos:
        acumulado += valor
        n_mitad += 1
        if acumulado >= bruto / 2:
            break

    por_via = {}
    for e in ids:
        b, m = por_via.get(via(e), (0.0, 0.0))
        por_via[via(e)] = (b + base.get(e, 0.0), m + mejor.get(e, 0.0))
    vias = sorted(por_via.items(), key=lambda kv: kv[1][0] - kv[1][1], reverse=True)
    top5 = sum(b - m for _, (b, m) in vias[:5])
    vias_bruto = sum(b - m for _, (b, m) in vias if b > m)

    return {
        "aristas": len(ids),
        "tiempo_perdido_total_base": round(total_base, 1),
        "tiempo_perdido_total_mejor": round(total_mejor, 1),
        "cambio_pct": cambio(total_base, total_mejor),
        "aristas_mejoran": sum(1 for v in ahorro.values() if v > 0),
        "aristas_empeoran": sum(1 for v in ahorro.values() if v < 0),
        "ahorro_neto": round(neto, 1),
        "ahorro_bruto": round(bruto, 1),
        "aristas_para_mitad_del_ahorro_bruto": n_mitad,
        "vias": len(vias),
        "vias_que_mejoran": sum(1 for _, (b, m) in vias if b > m),
        "top5_vias_pct_del_ahorro_neto": round(100 * top5 / neto, 1) if neto else None,
        "top5_vias_pct_del_ahorro_bruto_por_via": round(100 * top5 / vias_bruto, 1) if vias_bruto else None,
        "top5_vias": [{"via": v, "base": round(b, 1), "mejor": round(m, 1)} for v, (b, m) in vias[:5]],
        "vias_que_empeoran": sum(1 for _, (b, m) in vias if m > b),
        "peores_vias": [{"via": v, "base": round(b, 1), "mejor": round(m, 1)}
                        for v, (b, m) in sorted(vias, key=lambda kv: kv[1][0] - kv[1][1])[:5]
                        if m > b],
    }


def convergencia(ga):
    Js = [1 / f for f in ga.best_solutions_fitness]
    pob = [1 / f for f in ga.last_generation_fitness]
    puntos = {g: round(Js[g], 1) for g in (0, 50, 100, len(Js) - 1) if g < len(Js)}
    return {
        "J_por_generacion": puntos,
        "mejora_0_50": round(Js[0] - Js[min(50, len(Js) - 1)], 1),
        "mejora_ultimas_50": round(Js[max(0, len(Js) - 51)] - Js[-1], 1),
        "media_poblacion_final_J": round(float(np.mean(pob)), 1),
        # la media se infla con pocos individuos que traban la red; la mediana no
        "mediana_poblacion_final_J": round(float(np.median(pob)), 1),
        "mejor_J": round(min(Js), 1),
        "generacion_del_mejor": int(np.argmin(Js)),
    }


def concordancia(run):
    """
    fraccion de pares de evaluaciones que J y el tiempo perdido ordenan igual,
    y que parte de los pares discordantes esta separada por menos de 1 s de J
    """
    import csv
    filas = [r for r in csv.DictReader(open(f"{run}.evaluations.csv", encoding="utf-8"))
             if r["time_loss"] not in ("", "None")]
    j = np.array([1 / float(r["fitness"]) for r in filas])
    tl = np.array([float(r["time_loss"]) for r in filas])
    conc = disc = disc_cerca = 0
    for i in range(len(j) - 1):
        dj, dt = j[i + 1:] - j[i], tl[i + 1:] - tl[i]
        validos = (dj != 0) & (dt != 0)
        mismo = np.sign(dj[validos]) == np.sign(dt[validos])
        conc += int(mismo.sum())
        disc += int((~mismo).sum())
        disc_cerca += int(((~mismo) & (np.abs(dj[validos]) < 1)).sum())
    return {"evaluaciones": len(j),
            "pares_concordantes_pct": round(100 * conc / (conc + disc), 2),
            "discordantes_con_dJ_menor_1s_pct": round(100 * disc_cerca / disc, 1) if disc else None}


class Laboratorio:
    """aplica genomas a la red y los simula igual que lo hace el GA"""

    def __init__(self, rutas, port, workers):
        self.ctrl = Controller(routes=rutas, port=port)
        self.ctrl.start_sumo_conn()
        self.base, split_counts = self.ctrl.build_genome()
        self.slices = np.cumsum([0] + split_counts)
        self.tls = self.ctrl.get_tl_ids()
        self.workers = workers

    def simular(self, genomas):
        """genomas: dict sid -> genoma. Devuelve sid -> (J, sin_terminar)"""
        def uno(par):
            sid, g = par
            self.ctrl.apply_solution(g, sid, self.tls, self.slices)
            d, w, stats = self.ctrl.run_simulation(sid)
            return sid, (round(J(d, w), 2), stats.get("sin_terminar", 0))
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            return dict(pool.map(uno, genomas.items()))

    def uniforme(self, ciclo):
        n = len(self.tls)
        g = list(self.base)
        g[:n] = [ciclo] * n
        return g

    def cerrar(self):
        self.ctrl.close_sumo_conn()


if __name__ == "__main__":
    args = parse_args()
    run = args.run
    meta = json.load(open(f"{run}.meta.json", encoding="utf-8"))
    rutas = meta["escenario"]["routes"]

    db, wb, tlb, sb = tripinfo(f"detail/{run}.baseline.tripinfo.xml")
    dm, wm, tlm, sm = tripinfo(f"detail/{run}.best.tripinfo.xml")
    stb = stats_xml(f"detail/{run}.baseline.stats.xml")
    stm = stats_xml(f"detail/{run}.best.stats.xml")

    resultado = {
        "run": run,
        "vehiculos": len(db),
        "sin_terminar": {"base": sb, "mejor": sm},
        "espera": {"base": distribucion(wb), "mejor": distribucion(wm),
                   "cambio_media_pct": cambio(wb.mean(), wm.mean())},
        "viaje": {"base": distribucion(db), "mejor": distribucion(dm),
                  "cambio_media_pct": cambio(db.mean(), dm.mean())},
        "tiempo_perdido_media": {"base": round(float(tlb.mean()), 2), "mejor": round(float(tlm.mean()), 2),
                                 "cambio_pct": cambio(tlb.mean(), tlm.mean())},
        "velocidad_media_m_s": {"base": stb["speed"], "mejor": stm["speed"],
                                "cambio_pct": cambio(stb["speed"], stm["speed"])},
        "horas_vehiculo": {"viaje_base": round(db.sum() / 3600, 1), "viaje_mejor": round(dm.sum() / 3600, 1),
                           "espera_base": round(wb.sum() / 3600, 1), "espera_mejor": round(wm.sum() / 3600, 1)},
        "descomposicion": {"movimiento_base": round(float((db - wb).mean()), 2),
                           "movimiento_mejor": round(float((dm - wm).mean()), 2),
                           "detenido_base": round(float(wb.mean()), 2),
                           "detenido_mejor": round(float(wm.mean()), 2)},
        "J": {"base": round(J(db, wb), 2), "mejor": round(J(dm, wm), 2)},
        "evaluaciones": meta["resultado"]["evaluaciones"],
        "generacion_del_mejor": meta["resultado"]["mejor_generacion"],
    }

    with open(f"{run}.pkl", "rb") as f:
        ga = cloudpickle.load(f)
    resultado["convergencia"] = convergencia(ga)
    resultado["espacial"] = analisis_espacial(run)
    resultado["concordancia_J_tiempo_perdido"] = concordancia(run)

    # la mejor solucion esta en la poblacion final gracias al elitismo
    mejor = list(ga.population[int(np.argmax(ga.last_generation_fitness))])

    lab = Laboratorio(rutas, args.port, args.workers)
    try:
        sin_desfase = list(mejor)
        n = len(lab.tls)
        sin_desfase[-n:] = [0] * n
        r = lab.simular({f"an_{run}_mejor": mejor, f"an_{run}_sin_desfase": sin_desfase})
        J_mejor, J_sin = r[f"an_{run}_mejor"][0], r[f"an_{run}_sin_desfase"][0]
        resultado["desfases_anulados"] = {
            "J_mejor_resimulado": J_mejor, "J_sin_desfases": J_sin,
            "deterioro_pct": cambio(J_mejor, J_sin),
            "sin_terminar": r[f"an_{run}_sin_desfase"][1]}

        desde, hasta, paso = args.ciclos
        grueso = lab.simular({f"an_{run}_u{c}": lab.uniforme(c) for c in range(desde, hasta + 1, paso)})
        c0 = min(range(desde, hasta + 1, paso), key=lambda c: grueso[f"an_{run}_u{c}"][0])
        finos = [c for c in range(max(desde, c0 - paso + 1), min(hasta, c0 + paso - 1) + 1)
                 if (c - desde) % paso != 0]
        fino = lab.simular({f"an_{run}_u{c}": lab.uniforme(c) for c in finos})
        todos = {**grueso, **fino}
        barrido = {int(re.search(r"_u(\d+)$", k).group(1)): v for k, v in todos.items()}
        c_opt = min(barrido, key=lambda c: barrido[c][0])
        resultado["referencia_uniforme"] = {
            "ciclo_optimo_s": c_opt, "J_optimo": barrido[c_opt][0],
            "diferencia_vs_GA_pct": cambio(barrido[c_opt][0], J_mejor),
            "barrido": {str(c): barrido[c][0] for c in sorted(barrido)}}
    finally:
        lab.cerrar()

    with open(f"{run}.analisis.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
