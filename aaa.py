import os
import sys
import sumolib

print("SUMO_HOME =", os.environ.get("SUMO_HOME"))
tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
print("tools =", tools)
print("checkBinary sumo =", sumolib.checkBinary("sumo"))
print("exists? sumo.exe =", os.path.exists(os.path.join(os.environ["SUMO_HOME"], "bin", "sumo.exe")))

print("SUMO_HOME =", os.environ.get("SUMO_HOME"))
