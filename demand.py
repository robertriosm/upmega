"""
generacion de demanda: viajes aleatorios para una cantidad de vehiculos dada
"""

import os
import xml.etree.ElementTree as ET

import randomTrips


DIR = "demand"


def route_file(num_cars, seed):
    return os.path.join(DIR, f"cars{num_cars}_s{seed}.rou.xml")


def trip_file(num_cars, seed):
    return os.path.join(DIR, f"cars{num_cars}_s{seed}.trips.xml")


def count_vehicles(path):
    """
    cuantos vehiculos quedaron de verdad en el archivo de rutas
    """
    return sum(1 for _ in ET.parse(path).getroot().iter("vehicle"))


def generate(num_cars, net = "test.net.xml", end = 1000, seed = 42, force = False):
    """
    genera un archivo de rutas con aproximadamente num_cars vehiculos.

    randomTrips no tiene una opcion de cantidad de vehiculos: emite una salida
    cada 'period' segundos entre begin y end, asi que la cantidad se controla
    con period = end / num_cars. La ventana se mantiene fija, de modo que subir
    num_cars sube la DENSIDAD de trafico y no la duracion de la simulacion.

    Ojo: --validate descarta los viajes que no rutean, asi que el archivo final
    trae menos vehiculos de los pedidos (~76% en esta red). Por eso se devuelve
    tambien cuantos quedaron.

    Retorna (ruta_del_archivo_de_rutas, info).
    """
    if num_cars <= 0:
        raise ValueError(f"num_cars debe ser mayor que 0, se recibio {num_cars}")

    os.makedirs(DIR, exist_ok=True)

    rutas = route_file(num_cars, seed)
    viajes = trip_file(num_cars, seed)
    period = end / num_cars

    if force or not os.path.exists(rutas):
        # -o es obligatorio: sin el, randomTrips escribe sobre trips.trips.xml,
        # que es su valor por defecto y ademas un archivo del proyecto
        args = ["-n", net,
                "-o", viajes,
                "-r", rutas,
                "-e", str(end),
                "-p", f"{period:.6f}",
                "-l",
                "--validate",
                "--seed", str(seed)]

        if not randomTrips.main(randomTrips.get_options(args)):
            raise RuntimeError(f"randomTrips no pudo generar viajes sobre {net}")

    generados = count_vehicles(rutas)

    return rutas, {
        "solicitados": num_cars,
        "generados": generados,
        "period": round(period, 6),
        "end": end,
        "seed": seed,
        "net": net,
        "archivo": rutas,
    }
