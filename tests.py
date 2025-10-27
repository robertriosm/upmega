import os
import sys
# import sumolib
import traci
# import sumolib

SUMO_BINARY = r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe"
CONFIG = "map.sumo.cfg"

# Arrancar SUMO pausado (sin avanzar el tiempo)
traci.start([SUMO_BINARY, "-c", CONFIG, "--start", "--no-step-log", "true"])

# Leer datos sin avanzar la simulación
tl_ids = traci.trafficlight.getIDList()
print("Semáforos:", tl_ids)

for tl in tl_ids:
    logics = traci.trafficlight.getAllProgramLogics(tl)
    print(f"{tl}: {logics} fases")

# Cerrar conexión
traci.close()

# print("SUMO_HOME =", os.environ.get("SUMO_HOME"))
# tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
# print("tools =", tools)
# print("checkBinary sumo =", sumolib.checkBinary("sumo"))
# print("exists? sumo.exe =", os.path.exists(os.path.join(os.environ["SUMO_HOME"], "bin", "sumo.exe")))

# print("SUMO_HOME =", os.environ.get("SUMO_HOME"))

