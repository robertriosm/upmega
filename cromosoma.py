"""
recorre paso a paso como se arma, se guarda y se decodifica el cromosoma de
una corrida del GA, con los tipos de dato reales que maneja cada pieza.

Arma el genoma base con el mismo Controller de la corrida (levanta SUMO un
momento para leer los semaforos), carga el pkl para ver la poblacion de PyGAD
y decodifica el mejor individuo de algunos semaforos, comparandolo con la red
que la corrida guardo.

Escribe {run}.cromosoma.txt con los cromosomas completos (netconvert y el
mejor), el orden de los semaforos y los pesos por semaforo.

Uso:
    python cromosoma.py g150p30m12touuniP2c2600s42
    python cromosoma.py g150p30m12touuniP2c2600s42 --semaforos 1903163106 1438391835
"""

import argparse
import json
import xml.etree.ElementTree as ET

import cloudpickle
import numpy as np

from controller import Controller


def parse_args():
    parser = argparse.ArgumentParser(description="Estructura del cromosoma de una corrida del GA")
    parser.add_argument("run", help="nombre de la corrida, p. ej. g150p30m12touuniP2c2600s42")
    parser.add_argument("--semaforos", nargs="+", default=["1903163106", "1438391835"],
                        help="ids de los semaforos que se muestran en detalle")
    parser.add_argument("--port", type=int, default=8819,
                        help="puerto TraCI (default 8819, distinto del 8813 de main.py)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run, ejemplos = args.run, args.semaforos
    meta = json.load(open(f"{run}.meta.json", encoding="utf-8"))

    con = Controller(network=meta["escenario"]["network"], routes=meta["escenario"]["routes"],
                     port=args.port)
    con.start_sumo_conn()
    try:
        tls = con.get_tl_ids()
        base, split_counts = con.build_genome()
        logicas = {t: con.get_tl_logic(t) for t in ejemplos}
    finally:
        con.close_sumo_conn()

    slices = np.cumsum([0] + split_counts)
    N = len(tls)
    P = int(slices[-1])

    def posiciones(tl):
        """posicion del ciclo, de los pesos y del desfase de un semaforo"""
        i = tls.index(tl)
        return i, list(range(N + slices[i], N + slices[i + 1])), N + P + i

    print("PASO 1. Lista de semaforos que entrega TraCI")
    print("  tipo:", type(tls).__name__, "| largo:", len(tls), "| tipo de cada id:", type(tls[0]).__name__)
    print("  primeros 3:", tls[:3])
    print()

    print("PASO 2. Estructura de cada semaforo (split_layout)")
    for t in ejemplos:
        lg = logicas[t]
        indices, ambar, minimos = con.split_layout(lg)
        print(f"  {t}: fases {[(p.duration, p.state) for p in lg.phases]}")
        print(f"     fases variables (indices) = {indices}, ambar total = {ambar} s, minimos = {minimos}")
    print()

    print("PASO 3. Genoma base que arma build_genome (individuo de netconvert)")
    print("  tipo:", type(base).__name__, "| largo:", len(base), "| tipo de cada gen:", type(base[0]).__name__)
    print("  split_counts (pesos por semaforo): tipo", type(split_counts).__name__,
          "| valores distintos:", sorted(set(split_counts)), "| suma:", sum(split_counts))
    print("  gene_slices (np.cumsum):", repr(slices[:6]), "...", "ultimo =", slices[-1])
    print(f"  tramo 1, ciclos   base[0:{N}]      ->", base[:6], "...")
    print(f"  tramo 2, pesos    base[{N}:{N + P}]    ->", base[N:N + 6], "...")
    print(f"  tramo 3, desfases base[{N + P}:{N + P + N}]  ->", base[N + P:N + P + 6], "...")
    for t in ejemplos:
        i, ps, po = posiciones(t)
        print(f"  {t}: es el semaforo {i}; ciclo en la posicion {i} = {base[i]}, "
              f"pesos en {ps} = {[base[p] for p in ps]}, desfase en {po} = {base[po]}")
    print()

    with open(f"{run}.pkl", "rb") as f:
        ga = cloudpickle.load(f)

    print("PASO 4. Espacio genetico (gene_space), un rango por gen")
    print("  tipo:", type(ga.gene_space).__name__, "| largo:", len(ga.gene_space),
          "| tipo de cada elemento:", type(ga.gene_space[0]).__name__)
    for t in ejemplos:
        i, ps, po = posiciones(t)
        print(f"  {t}: ciclo {ga.gene_space[i]}, pesos {[ga.gene_space[p] for p in ps]}, "
              f"desfase {ga.gene_space[po]}")
    print()

    pi = ga.initial_population
    print("PASO 5. Poblacion inicial dentro de PyGAD")
    print("  tipo:", type(pi).__module__ + "." + type(pi).__name__, "| forma:", pi.shape, "| dtype:", pi.dtype,
          "| tipo de un gen:", type(pi[0][0]).__name__)
    print("  fila 0 == genoma base de netconvert:", bool(np.array_equal(pi[0], np.array(base))))
    for t in ejemplos:
        i, ps, po = posiciones(t)
        print(f"  {t} en la fila 1 (aleatoria): ciclo {pi[1][i]}, pesos {[int(pi[1][p]) for p in ps]}, "
              f"desfase {pi[1][po]}")
    print()

    pop = ga.population
    k = int(np.argmax(ga.last_generation_fitness))
    mejor = pop[k]
    print("PASO 6. Poblacion final y mejor individuo")
    print("  ga.population: forma", pop.shape, "| dtype", pop.dtype)
    print("  mejor individuo: fila", k, "| tipo", type(mejor).__name__, "| aptitud", ga.last_generation_fitness[k],
          "| J =", round(1 / ga.last_generation_fitness[k] - 1e-6, 2))
    for nombre, a, b in (("ciclos", 0, N), ("pesos", N, N + P), ("desfases", N + P, N + P + N)):
        print(f"  {nombre} iguales a netconvert: {int((pi[0][a:b] == mejor[a:b]).sum())} de {b - a}")
    print("  repr que ve Python:")
    print("  " + repr(mejor).replace("\n", "\n  "))
    print()

    print("PASO 7. Decodificacion del mejor individuo (apply_solution) y comparacion con la red guardada")
    red_mejor = meta["resultado"]["red_de_la_mejor"]
    red = {t.get("id"): t for t in ET.parse(red_mejor).getroot().findall("tlLogic")}
    for t in ejemplos:
        i, ps, po = posiciones(t)
        lay = con.TL_LAYOUT[t]
        # mismas cuentas que Controller.apply_solution, para un solo semaforo
        ciclo = max(int(mejor[i]), lay["ambar"] + sum(lay["minimos"]))
        pesos = [int(mejor[p]) for p in ps]
        variables = con.reparto(ciclo, lay["ambar"], lay["minimos"], pesos)
        sig = iter(variables)
        dur = [next(sig) if j in lay["indices"] else d for j, d in enumerate(lay["duraciones"])]
        desf = int(round(ciclo * float(mejor[po]) / 100)) % ciclo
        guardado = [int(float(p.get("duration"))) for p in red[t].findall("phase")]
        print(f"  {t}: genes ciclo={mejor[i]}, pesos={pesos}, desfase={mejor[po]} %")
        print(f"     -> ciclo {ciclo} s, ambar {lay['ambar']} s, minimos {lay['minimos']}, "
              f"sobran {ciclo - lay['ambar'] - sum(lay['minimos'])} s para repartir")
        print(f"     -> duraciones {dur}, desfase {desf} s | en {red_mejor}: {guardado}, "
              f"offset {red[t].get('offset')}")

    salida = f"{run}.cromosoma.txt"
    with open(salida, "w", encoding="utf-8") as f:
        f.write(f"# genoma base (netconvert), {len(base)} genes\n")
        f.write(f"ciclos   = {base[:N]}\n\npesos    = {base[N:N + P]}\n\ndesfases = {base[N + P:]}\n\n")
        f.write(f"# mejor individuo, {len(mejor)} genes\n")
        f.write(f"ciclos   = {mejor[:N].tolist()}\n\npesos    = {mejor[N:N + P].tolist()}\n\n"
                f"desfases = {mejor[N + P:].tolist()}\n\n")
        f.write("# orden de los semaforos\n")
        f.write(f"tls_ids = {list(tls)}\n\nsplit_counts = {split_counts}\n")
    print()
    print("cromosomas completos en", salida)
