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
                 template = "template.net.xml",
                 port = 8813,
                 seed = 23) -> None:
        self.CONFIG = config
        self.PORT = port
        self.NETWORK = network
        self.TEMPLATE = template
        self.ROUTES = routes
        self.SEED = seed # 23 es el valor por defecto de SUMO, se fija para dejarlo registrado
        self.SUMO_BINARY = self.get_sumo_binary()
        self.prepare_dirs()


    def prepare_dirs(self):
        """
        crear las carpetas de trabajo si no existen, un clone limpio no las trae
        """
        for d in ("logics", "outputs", "detail"):
            os.makedirs(d, exist_ok=True)


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
                    "--seed", str(self.SEED),
                    "--no-step-log", "true", "--no-warnings", "true"])
        time.sleep(0.01)


    def reload(self, sid):
        """
        llamar a ejecucion con nuevo archivo para guardar datos.
        Este metodo necesita de: 'outputs/' y 'logics/' para funcionar.
        - logics guarda la solucion para ser probada
        - outputs guarda resultados de simulacion

        Salidas por evaluacion, las dos baratas:
        - tripinfo: un registro por vehiculo, es la fuente del fitness
        - statistic: un resumen agregado de ~2KB, trae timeLoss, velocidad media
          y sobre todo los teleports, que delatan una solucion con gridlock
        """
        traci.load(["-n", f"logics/{sid}.net.xml", "-r", self.ROUTES,
                    "--tripinfo-output", f"outputs/{sid}.xml",
                    "--statistic-output", f"outputs/{sid}.stats.xml",
                    "--seed", str(self.SEED),
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

        return durations, waiting_times, self.read_statistics(f"outputs/{sid}.stats.xml")


    def read_statistics(self, path):
        """
        lee el resumen agregado que SUMO escribe con --statistic-output.
        Devuelve dict vacio si el archivo no existe, para no tumbar una corrida
        entera por una salida que es complementaria y no critica.
        """
        if not os.path.exists(path):
            return {}

        root = ET.parse(path).getroot()
        stats = {}

        trips = root.find("vehicleTripStatistics")
        if trips is not None:
            for key in ("count", "routeLength", "speed", "duration",
                        "waitingTime", "timeLoss", "departDelay"):
                if trips.get(key) is not None:
                    stats[key] = float(trips.get(key))

        teleports = root.find("teleports")
        if teleports is not None:
            stats["teleports"] = int(teleports.get("total", 0))

        safety = root.find("safety")
        if safety is not None:
            stats["collisions"] = int(safety.get("collisions", 0))

        return stats


    def run_detailed(self, network, tag):
        """
        corre una simulacion sobre una red concreta pidiendole a SUMO todas las
        salidas: por vehiculo, resumen agregado, serie de tiempo y por arista.

        Se usa fuera del ciclo del GA (baseline y mejor solucion), por eso puede
        permitirse escribir archivos grandes: son dos simulaciones por corrida,
        no mil. Es lo que permite responder donde y cuando mejoro la red, que
        el tripinfo por si solo no puede decir.
        """
        paths = {
            "tripinfo":  f"detail/{tag}.tripinfo.xml",
            "statistic": f"detail/{tag}.stats.xml",
            "summary":   f"detail/{tag}.summary.xml",
            "edgedata":  f"detail/{tag}.edgedata.xml",
        }

        traci.load(["-n", network, "-r", self.ROUTES,
                    "--tripinfo-output", paths["tripinfo"],
                    "--statistic-output", paths["statistic"],
                    "--summary-output", paths["summary"],
                    "--edgedata-output", paths["edgedata"],
                    "--seed", str(self.SEED),
                    "--no-step-log", "true", "--no-warnings", "true"])

        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
        self.reset()
        time.sleep(0.05)

        return paths, self.read_statistics(paths["statistic"])


    def get_sumo_version(self):
        """
        version del binario, para dejar constancia de con que se corrio
        """
        try:
            return traci.getVersion()[1]
        except Exception:
            return None

    

    def apply_solution(self, solution, sid, tls_ids, gene_slices):
        """
        Construye un archivo con la solucion para aplicarle a SUMO.

        El genoma trae dos tramos:
        - [0 : n_fases]   duraciones de fase en segundos
        - [n_fases : ]    un offset por semaforo, en porcentaje del ciclo

        gene_slices son los indices de corte del primer tramo, uno por semaforo.
        """
        n_fases = int(gene_slices[-1])
        esperado = n_fases + len(tls_ids)

        if len(solution) != esperado:
            raise ValueError(
                f"El genoma trae {len(solution)} genes y se esperaban {esperado}: "
                f"{n_fases} duraciones + {len(tls_ids)} offsets."
            )

        duraciones = solution[:n_fases]
        offsets_pct = solution[n_fases:]

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
            start, end = gene_slices[i], gene_slices[i + 1]
            durations = duraciones[start:end]

            logic = self.get_tl_logic(tl_id)
            new_phases = [
                self.phase(logic.phases[j], durations[j])
                for j in range(len(logic.phases))
            ]
            new_logic = self.logic(logic, new_phases)

            # el offset viaja como porcentaje del ciclo porque su dominio
            # depende del ciclo, que es la suma de otros genes. Aqui se
            # convierte a segundos, que es lo que entiende SUMO
            ciclo = sum(float(d) for d in durations)
            offset = int(round(ciclo * float(offsets_pct[i]) / 100)) % int(round(ciclo)) if ciclo > 0 else 0

            tl_elem = ET.Element("tlLogic", {
                "id": str(tl_id),
                "type": "static",
                "programID": str(new_logic.programID),
                "offset": str(offset)
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
    

    def read_offsets(self, network):
        """
        offset en segundos de cada tlLogic del archivo de red.
        TraCI no expone el offset en su objeto Logic (solo lo hace para
        controladores NEMA), asi que hay que leerlo del XML.
        """
        root = ET.parse(network).getroot()
        return {tl.get("id"): float(tl.get("offset", 0)) for tl in root.findall("tlLogic")}


    def build_genome(self):
        """
        recorre los ids de los semaforos para armar el genoma, que tiene
        dos tramos:

        - duraciones: una por fase, en segundos
        - offsets: uno por semaforo, en porcentaje del ciclo

        Tambien devuelve la cantidad de fases de cada semaforo, que es lo que
        permite asociar cada duracion con su semaforo al decodificar.
        """
        genome = []
        phase_counts = []
        offsets_pct = []

        base_offsets = self.read_offsets(self.NETWORK)

        for tl_id in self.get_tl_ids():
            logic = traci.trafficlight.getAllProgramLogics(tl_id)[0]
            phase_counts.append(len(logic.phases))
            for phase in logic.phases:
                genome.append(phase.duration)

            ciclo = sum(float(p.duration) for p in logic.phases)
            segundos = base_offsets.get(tl_id, 0.0)
            offsets_pct.append(int(round(100 * segundos / ciclo)) % 100 if ciclo > 0 else 0)

        return genome + offsets_pct, phase_counts


    def close_sumo_conn(self):
        """
        Cerrar la sesion
        """
        try:
            traci.close()
        except Exception as e:
            raise ConnectionError(f"Error al cerrar conexion con SUMO: {e}")
        