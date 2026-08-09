"""
clase dedicada a la interaccion con SUMO y comunicacion con el algoritmo 
"""

import traci, os, time, subprocess
import xml.etree.ElementTree as ET


class Controller:
    # minimos de seguridad, en segundos: verde minimo para que un vehiculo
    # detenido alcance a arrancar y cruzar, rojo minimo para despejar el cruce
    MIN_VERDE = 7
    MIN_ROJO = 3

    def __init__(self,
                 config = "map.sumo.cfg",
                 network = "test.net.xml",
                 routes = "map.rou.xml",
                 template = "template.net.xml",
                 port = 8813,
                 seed = 23,
                 demand = None,
                 max_steps = 10000,
                 max_quiet = 600) -> None:
        self.CONFIG = config
        self.PORT = port
        self.NETWORK = network
        self.TEMPLATE = template
        self.ROUTES = routes
        self.SEED = seed # 23 es el valor por defecto de SUMO, se fija para dejarlo registrado
        self.DEMAND = demand # parametros con los que se genero la demanda, para el registro
        # sin teletransportes una red trabada no se destraba sola, asi que hace
        # falta un tope de pasos para que una mala solucion no cuelgue la corrida
        self.MAX_STEPS = max_steps
        self.MAX_QUIET = max_quiet # pasos seguidos sin una sola llegada = red trabada
        self.SUMO_BINARY = self.get_sumo_binary()
        self.prepare_dirs()


    def sim_flags(self):
        """
        banderas comunes a toda simulacion, para que evaluaciones, baseline y
        detalle midan exactamente bajo las mismas condiciones.

        --time-to-teleport -1 desactiva los teletransportes. SUMO deja de
        rescatar vehiculos atascados, asi que lo que se mide es lo que de
        verdad pasaria en la calle. El precio es que una red trabada ya no se
        destraba sola: de ahi el tope de pasos.

        --tripinfo-output.write-unfinished es obligatorio junto con lo anterior.
        Sin el, los vehiculos que quedan atascados no aparecen en el tripinfo y
        una solucion que traba la red puntua MEJOR que una sana, porque solo se
        promedia a los que lograron salir. Medido: una red trabada daba J=538
        sin la bandera y J=2033 con ella.
        """
        return ["--time-to-teleport", "-1",
                "--tripinfo-output.write-unfinished", "true",
                "--tripinfo-output.write-undeparted", "true",
                "--seed", str(self.SEED),
                "--no-step-log", "true", "--no-warnings", "true"]


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

        # todo lo que la evaluacion necesita saber de la red se lee aqui, una
        # sola vez. A partir de este punto evaluar no depende de TraCI, que es
        # lo que permite correr varias simulaciones a la vez
        self.cache_tl_layout()
        self.cache_template()


    def cache_tl_layout(self):
        """
        lee una sola vez la estructura de cada semaforo: estados de fase,
        duraciones originales, indices variables, ambar total, minimos y
        programID.

        Todo eso es invariante entre soluciones: los ambares se copian sin
        tocar y los estados nunca cambian. Consultarlo por evaluacion era
        trabajo repetido y, sobre todo, ataba la evaluacion a la conexion TraCI.
        """
        self.TL_LAYOUT = {}

        for tl_id in self.get_tl_ids():
            logic = self.get_tl_logic(tl_id)
            indices, ambar, minimos = self.split_layout(logic)
            self.TL_LAYOUT[tl_id] = {
                "estados": [p.state for p in logic.phases],
                "duraciones": [int(round(float(p.duration))) for p in logic.phases],
                "indices": indices,
                "ambar": ambar,
                "minimos": minimos,
                "programID": logic.programID,
            }

        return self.TL_LAYOUT


    def cache_template(self):
        """
        parte la plantilla en (cabecera, cola) por el punto donde se insertan
        los tlLogic: el inicio de la linea del primer <junction>.

        Antes cada evaluacion hacia ET.parse de 1.37 MB, ET.indent sobre el
        arbol entero y tree.write: del orden de medio segundo de Python por
        individuo. Como texto es concatenar, milisegundos.
        """
        with open(self.TEMPLATE, "r", encoding="utf-8") as f:
            texto = f.read()

        corte = texto.find("<junction ")
        if corte < 0:
            raise RuntimeError(f"No se encontro ninguna etiqueta <junction> en {self.TEMPLATE}")

        # retroceder al inicio de la linea para controlar la indentacion
        inicio = texto.rfind("\n", 0, corte) + 1
        self.TPL_HEAD = texto[:inicio]
        self.TPL_TAIL = texto[inicio:]
    
    
    def reset(self):
        """
        sirve para resetear la simulacion 
        mejora la velocidad de ejecucion y reduce complejidad computacional
        """
        traci.load(["-n", self.NETWORK, "-r", self.ROUTES] + self.sim_flags())
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
                    "--statistic-output", f"outputs/{sid}.stats.xml"] + self.sim_flags())


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
        Ejecuta la simulación por TraCI y lee los resultados.

        Es el camino original, avanzando la simulacion paso a paso desde aqui.
        Se conserva porque permite el guardia de inactividad y porque sirve de
        referencia para comprobar que el camino por subproceso da lo mismo.
        """
        self.reload(sid)
        pasos, trabada = self.step_until_done()
        self.reset()

        # Esperar brevemente a que SUMO termine de escribir el archivo
        time.sleep(0.05)

        durations, waiting_times, stats = self.read_results(sid)
        stats["pasos"] = pasos
        stats["trabada"] = trabada

        return durations, waiting_times, stats


    def run_simulation(self, sid):
        """
        Ejecuta la simulación como proceso aparte, sin TraCI.

        Es lo que permite paralelizar: cada evaluacion queda aislada con su
        propia red, su semilla y sus archivos, sin estado compartido. Ademas la
        muerte del proceso garantiza que las salidas quedaron completas en
        disco, cosa que la respuesta de traci.load no garantiza.

        --end sustituye al bucle de pasos. Es tiempo de SIMULACION, no de
        reloj: un tope por reloj haria que el resultado dependiera de la carga
        de la maquina y rompería la reproducibilidad.
        """
        cmd = [self.SUMO_BINARY,
               "-n", f"logics/{sid}.net.xml",
               "-r", self.ROUTES,
               "--tripinfo-output", f"outputs/{sid}.xml",
               "--statistic-output", f"outputs/{sid}.stats.xml",
               "--end", str(self.MAX_STEPS)] + self.sim_flags()

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"SUMO fallo en la evaluacion {sid} (codigo {e.returncode}): {e.stderr}"
            ) from e

        return self.read_results(sid)


    def read_results(self, sid):
        """
        parsea las salidas de una evaluacion. Lo comparten los dos caminos
        (TraCI y subproceso) para garantizar que calculan exactamente lo mismo.
        """
        output_path = f"outputs/{sid}.xml"

        if not os.path.exists(output_path):
            raise FileNotFoundError(f"No se generó el archivo {output_path}")

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                raise ValueError(f"El archivo {output_path} está vacío.")
            tree = ET.fromstring(content)

        durations = []
        waiting_times = []
        sin_terminar = 0

        for item in tree.findall("tripinfo"):
            if float(item.get("arrival", 0)) < 0:
                # nunca llego a destino. Se le cobra el horizonte completo en
                # vez de lo que llevara acumulado al cortar: si no, cortar antes
                # abarata a las soluciones que traban la red y el GA aprende a
                # trabarla. Asi la penalizacion no depende de cuando se corto
                sin_terminar += 1
                durations.append(float(self.MAX_STEPS))
                waiting_times.append(float(self.MAX_STEPS))
            else:
                durations.append(float(item.get("duration", 0)))
                waiting_times.append(float(item.get("waitingTime", 0)))

        stats = self.read_statistics(f"outputs/{sid}.stats.xml")
        stats["sin_terminar"] = sin_terminar
        stats["registros"] = len(durations)
        # por subproceso no se cuentan pasos; la red trabada se detecta igual
        stats["pasos"] = None
        stats["trabada"] = stats.get("sin_llegar", 0) > 0

        return durations, waiting_times, stats


    def step_until_done(self):
        """
        avanza la simulacion hasta que no quede ningun vehiculo por salir,
        con un tope de pasos.

        El tope existe porque sin teletransportes una red trabada no se
        destraba: sin el, una mala solucion colgaria la corrida entera. Si se
        alcanza el tope la simulacion se corta, pero gracias a
        --tripinfo-output.write-unfinished los vehiculos atascados igual quedan
        contabilizados con su demora acumulada, asi que la solucion puntua mal
        en vez de puntuar bien por omision.
        """
        pasos, silencio = 0, 0

        while traci.simulation.getMinExpectedNumber() > 0 and pasos < self.MAX_STEPS:
            traci.simulationStep()
            pasos += 1

            # una red sana produce llegadas de forma continua. Si pasan varios
            # minutos simulados sin que llegue nadie, esta trabada: cortar ahi
            # en vez de agotar el tope ahorra la mayor parte del costo, porque
            # las soluciones malas son justo las que llegaban al tope
            if traci.simulation.getArrivedNumber() > 0:
                silencio = 0
            else:
                silencio += 1
                if silencio >= self.MAX_QUIET:
                    break

        return pasos, traci.simulation.getMinExpectedNumber() > 0


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

        # vehiculos que seguian en la red al terminar: con los teletransportes
        # desactivados, cualquier valor > 0 significa que la solucion trabo la red
        vehiculos = root.find("vehicles")
        if vehiculos is not None:
            stats["sin_llegar"] = int(vehiculos.get("running", 0)) + int(vehiculos.get("waiting", 0))

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
                    "--edgedata-output", paths["edgedata"]] + self.sim_flags())

        self.step_until_done()
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

        El genoma trae tres tramos:
        - un ciclo por semaforo, en segundos
        - los pesos de reparto de las fases variables
        - un offset por semaforo, en porcentaje del ciclo

        gene_slices son los indices de corte del tramo de pesos.
        """
        n_tls = len(tls_ids)
        n_pesos = int(gene_slices[-1])
        esperado = n_tls + n_pesos + n_tls

        if len(solution) != esperado:
            raise ValueError(
                f"El genoma trae {len(solution)} genes y se esperaban {esperado}: "
                f"{n_tls} ciclos + {n_pesos} pesos + {n_tls} offsets."
            )

        ciclos = solution[:n_tls]
        pesos_all = solution[n_tls:n_tls + n_pesos]
        offsets_pct = solution[n_tls + n_pesos:]

        partes = []

        for i, tl_id in enumerate(tls_ids):
            tl = self.TL_LAYOUT[tl_id]
            indices, ambar, minimos = tl["indices"], tl["ambar"], tl["minimos"]

            # el ciclo nunca puede bajar del minimo fisico de la interseccion
            ciclo = max(int(ciclos[i]), ambar + sum(minimos))
            pesos = pesos_all[gene_slices[i]:gene_slices[i + 1]]
            variables = self.reparto(ciclo, ambar, minimos, pesos)

            # las fases variables toman su reparto, los ambares se copian
            duraciones = []
            siguiente = iter(variables)
            for j, original in enumerate(tl["duraciones"]):
                duraciones.append(next(siguiente) if j in indices else original)

            # el offset viaja como porcentaje porque su dominio es [0, ciclo)
            # y el ciclo es otro gen: en porcentaje el rango queda fijo
            offset = int(round(ciclo * float(offsets_pct[i]) / 100)) % ciclo

            partes.append(f'    <tlLogic id="{tl_id}" type="static" '
                          f'programID="{tl["programID"]}" offset="{offset}">\n')
            for estado, duracion in zip(tl["estados"], duraciones):
                partes.append(f'        <phase duration="{float(duracion)}" state="{estado}"/>\n')
            partes.append('    </tlLogic>\n')

        with open(f"logics/{sid}.net.xml", "w", encoding="utf-8") as f:
            f.write(self.TPL_HEAD)
            f.write("".join(partes))
            f.write(self.TPL_TAIL)
    

    def phase_kind(self, state):
        """
        clasifica una fase por su estado. Se pregunta primero por el verde: una
        fase con movimiento en verde es una fase verde aunque arrastre un ambar
        """
        if 'G' in state or 'g' in state:
            return "verde"
        if 'y' in state:
            return "ambar"
        return "rojo"


    def split_layout(self, logic):
        """
        estructura de reparto de una interseccion:
        (indices de las fases que son variables, ambar total, minimos)

        Los ambares no son variables: su duracion la fija la velocidad de
        aproximacion, no el trafico. Se suman aparte y se copian tal cual.

        Es la pieza que comparten el armado del genoma, el espacio de busqueda
        y la decodificacion, para que las tres vean la misma estructura.
        """
        indices, minimos, ambar = [], [], 0

        for j, phase in enumerate(logic.phases):
            tipo = self.phase_kind(phase.state)
            if tipo == "ambar":
                ambar += int(round(float(phase.duration)))
            else:
                indices.append(j)
                minimos.append(self.MIN_VERDE if tipo == "verde" else self.MIN_ROJO)

        return indices, ambar, minimos


    def min_cycle(self, logic):
        """
        ciclo mas corto fisicamente admisible: los ambares mas los minimos
        """
        _, ambar, minimos = self.split_layout(logic)
        return ambar + sum(minimos)


    def reparto(self, ciclo, ambar, minimos, pesos):
        """
        reparte el tiempo del ciclo que no es ambar entre las fases variables,
        proporcionalmente a sus pesos y respetando los minimos de seguridad.

        Usa restos mayores para que la suma de exactamente el ciclo pedido: sin
        eso el redondeo haria que el ciclo real se aleje del que pidio el gen.
        """
        extra = ciclo - ambar - sum(minimos)
        pesos = [max(1, int(p)) for p in pesos]
        total = sum(pesos)

        crudo = [p * extra / total for p in pesos]
        parte = [int(x) for x in crudo]

        # el sobrante del redondeo va a las fases con mayor resto fraccionario
        sobrante = extra - sum(parte)
        orden = sorted(range(len(crudo)), key=lambda k: crudo[k] - parte[k], reverse=True)
        for k in orden[:sobrante]:
            parte[k] += 1

        return [m + p for m, p in zip(minimos, parte)]


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
        arma el genoma en tres tramos:

            [ un ciclo por semaforo ]  [ pesos de reparto ]  [ un offset por semaforo ]

        El ciclo es la variable que mas pesa en la demora y antes no existia:
        era la suma de las duraciones, o sea que moverlo exigia mutar de forma
        coordinada las 3 o 4 fases de cada interseccion a la vez. Ahora es un
        gen y la mutacion lo alcanza directo.

        Las duraciones dejan de ser segundos absolutos y pasan a ser pesos de
        reparto del tiempo disponible. Los ambares no son genes.

        Devuelve tambien cuantas fases variables tiene cada semaforo, que es lo
        que permite trocear el tramo de pesos al decodificar.
        """
        ciclos, pesos, offsets_pct, split_counts = [], [], [], []
        base_offsets = self.read_offsets(self.NETWORK)

        for tl_id in self.get_tl_ids():
            logic = traci.trafficlight.getAllProgramLogics(tl_id)[0]
            indices, ambar, minimos = self.split_layout(logic)

            ciclo = int(round(sum(float(p.duration) for p in logic.phases)))
            ciclos.append(ciclo)
            split_counts.append(len(indices))

            # el peso que reproduce exactamente la duracion original: lo que
            # esa fase tiene por encima de su minimo
            for j, minimo in zip(indices, minimos):
                pesos.append(max(1, int(round(float(logic.phases[j].duration))) - minimo))

            segundos = base_offsets.get(tl_id, 0.0)
            offsets_pct.append(int(round(100 * segundos / ciclo)) % 100 if ciclo > 0 else 0)

        return ciclos + pesos + offsets_pct, split_counts


    def close_sumo_conn(self):
        """
        Cerrar la sesion
        """
        try:
            traci.close()
        except Exception as e:
            raise ConnectionError(f"Error al cerrar conexion con SUMO: {e}")
        