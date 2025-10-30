import os
import sys
import traci
import sumolib
import tempfile

CONFIG = "map.sumo.cfg" 
PORT = 8813
NETWORK = "test.net.xml"
ROUTES = "map.rou.xml"

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
    
SUMO_BINARY = sumolib.checkBinary("sumo") 

traci.start(cmd=[SUMO_BINARY, "-c", CONFIG], port=PORT)  

with tempfile.NamedTemporaryFile(mode='w+t', encoding='utf-8', suffix=".xml", delete_on_close=False) as temp_file:
    temp_file.close()

    traci.load(['-n', NETWORK, '-r', ROUTES, "--tripinfo", temp_file.name])

    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

    with open(temp_file.name, 'r', encoding='utf-8') as f:
        content = f.read()

    temp_file.close()
        
traci.close()


"""
    def apply_solution(self, solution, solution_idx, tls_ids, offsets): 
        ""
        aplicar configuracion de semaforos encontrada por algoritmo a la network 
        guardandola en un archivo listo para cargar al simulador
        ""
        if len(solution) != (offsets[-1]):
            raise ValueError("Solution length does not match expected number of genes.")

        for i, tl_id in enumerate(tls_ids): 
            start, end = offsets[i], offsets[i+1]
            durations = solution[start:end] 

            logic = self.controller.get_tl_logic(tl_id)
            new_phases = []

            for j, phase in enumerate(logic.phases):
                new_phases.append(self.controller.phase(phase, durations[j]))

            new_logic = self.controller.logic(logic, new_phases)
            self.controller.set_tl_logic(tl_id, new_logic)
        
        return self.controller.save_net(solution_idx)


"""