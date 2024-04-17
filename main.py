# import os
# import sys
# import subprocess
import traci


# traci.start(["C:/Program Files (x86)/Eclipse/Sumo/bin/sumo-gui.exe", "-c", "trialmap/hello.sumocfg"]) # .sumocfg or .sumo.cfg

# step = 0

# while step < 10:
#     traci.simulationStep()
#     if traci.inductionloop.getLastStepVehicleNumber("0") > 0:
#         traci.trafficlight.setRedYellowGreenState("0", "GrGr")
#     step += 1

# traci.close()


traci.start(["C:/Program Files (x86)/Eclipse/Sumo/bin/sumo-gui.exe", "-c", "example1/run.sumo.cfg"]) # .sumocfg or .sumo.cfg

step = 0

while step < 10:
    traci.simulationStep()
    if traci.inductionloop.getLastStepVehicleNumber("0") > 0:
        traci.trafficlight.setRedYellowGreenState("0", "GrGr")
    step += 1

traci.close()
