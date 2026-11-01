"""
renderiza las escenas de escenas.py y las une en un solo video.

Uso, desde esta carpeta:
    .venv\\Scripts\\python renderizar.py                 todas, en 1080p
    .venv\\Scripts\\python renderizar.py --calidad l     todas, en 480p (revision rapida)
    .venv\\Scripts\\python renderizar.py Cruce Mutacion  solo esas, sin unir
"""

import argparse
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

import disposicion
from disposicion import ESCENAS

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / "salida"
CALIDADES = {"l": "-l", "m": "-m", "hd": "--hd"}


def renderizar(escena, calidad):
    cmd = [str(AQUI / ".venv" / "Scripts" / "manimgl"), "escenas.py", escena, "-w", CALIDADES[calidad]]
    print("renderizando", escena, flush=True)
    subprocess.run(cmd, cwd=AQUI, check=True)
    return SALIDA / f"{escena}.mp4"


def duracion(video):
    salida = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-i", str(video)], capture_output=True, text=True).stderr
    h, m, s = salida.split("Duration:")[1].split(",")[0].strip().split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def componer_simulacion(fondo):
    """inserta los clips de SUMO-GUI (grabar_sumo.py) en los paneles del fondo de la escena"""
    clips = [SALIDA / f"sumo_{p}.mp4" for p in disposicion.SIM_CENTROS]
    faltan = [c.name for c in clips if not c.exists()]
    if faltan:
        sys.exit(f"faltan {faltan}: corre primero grabar_sumo.py")
    alto_fondo = int(subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-i", str(fondo)], capture_output=True,
                                    text=True).stderr.split(" Video: ")[1].split(",")[2].strip().split("x")[1].split()[0])
    ancho_fondo = alto_fondo * 16 // 9
    t0 = disposicion.SIM_INICIO_CLIP
    fin = duracion(fondo) - disposicion.SIM_FUNDIDO
    filtros, previo = [], "[0:v]"
    for k, plan in enumerate(disposicion.SIM_CENTROS, start=1):
        x, y, w, h = disposicion.rect_pixeles(plan, ancho_fondo, alto_fondo)
        # el clip arranca en t0, entra y sale con un fundido, y despues de su ultimo
        # cuadro lo repite hasta el fundido final de la escena
        filtros.append(f"[{k}:v]tpad=stop_mode=clone:stop_duration=120,scale={w}:{h},"
                       f"setpts=PTS-STARTPTS+{t0}/TB,fade=t=in:st={t0}:d=0.5,"
                       f"fade=t=out:st={fin:.2f}:d={disposicion.SIM_FUNDIDO}[c{k}]")
        salida_f = f"[v{k}]" if k < len(clips) else "[v]"
        filtros.append(f"{previo}[c{k}]overlay=x={x}:y={y}:eof_action=pass{salida_f}")
        previo = salida_f
    destino = SALIDA / "Simulacion_compuesta.mp4"
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(fondo)]
    for c in clips:
        cmd += ["-i", str(c)]
    cmd += ["-filter_complex", ";".join(filtros), "-map", "[v]", "-t", f"{duracion(fondo):.2f}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-r", "30", str(destino)]
    subprocess.run(cmd, check=True)
    print("compuesta:", destino)
    return destino


# escenas cuyo video final se arma componiendo otros videos sobre el que renderiza manim
COMPOSICIONES = {"Simulacion": componer_simulacion}


def unir(videos, destino):
    lista = SALIDA / "lista.txt"
    lista.write_text("".join(f"file '{v.name}'\n" for v in videos), encoding="utf-8")
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "concat",
                    "-safe", "0", "-i", str(lista), "-c", "copy", str(destino)], cwd=SALIDA, check=True)
    print("video unido:", destino)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Renderiza el video del AGS")
    parser.add_argument("escenas", nargs="*", help="escenas a renderizar (por defecto, todas)")
    parser.add_argument("--calidad", choices=CALIDADES, default="hd")
    args = parser.parse_args()

    elegidas = args.escenas or ESCENAS
    desconocidas = [e for e in elegidas if e not in ESCENAS]
    if desconocidas:
        sys.exit(f"escenas desconocidas: {desconocidas}; disponibles: {ESCENAS}")

    videos = []
    for e in elegidas:
        video = renderizar(e, args.calidad)
        videos.append(COMPOSICIONES[e](video) if e in COMPOSICIONES else video)
    if not args.escenas:
        unir(videos, SALIDA / "video_ags.mp4")
