"""
cifras que muestra el video, leidas de los archivos de la corrida y no
copiadas a mano, para que el video diga lo mismo que la tesis.

Todo sale de la carpeta upmega: meta.json, analisis.json, evaluations.csv,
detail/ (tripinfo), logics/ (red de la mejor solucion), robustez/ y la
funcion de reparto del controlador.
"""

import csv
import json
import sys
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RUN = "g150p30m12touuniP2c2600s42"

sys.path.insert(0, str(RAIZ))
from controller import Controller  # noqa: E402


def _json(nombre):
    return json.loads((RAIZ / nombre).read_text(encoding="utf-8"))


@lru_cache(None)
def meta():
    return _json(f"{RUN}.meta.json")


@lru_cache(None)
def analisis():
    return _json(f"{RUN}.analisis.json")


@lru_cache(None)
def robustez():
    return _json(f"robustez/{RUN}.json")


@lru_cache(None)
def evaluaciones():
    with open(RAIZ / f"{RUN}.evaluations.csv", encoding="utf-8") as f:
        return [{"gen": int(r["generation"]), "J": 1 / float(r["fitness"]),
                 "trabada": r["trabada"] == "True"} for r in csv.DictReader(f)]


def curva_mejor():
    """J del mejor individuo encontrado hasta cada generacion"""
    mejor_por_gen = {}
    for e in evaluaciones():
        mejor_por_gen[e["gen"]] = min(mejor_por_gen.get(e["gen"], float("inf")), e["J"])
    curva, actual = [], float("inf")
    for g in sorted(mejor_por_gen):
        actual = min(actual, mejor_por_gen[g])
        curva.append((g, actual))
    return curva


def trabadas_por_bloque():
    """evaluaciones que traban la red: generacion 0 y bloques de 50 generaciones"""
    bloques = [(0, 0), (1, 50), (51, 100), (101, 150)]
    salida = []
    for a, b in bloques:
        es = [e for e in evaluaciones() if a <= e["gen"] <= b]
        salida.append({"desde": a, "hasta": b, "trabadas": sum(e["trabada"] for e in es), "total": len(es)})
    return salida


def robustez_resumen():
    """mediana de J y combinaciones trabadas por plan, y mediana de las reducciones por combinacion"""
    import statistics
    filas = robustez()["filas"]
    planes = ("netconvert", "algoritmo", "uniforme")
    J = {p: {(f["semilla_demanda"], f["semilla_sumo"]): f["J"] for f in filas if f["plan"] == p} for p in planes}
    casos = sorted(J["netconvert"])
    return {
        "casos": len(casos),
        "mediana_J": {p: round(statistics.median(J[p].values()), 1) for p in planes},
        "trabadas": robustez()["casos_con_vehiculos_sin_terminar"],
        "reduccion_vs_netconvert": round(statistics.median(
            100 * (J["netconvert"][c] - J["algoritmo"][c]) / J["netconvert"][c] for c in casos), 1),
        "mejor_que_netconvert": robustez()["casos_algoritmo_mejor_que_netconvert"],
    }


def tripinfo_ejemplo(indice=0):
    """registro tripinfo de un vehiculo en la simulacion de la mejor solucion"""
    ruta = RAIZ / meta()["archivos"]["detalle_mejor"]["tripinfo"]
    for i, t in enumerate(ET.parse(ruta).getroot().iter("tripinfo")):
        if i == indice:
            return {k: t.get(k) for k in ("id", "depart", "arrival", "duration", "routeLength",
                                          "waitingTime", "timeLoss")}


def clip_sumo(plan):
    """contadores y J de la grabacion de SUMO-GUI hecha con grabar_sumo.py"""
    ruta = Path(__file__).resolve().parent / "salida" / f"sumo_{plan}.json"
    if not ruta.exists():
        raise FileNotFoundError(f"falta {ruta}: corre primero grabar_sumo.py")
    return json.loads(ruta.read_text(encoding="utf-8"))


def medias_tripinfo(plan):
    """viaje medio, espera media y J del tripinfo de la grabacion, con la regla del controlador"""
    ruta = Path(__file__).resolve().parent / "salida" / f"sumo_{plan}.tripinfo.xml"
    tope = 10000
    d, w = [], []
    for t in ET.parse(ruta).getroot().iter("tripinfo"):
        llego = float(t.get("arrival", 0)) >= 0
        d.append(float(t.get("duration")) if llego else tope)
        w.append(float(t.get("waitingTime")) if llego else tope)
    f = meta()["fitness"]
    viaje, espera = sum(d) / len(d), sum(w) / len(w)
    return {"viaje": viaje, "espera": espera, "J": f["w1"] * viaje + f["w2"] * espera, "vehiculos": len(d)}


def tllogic(tl_id, red):
    for t in ET.parse(RAIZ / red).getroot().iter("tlLogic"):
        if t.get("id") == tl_id:
            return {"offset": int(float(t.get("offset", 0))),
                    "fases": [(int(float(p.get("duration"))), p.get("state")) for p in t.iter("phase")]}


def tllogic_antes_despues(tl_id="1903163106"):
    return (tllogic(tl_id, meta()["escenario"]["network"]),
            tllogic(tl_id, meta()["resultado"]["red_de_la_mejor"]))


def reparto(ciclo, ambar, minimos, pesos):
    """el mismo reparto que hace el controlador al decodificar un genoma"""
    return Controller.reparto(None, ciclo, ambar, minimos, pesos)


def desfase_segundos(ciclo, pct):
    """el mismo redondeo que aplica el controlador al desfase"""
    return int(round(ciclo * float(pct) / 100)) % ciclo


if __name__ == "__main__":
    m, a = meta(), analisis()
    print("ga:", {k: m["ga"][k] for k in ("num_generations", "sol_per_pop", "num_parents_mating",
                                          "K_tournament", "mutation_probability", "keep_elitism", "num_genes")})
    print("J:", a["J"], "curva:", curva_mejor()[0], curva_mejor()[50], curva_mejor()[-1])
    print("trabadas:", trabadas_por_bloque())
    print("tripinfo:", tripinfo_ejemplo())
    print("tllogic:", tllogic_antes_despues())
    print("reparto 45:", reparto(45, 12, [7, 7], [30, 12]), "desfase:", desfase_segundos(45, 25))
    print("robustez:", robustez()["J_por_plan"], robustez()["mejora_algoritmo_vs_netconvert_pct"])
