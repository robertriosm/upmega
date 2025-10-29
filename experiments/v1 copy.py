import os, traci, sumolib
import xml.etree.ElementTree as ET
import numpy as np
import re
from time import sleep

CONFIG = "map.sumo.cfg"
NETWORK = "test.net.xml"
ROUTES = "map.rou.xml"
PORT = 8813
SUMO_BINARY = sumolib.checkBinary("sumo")
IDSOL = "1"

# Lanzar SUMO una sola vez
traci.start([SUMO_BINARY, "-c", CONFIG], port=PORT)

with open(f"data/{IDSOL}.xml", encoding="utf-8", mode="w+t") as f:
    # Recargar escenario
    traci.load(["-n", NETWORK, "-r", ROUTES, "--tripinfo-output", f.name])

    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

    traci.load(["-n", NETWORK, "-r", ROUTES])
    sleep(0.01)
    tree = ET.fromstring(f.read())

    # Parse an XML file
    durations = []
    wts = []

    # Find and print elements
    for item in tree.findall("tripinfo"):
        duration = item.get("duration")
        waiting_time = item.get("waitingTime")
        durations.append(duration)
        wts.append(waiting_time)

    mean_wt = np.mean(np.array(wts, dtype=np.float16))
    mean_dur = np.mean(np.array(durations, dtype=np.float16))

    # Mantener conexión viva para futuras simulaciones
    print("Simulación finalizada sin cerrar TraCI.")
    print(f"MEAN WT: {mean_wt}")
    print(f"MEAN DUR: {mean_dur}")

traci.close()