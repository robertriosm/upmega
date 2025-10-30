"""
clase dedicada a la interaccion con SUMO y comunicacion con el algoritmo 
"""

import traci, os, time, sumolib
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
    

    def reload(self, idx, logic):
        """
        llamar a ejecucion con nuevo archivo para guardar datos.
        Este metodo necesita de: 'data/' y 'logics/' para funcionar.
        en data guarda resultados
        en logics obtiene la solucion 
        """
        traci.load(["-n", "test.net.xml", "-r", self.ROUTES, "-a", f"logics/{logic}.add.xml", "--tripinfo-output", f"data/{idx}.xml"])


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


    def execute_simulation(self, solution_idx, net_path):
        """
        abre un archivo, ejecuta la simulacion, guarda la simulacion 
        en el archivo, luego colecta los datos del archivo en forma de lista
        """
        with open(f"data/{solution_idx}.xml", encoding="utf-8", mode="w+t") as f:
            
            self.reload(f.name, net_path)

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
    

    def apply_solution(self, solution, solution_idx, tls_ids, offsets):
        """
        Aplica una configuración y genera un archivo para SUMO.

        - solution: vector de genes (duraciones)
        - solution_idx: id para escribir los archivos
        - tls_ids: lista con los IDs de los semáforos
        - offsets: lista de índices de inicio/fin de cada semáforo (len = len(tls_ids)+1)
        """

        if len(solution) != offsets[-1]:
            raise ValueError("Solution length does not match expected number of genes.")

        root = ET.Element("additional")

        for i, tl_id in enumerate(tls_ids):
            # utilizar los indices en los offsets para mapear las duraciones de las fases
            start, end = offsets[i], offsets[i + 1]
            durations = solution[start:end]

            logic = self.get_tl_logic(tl_id)

            # crear nuevas fases con las duraciones
            new_phases = [
                self.phase(logic.phases[j], durations[j])
                for j in range(len(logic.phases))
            ]

            new_logic = self.logic(logic, new_phases)

            tl_elem = ET.SubElement(root, "tlLogic", {
                "id": tl_id,
                "type": getattr(new_logic, "type", "static"),
                "programID": getattr(new_logic, "programID", "0"),
                "offset": str(getattr(new_logic, "offset", "0"))
            })

            for phase in new_logic.phases:
                ET.SubElement(tl_elem, "phase", {
                    "duration": str(phase.duration),
                    "state": phase.state
                })

        tree = ET.ElementTree(root)
        tree.write(f"logics/{solution_idx}.add.xml", encoding="utf-8", xml_declaration=True)

        return str(solution_idx)
    

    def build_genome(self):
        """
        recorre los ids de los semaforos para guardar en una lista los tiempos 
        de fases, esto es el genoma, tambien cuenta la cantidad 
        de fases de un semaforo para asociar fases con semaforos
        """
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
        try:
            traci.close()
        except Exception as e:
            raise ConnectionError(f"Error al cerrar conexion con SUMO: {e}")
        