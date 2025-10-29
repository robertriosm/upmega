"""
clase dedicada a la interaccion con SUMO y comunicacion con el algoritmo 
"""

import traci
import traci.constants as tc
import os


class Controller:
    def __init__(self, 
                 config = "./map.sumo.cfg", 
                 use_ui = False, 
                 port = 8813) -> None:
        self.CONFIG = config # .sumocfg or .sumo.cfg
        self.PORT = port
        self.SUMO_BINARY = self.get_sumo_binary()

    def save_state(self):
        """
        guardar la network en su estado inicial para realizar 
        carga rapida y dinamica desde archivo 
        """
        if not os.path.exists("initial_state.state.xml"):
            traci.simulation.saveState("initial_state.state.xml")
    

    def save_solution(self, filename = "solution"):
        """
        guardar el estado final de la network con la solucion hallada
        """
        traci.simulation.saveState(f"{filename}.state.xml")


    def get_sumo_binary(self):
        """
        obtener la ruta del programa para conectar una sesion
        """
        return r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe"
    

    def start_sumo_conn(self, superfast = True):
        """
        iniciar la conexion a SUMO
        """
        if not os.path.exists(self.CONFIG):
            raise FileNotFoundError(f"SUMO config no existe: {self.CONFIG}")
        
        cmd = [self.SUMO_BINARY, "-c", self.CONFIG, "--start"] 
        if superfast: 
            cmd += ["--no-warnings", "true"] # "--no-step-log", "true",

        try:
            traci.start(cmd, port=self.PORT) 
        except Exception as e: 
            raise RuntimeError(f"Error iniciando SUMO: {e}") 
    
    
    def reset(self):
        """
        sirve para resetear la simulacion 
        Se optimizo respecto a traci.load para mejorar la 
        velocidad de ejecucion y reducir complejidad computacional
        """
        traci.load(['sumo', '-c', 'map.sumo.cfg', '--tripinfo-output', 'new_tripinfo.xml']) 


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
        return traci.trafficlight.getAllProgramLogics(tl_id)[0]
    

    def set_tl_logic(self, tls_id, new_logic):
        """
        asigna nueva logica (fases, tiempos) de una interseccion con semaforo
        """
        traci.trafficlight.setProgramLogic(tls_id, new_logic)


    def get_tl_ids(self):
        """
        retorna una lista con los ids de los semaforos
        """
        return traci.trafficlight.getIDList()


    def execute_simulation(self):
        veh_start_time = {}
        veh_wait_cache = {}
        completed_waits, completed_tts = [], []

        # Suscribirse a todas las variables relevantes
        traci.simulation.subscribe([tc.VAR_ACCUMULATED_WAITING_TIME])

        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()

            # Registrar nuevos vehículos
            for vid in traci.simulation.getDepartedIDList():
                veh_start_time[vid] = traci.simulation.getTime()

            # Obtener datos de todas las suscripciones de golpe
            all_data = traci.vehicle.getAllSubscriptionResults()
            if all_data:
                for vid, vars_dict in all_data.items():
                    wt = vars_dict.get(tc.VAR_ACCUMULATED_WAITING_TIME, 0.0)
                    veh_wait_cache[vid] = wt

            # Vehículos que completaron su viaje
            for vid in traci.simulation.getArrivedIDList():
                if vid in veh_start_time:
                    start = veh_start_time.pop(vid)
                    travel_time = traci.simulation.getTime() - start
                    completed_tts.append(travel_time)
                wt = veh_wait_cache.pop(vid, None)
                if wt is not None:
                    completed_waits.append(wt)

        return completed_waits, completed_tts 
    

    def build_genome(self, tl_ids):
        genome = []
        phase_counts = []
        for tl_id in tl_ids:
            logic = traci.trafficlight.getAllProgramLogics(tl_id)[0]
            phase_counts.append(len(logic.phases))
            for phase in logic.phases:
                genome.append(phase.duration)
        return genome, phase_counts


    def close_sumo_conn(self):
        """
        Cerrar la sesion
        """
        try:
            traci.close()
        except Exception as e:
            raise ConnectionError(f"Error al cerrar conexion con SUMO: {e}")
        