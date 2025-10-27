"""
clase dedicada a la interaccion con SUMO y comunicacion con el algoritmo 
"""

import traci
import os


class Controller:
    def __init__(self, 
                 config = "./map.sumo.cfg", 
                 use_ui = False, 
                 port = 8813) -> None:
        
        self.USE_UI = use_ui # cambiar a True para ver UI
        self.CONFIG = config # .sumocfg or .sumo.cfg
        self.PORT = port
        self.SUMO_BINARY = self.get_sumo_binary()
        self.start_sumo_conn() # iniciar la conexion 
        self.save_state() # guardar la config inicial si no existe en root


    def save_state(self):
        """
        guardar la network en su estado inicial para realizar 
        carga rapida y dinamica desde archivo 
        """
        if "initial_state.xml" not in os.listdir():
            traci.simulation.saveState("initial_state.xml")
    

    def save_solution(self, filename):
        """
        guardar el estado final de la network con la solucion hallada
        """
        traci.simulation.saveState(fileName=filename)


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
        try:
            traci.start(cmd=[self.SUMO_BINARY, "-c", self.CONFIG, "--start"], port=self.PORT) 
        except Exception as e:
            raise Exception(f"{e}\n-> No se pudo establecer una conexion con sumo.")
    
    
    def reset(self):
        """
        sirve para resetear la simulacion 
        Se optimizo respecto a traci.load para mejorar la 
        velocidad de ejecucion y reducir complejidad computacional
        """
        traci.simulation.loadState("initial_state.xml") 


    def logic(self, logic, new_phases):
        return traci.trafficlight.Logic(
                programID=logic.programID,
                type=logic.type,
                currentPhaseIndex=logic.currentPhaseIndex,
                phases=tuple(new_phases),
                subParameter=logic.subParameter)


    def phase(self, phase, duration):
        return traci.trafficlight.Phase(
                    duration=float(duration),
                    state=phase.state,
                    minDur=phase.minDur,
                    maxDur=phase.maxDur)
    

    def get_tl_id_count(self):
        """
        retorna la cantidad de semaforos en un sistema
        """
        return traci.trafficlight.getIDCount()
    
    
    def get_tl_logic(self, tl_id):
        """
        retorna la logica (fases, tiempos) de una interseccion con semaforo
        """
        return traci.trafficlight.getAllProgramLogics(tlsID=tl_id)[0]
    

    def set_tl_logic(self, tls_id, new_logic):
        """
        asigna nueva logica (fases, tiempos) de una interseccion con semaforo
        """
        traci.trafficlight.setProgramLogic(tlsID=tls_id, logic=new_logic)


    def get_tl_ids(self):
        """
        retorna una lista con los ids de los semaforos
        """
        return traci.trafficlight.getIDList()


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
            
            # Vehiculos nuevos que entran a la simulacion
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


    def build_genome(self):
        genome = []
        phase_counts = []
        for tl_id in self.get_tl_ids():
            logic = traci.trafficlight.getAllProgramLogics(tl_id)[0]
            phase_counts.append(len(logic.phases))
            for phase in logic.phases:
                genome.append(phase.duration)
        return genome, phase_counts


    def close_sumo_conn(self):
        """
        Cerrar la sesion
        """
        traci.close()
