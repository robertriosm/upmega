"""
clase dedicada a la interaccion con SUMO y comunicacion con el algoritmo 
"""


import os
import sys
import traci
import sumolib
import time


class Controller:
    def __init__(self, 
                 config = "./map.sumo.cfg", 
                 use_ui = False, 
                 port = 8813) -> None:
        
        self.USE_UI = use_ui # cambiar a True para ver UI
        self.CONFIG = config # .sumocfg or .sumo.cfg
        self.PORT = port
        self.SUMO_BINARY = self.get_sumo_binary()


    def get_sumo_binary(self):
        """
        obtener la ruta del programa para conectar una sesion
        """
        if self.USE_UI:
            return r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo-gui.exe"
        else:
            return r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe"
    

    def start_sumo_conn(self):
        """
        iniciar la conexion a SUMO
        """
        traci.start(cmd=[self.SUMO_BINARY, "-c", self.CONFIG, "--start"], port=self.PORT) 
    

    def get_tl_id_count(self):
        """
        retorna la cantidad de semaforos en un sistema
        """
        return traci.trafficlight.getIDCount()


    def execute_simulation(self):
        """
        Avanzar la simulación hasta el final.
        Devuelve:
            - tiempos de espera en colas
            - tiempos de viajes
        """
        veh_wt = dict()          # {veh_id: tiempo_acumulado}
        veh_initial_tt = dict()  # {veh_id: tiempo_inicio}
        veh_tt = dict()          # {veh_id: tiempo de viaje completados}

        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()

            # Sobreescribir el tiempo acumulado de los vehiculos hasta que terminan su recorrido
            for veh_id in traci.vehicle.getIDList():
                veh_wt[veh_id] = traci.vehicle.getAccumulatedWaitingTime(vehID=veh_id)
            
            # Vehiculos nuevos que entran a la simulación
            for veh_id in traci.simulation.getDepartedIDList():
                veh_initial_tt[veh_id] = traci.simulation.getTime()

            # Vehiculos que terminan su recorrido
            for veh_id in traci.simulation.getArrivedIDList():
                if veh_id in veh_initial_tt:
                    start_time = veh_initial_tt.pop(veh_id)
                    end_time = traci.simulation.getTime()
                    travel_time = end_time - start_time
                    veh_tt[veh_id] = travel_time
        
        return veh_wt, veh_tt


    def close_sumo_conn(self):
        """
        Cerrar la sesion
        """
        traci.close()
