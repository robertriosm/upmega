"""
clase dedicada a la interaccion con SUMO y comunicacion con el algoritmo 
"""

import traci, os, time
import xml.etree.ElementTree as ET


class Controller:
    def __init__(self, 
                 config = "map.sumo.cfg", 
                 network = "test.net.xml",
                 routes = "map.rou.xml",
                 port = 8813) -> None:
        self.CONFIG = config # .sumocfg | .sumo.cfg
        self.PORT = port
        self.NETWORK = network
        self.ROUTES = routes
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
        traci.simulation.saveState(f"{filename}.xml")


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
        
        cmd = [self.SUMO_BINARY, "-c", self.CONFIG] 
        if superfast: 
            cmd += ["--no-warnings", "true", "--no-step-log", "true"] 

        try:
            traci.start(cmd, port=self.PORT) 
        except Exception as e: 
            raise RuntimeError(f"Error iniciando SUMO: {e}") 
    
    
    def reset(self):
        """
        sirve para resetear la simulacion 
        mejora la velocidad de ejecucion y reduce complejidad computacional
        """
        traci.load(["-n", self.NETWORK, "-r", self.ROUTES]) 
        time.sleep(0.01)
    

    def reload(self, idx):
        """
        llamar a ejecucion con nuevo archivo para guardar datos.
        Este metodo necesita del folder 'data/' para funcionar.
        """
        traci.load(["-n", self.NETWORK, "-r", self.ROUTES, "--tripinfo-output", f"data/{idx}.xml"])


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


    def execute_simulation(self, solution_idx):
        """
        abre un archivo, ejecuta la simulacion, guarda la simulacion 
        en el archivo, luego colecta los datos del archivo en forma de lista
        """
        with open(f"data/{solution_idx}.xml", encoding="utf-8", mode="w+t") as f:
            
            self.reload(solution_idx)

            while traci.simulation.getMinExpectedNumber() > 0:
                traci.simulationStep()
            
            self.reset()

            tree = ET.fromstring(f.read())

            durations = []
            waiting_times = []

            for item in tree.findall("tripinfo"):
                durations.append(item.get("duration"))
                waiting_times.append(item.get("waitingTime"))
            
            return durations, waiting_times
    

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
        