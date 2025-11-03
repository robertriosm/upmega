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
                 template = "template.net.xml",
                 port = 8813) -> None:
        self.CONFIG = config
        self.PORT = port
        self.NETWORK = network
        self.TEMPLATE = template
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
    

    def start_sumo_conn(self, noSteps = True, noWarns = True):
        """
        iniciar la conexion a SUMO
        """
        if not os.path.exists(self.CONFIG):
            raise FileNotFoundError(f"SUMO config no existe: {self.CONFIG}")
        
        cmd = [self.SUMO_BINARY, "-c", self.CONFIG, "--no-step-log", "true", "--no-warnings", "true"] 

        try:
            traci.start(cmd, port=self.PORT) 
        except Exception as e: 
            raise RuntimeError(f"Error iniciando SUMO: {e}") 
    
    
    def reset(self):
        """
        sirve para resetear la simulacion 
        mejora la velocidad de ejecucion y reduce complejidad computacional
        """
        traci.load(["-n", self.NETWORK, "-r", self.ROUTES, 
                    "--no-step-log", "true", "--no-warnings", "true"]) 
        time.sleep(0.01)
    

    def reload(self, sid):
        """
        llamar a ejecucion con nuevo archivo para guardar datos.
        Este metodo necesita de: 'outputs/' y 'logics/' para funcionar.
        - logics guarda la solucion para ser probada 
        - outputs guarda resultados de simulacion
        """
        traci.load(["-n", f"logics/{sid}.net.xml", "-r", self.ROUTES, 
                    "--tripinfo-output", f"outputs/{sid}.xml",
                    "--no-step-log", "true", "--no-warnings", "true"])


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


    def execute_simulation(self, sid):
        """
        Ejecuta la simulación y lee los resultados desde tripinfo-output.
        """
        output_path = f"outputs/{sid}.xml"

        # Ejecutar simulación con salida de tripinfos
        self.reload(sid)
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
        self.reset()

        # Esperar brevemente a que SUMO termine de escribir el archivo
        time.sleep(0.05)

        # Leer el archivo generado por SUMO
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"No se generó el archivo {output_path}")

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                raise ValueError(f"El archivo {output_path} está vacío.")
            tree = ET.fromstring(content)

        durations = []
        waiting_times = []
        for item in tree.findall("tripinfo"):
            durations.append(float(item.get("duration", 0)))
            waiting_times.append(float(item.get("waitingTime", 0)))

        return durations, waiting_times

    

    def apply_solution(self, solution, sid, tls_ids, offsets):
        """
        Construye un archivo con la solucion para aplicarle a SUMO
        """

        if len(solution) != offsets[-1]:
            raise ValueError("Solution length does not match expected number of genes.")

        tree = ET.parse(self.TEMPLATE)
        root = tree.getroot()

        # Buscar el primer <junction> para insertar los <tlLogic> antes de eso
        insert_index = None
        for i, elem in enumerate(root):
            if elem.tag == "junction":
                insert_index = i
                break 
        if insert_index is None:
            raise RuntimeError("No se encontró ninguna etiqueta <junction> en la plantilla base.")

        # --- Generar e insertar los nuevos tlLogic ---
        for i, tl_id in enumerate(tls_ids):
            start, end = offsets[i], offsets[i + 1]
            durations = solution[start:end]

            logic = self.get_tl_logic(tl_id)
            new_phases = [
                self.phase(logic.phases[j], durations[j])
                for j in range(len(logic.phases))
            ]
            new_logic = self.logic(logic, new_phases)

            tl_elem = ET.Element("tlLogic", {
                "id": str(tl_id),
                "type": "static",
                "programID": str(new_logic.programID),
                "offset": "0"
            })

            for phase in new_logic.phases:
                ET.SubElement(tl_elem, "phase", {
                    "duration": str(phase.duration),
                    "state": str(phase.state)
                })

            # Insertar justo antes del primer <junction>
            root.insert(insert_index, tl_elem)
            insert_index += 1  # mantener el orden para múltiples tlLogic

        ET.indent(tree, space="\t")
        tree.write(f"logics/{sid}.net.xml", encoding="utf-8", xml_declaration=True)
    

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
        