"""
main del backend de SUMO, con y sin GUI
"""

import os
import sys
import traci
import sumolib

# configuracion para el controlador
USE_UI = False # cambiar a True para ver UI
CONFIG = "map.sumo.cfg" # .sumocfg or .sumo.cfg
PORT = 8813

# opcion para usar la UI
if USE_UI:
    SUMO_BINARY = "C:/Program Files (x86)/Eclipse/Sumo/bin/sumo-gui.exe"
else:
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("please declare environment variable 'SUMO_HOME'")
    
    SUMO_BINARY = sumolib.checkBinary("sumo") # C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe 
    
# iniciar conexion al simulador
traci.start(cmd=[SUMO_BINARY, "-c", CONFIG, "--start"], port=PORT) 

# ajustar la visualizacion si se utiliza
if USE_UI:
    traci.gui.setZoom("View #0", 500)

# file = open('results.txt', mode='w', encoding='utf')

# Avanzar la simulación hasta el final
# while traci.simulation.getMinExpectedNumber() > 0:
#     # time.sleep(0.1)
#     traci.simulationStep()

# try:
#     traci.vehicle
#     traci.trafficlight
    # file.write(f'getIDList: {traci.trafficlight.getIDList().__repr__()}')
    # file.write('\n')
    # file.write(f'getControlledLinks: {traci.trafficlight.getControlledLinks('1438391835').__repr__()}')
    # file.write('\n')
    # file.write(f'getControlledLanes: {traci.trafficlight.getControlledLanes('1438391835').__repr__()}')
    # file.write('\n')
    # file.write(f'getSpentDuration: {traci.trafficlight.getSpentDuration('1438391835').__repr__()}')
    # file.write('\n')
    # file.write(f'getRedYellowGreenState: {traci.trafficlight.getRedYellowGreenState('1438391835').__repr__()}')
    # file.write('\n')
    # file.write(f'getAllContextSubscriptionResults: {traci.trafficlight.getAllContextSubscriptionResults().__repr__()}')
    # file.write('\n')
    # # file.write('getBlockingVehicles: traci.trafficlight.getBlockingVehicles().__repr__()')
    # file.write('\n')
    # # file.write(f'getNemaPhaseCalls: {traci.trafficlight.getNemaPhaseCalls('1438391835').__repr__()}')
    # file.write('\n')
    # # file.write('getPriorityVehicles: traci.trafficlight.getPriorityVehicles().__repr__()')
    # file.write('\n')
    # file.write(f'getAllProgramLogics: {traci.trafficlight.getAllProgramLogics('1438391835').__repr__()}') # deprecated -> getCompleteRedYellowGreenDefinition
    # file.write('\n')
    # file.write(f'getNextSwitch: {traci.trafficlight.getNextSwitch('1438391835').__repr__()}')
    # file.write('\n')
    # # file.write('getServedPersonCount: {traci.trafficlight.getServedPersonCount().__repr__()')
    # file.write('\n')
    # # file.write('getRivalVehicles: {traci.trafficlight.getRivalVehicles().__repr__()')
    # file.write('\n')
    # file.write(f'getCompleteRedYellowGreenDefinition: {traci.trafficlight.getCompleteRedYellowGreenDefinition('1438391835').__repr__()}')
    # file.write('\n')
    # file.write(f'getProgram: {traci.trafficlight.getProgram('1438391835').__repr__()}')
    # file.write('\n')
    # file.write(f'getIDCount: {traci.trafficlight.getIDCount().__repr__()}')
#     ids = traci.trafficlight.getIDCount()
#     print(ids, type(ids))
# except Exception as e: 
#     print('hubo error: ', e)
#     file.close()

# cerrar conexion al simulador
# traci.close()
# file.close()

# ===========================
# Simulación y cálculo de T_viaje y T_espera
# ===========================
veh_travel_times = {}   # {vehID: tiempo_inicio}
completed_times = []    # lista de tiempos de viaje completados
veh_seen = set()        # vehículos que han aparecido
veh_wait_time = {}   # {veh_id: tiempo_acumulado}
waiting_times = []      # tiempos totales de espera de cada vehículo completado

while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()

    # Vehículos nuevos que entran a la simulación
    # for veh_id in traci.simulation.getDepartedIDList():
    #     veh_travel_times[veh_id] = traci.simulation.getTime()
    
    # # Vehículos que terminan su recorrido
    # for veh_id in traci.simulation.getArrivedIDList():
    #     if veh_id in veh_travel_times:
    #         start_time = veh_travel_times.pop(veh_id)
    #         end_time = traci.simulation.getTime()
    #         travel_time = end_time - start_time 
    #         completed_times.append(travel_time)
    
    # nuevos vehículos
    for vid in traci.simulation.getDepartedIDList():
        veh_seen.add(vid)
        veh_wait_time[vid] = 0.0

    # actualizar tiempos de espera en cada paso
    for vid in list(veh_seen):
        try:
            w = traci.vehicle.getAccumulatedWaitingTime(vid)
            veh_wait_time[vid] = w
        except traci.exceptions.TraCIException:
            # el vehículo desapareció (llegó antes de procesarlo)
            continue

    # vehículos que llegaron
    for vid in traci.simulation.getArrivedIDList():
        if vid in veh_wait_time:
            completed_times.append(veh_wait_time[vid])
            veh_seen.remove(vid)
            del veh_wait_time[vid]

# ===========================
# Resultado final
# ===========================
traci.close()

# if completed_times:
#     # ecuación: T = sum(k_i) / N
#     avg_travel_time = sum(completed_times) / len(completed_times)
#     print(f"Tiempo promedio de viaje (T): {avg_travel_time:.2f} s")
#     print(f"Vehículos completados: {len(completed_times)}")
# else:
#     print("No se registraron vehículos completados.")

if completed_times:
    avg_wait = sum(completed_times) / len(completed_times)
    print(f"Tiempo promedio de espera: {avg_wait:.2f} s ({len(completed_times)} vehículos)")
else:
    print("No se registraron vehículos completados.")