"""
graba en SUMO-GUI la simulacion de un plan semafórico, para la escena de la
simulacion del video.

Corre sumo-gui con las mismas opciones que usa el algoritmo (sin
teletransportes, semilla 23, mismas rutas), enfoca la camara en el corredor que
mas mejora y guarda una captura cada cierto numero de pasos. En cada captura
colorea los vehiculos segun la definicion de espera de SUMO: rojo si van a
0.1 m/s o menos, azul si se mueven. Ademas registra, por cuadro, cuantos
vehiculos hay en la red, cuantos estan detenidos, cuantos llegaron y la espera
acumulada; al terminar la simulacion calcula J con el tripinfo de esa misma
corrida.

Escribe en salida/: sumo_{plan}.mp4 (el clip) y sumo_{plan}.json (contadores y J).

Uso, desde esta carpeta:
    .venv\\Scripts\\python grabar_sumo.py            graba netconvert y la mejor solucion
    .venv\\Scripts\\python grabar_sumo.py netconvert
"""

import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import imageio_ffmpeg
import sumolib
import traci
import traci.constants as tc

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
SALIDA = AQUI / "salida"
sys.path.insert(0, str(AQUI))
import datos  # noqa: E402

SUMO_GUI = r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo-gui.exe"
VIA = "406701908"          # corredor que mas mejora (analisis espacial de la tesis)
ANCHO, ALTO = 1290, 840     # pixeles de cada captura (proporcion del panel de la escena)
T_FIN_CLIP = 1500           # segundos de simulacion que cubre el clip
CADA = 3                    # una captura cada 3 s de simulacion
FPS = 24                    # el clip avanza 72 s de simulacion por segundo de video
MAX_PASOS = 10000           # mismo tope que el algoritmo
UMBRAL_ESPERA = 0.1         # m/s, definicion de waitingTime de SUMO
AZUL, ROJO = (40, 120, 210, 255), (225, 45, 45, 255)

# mismas banderas que Controller.sim_flags() del algoritmo
BANDERAS = ["--time-to-teleport", "-1",
            "--tripinfo-output.write-unfinished", "true",
            "--tripinfo-output.write-undeparted", "true",
            "--seed", "23", "--no-step-log", "true", "--no-warnings", "true"]

AJUSTES_GUI = """<viewsettings>
    <scheme name="tesis">
        <vehicles vehicleMode="0" vehicleQuality="2" vehicle_minSize="1" vehicle_exaggeration="3.5"/>
    </scheme>
    <delay value="0"/>
</viewsettings>
"""


def planes():
    m = datos.meta()
    return {"netconvert": m["escenario"]["network"], "algoritmo": m["resultado"]["red_de_la_mejor"]}


def encuadre(red):
    """rectangulo de la camara: el corredor con sus calles vecinas, en la proporcion del panel"""
    net = sumolib.net.readNet(str(RAIZ / red))
    puntos = [p for e in net.getEdges() if e.getID().lstrip("-").split("#")[0] == VIA for p in e.getShape()]
    xs, ys = [p[0] for p in puntos], [p[1] for p in puntos]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    w = max(xs) - min(xs) + 50
    h = w * ALTO / ANCHO
    return cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2


def J_tripinfo(ruta):
    """J con la misma regla del controlador: quien no llega cuenta el tope completo"""
    d, w, sin = [], [], 0
    for t in ET.parse(ruta).getroot().iter("tripinfo"):
        if float(t.get("arrival", 0)) < 0:
            sin += 1
            d.append(MAX_PASOS)
            w.append(MAX_PASOS)
        else:
            d.append(float(t.get("duration")))
            w.append(float(t.get("waitingTime")))
    m = datos.meta()["fitness"]
    return round(m["w1"] * sum(d) / len(d) + m["w2"] * sum(w) / len(w), 2), len(d), sin


def grabar(plan, red):
    cuadros_dir = SALIDA / f"sumo_{plan}"
    shutil.rmtree(cuadros_dir, ignore_errors=True)
    cuadros_dir.mkdir(parents=True)
    ajustes = SALIDA / "sumo_ajustes.xml"
    ajustes.write_text(AJUSTES_GUI, encoding="utf-8")
    tripinfo = SALIDA / f"sumo_{plan}.tripinfo.xml"

    cmd = [SUMO_GUI, "-n", str(RAIZ / red), "-r", str(RAIZ / datos.meta()["escenario"]["routes"]),
           "--tripinfo-output", str(tripinfo), "--end", str(MAX_PASOS), "-g", str(ajustes),
           "--start", "--quit-on-end", "--window-size", "1500,1100", "--window-pos", "40,40"] + BANDERAS
    traci.start(cmd, port=8817, label=plan)
    vista = traci.gui.DEFAULT_VIEW
    traci.gui.setSchema(vista, "tesis")
    traci.gui.setBoundary(vista, *encuadre(red))

    cuadros, color = [], {}
    llegados, espera_acum, paso = 0, 0.0, 0
    while traci.simulation.getMinExpectedNumber() > 0 and paso < MAX_PASOS:
        en_clip = paso <= T_FIN_CLIP and paso % CADA == 0
        if en_clip:
            # colores segun el estado actual y captura al cerrar el siguiente paso
            for vid, r in traci.vehicle.getAllSubscriptionResults().items():
                nuevo = ROJO if r[tc.VAR_SPEED] <= UMBRAL_ESPERA else AZUL
                if color.get(vid) != nuevo:
                    traci.vehicle.setColor(vid, nuevo)
                    color[vid] = nuevo
            traci.gui.screenshot(vista, str(cuadros_dir / f"f_{len(cuadros):05d}.png"), ANCHO, ALTO)
        traci.simulationStep()
        paso += 1
        for vid in traci.simulation.getDepartedIDList():
            traci.vehicle.subscribe(vid, [tc.VAR_SPEED])
        llegados += traci.simulation.getArrivedNumber()
        velocidades = [r[tc.VAR_SPEED] for r in traci.vehicle.getAllSubscriptionResults().values()]
        detenidos = sum(v <= UMBRAL_ESPERA for v in velocidades)
        espera_acum += detenidos  # vehiculos-segundo detenidos en este paso de 1 s
        if en_clip:
            cuadros.append({"t": paso, "en_red": len(velocidades), "detenidos": detenidos,
                            "llegados": llegados, "espera_h": round(espera_acum / 3600, 2)})
    traci.close()

    J, vehiculos, sin = J_tripinfo(tripinfo)
    clip = SALIDA / f"sumo_{plan}.mp4"
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-framerate", str(FPS),
                    "-i", str(cuadros_dir / "f_%05d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "18", str(clip)], check=True)
    info = {"plan": plan, "red": red, "fps": FPS, "cada_s": CADA, "t_fin_clip": T_FIN_CLIP,
            "duracion_clip_s": round(len(cuadros) / FPS, 2), "ancho": ANCHO, "alto": ALTO,
            "fin_simulacion_s": paso, "J": J, "vehiculos": vehiculos, "sin_terminar": sin,
            "espera_total_h": round(espera_acum / 3600, 1), "cuadros": cuadros}
    (SALIDA / f"sumo_{plan}.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{plan}: {len(cuadros)} cuadros, simulacion hasta {paso} s, J = {J}, sin terminar = {sin}")
    return info


if __name__ == "__main__":
    elegidos = sys.argv[1:] or list(planes())
    for plan in elegidos:
        grabar(plan, planes()[plan])
