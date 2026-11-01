# Video explicativo del AGS

Video hecho con [ManimGL](https://github.com/3b1b/manim) que explica el algoritmo genético simple de la
tesis: la arquitectura (AGS, controlador y SUMO), el cromosoma y su decodificación, el ciclo del
algoritmo, la evaluación con las métricas de SUMO y la función J, cada operador (selección, cruce,
mutación y elitismo), la convergencia y cómo se obtienen los resultados.

Las cifras no están escritas a mano: `datos.py` las lee de los archivos de la corrida
`g150p30m12touuniP2c2600s42` (meta.json, analisis.json, evaluations.csv, detail/, logics/ y robustez/)
y usa la misma función de reparto del controlador, así que el video dice lo mismo que la tesis.

## Instalación (una sola vez)

Desde esta carpeta:

```
python -m venv .venv
.venv\Scripts\python -m pip install manimgl imageio-ffmpeg traci "setuptools<81" audioop-lts
```

- `imageio-ffmpeg` trae un FFmpeg propio, de modo que no hace falta instalarlo en el sistema.
  `custom_config.yml` apunta a ese binario; si se reinstala el entorno, hay que actualizar esa ruta
  (`python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"`).
- `setuptools<81` y `audioop-lts` son necesarios con Python 3.13.

## Grabación de SUMO (escena Simulacion)

La escena Simulacion muestra dos grabaciones reales de SUMO-GUI, lado a lado: la red con el plan de
netconvert y con la mejor solución del algoritmo, enfocadas en el corredor que más mejora. Se graban
una vez con:

```
.venv\Scripts\python grabar_sumo.py
```

Abre SUMO-GUI (no hay que minimizar la ventana mientras graba), corre cada simulación con las mismas
opciones que el algoritmo y deja en `salida/` el clip, el tripinfo y los contadores de cada plan. Los
vehículos se pintan de rojo cuando van a 0.1 m/s o menos, que es la definición de espera de SUMO. Las
dos grabaciones reproducen las J de la tesis (878.11 y 428.80). Después, `renderizar.py` inserta los
clips en los paneles de la escena con FFmpeg; la geometría de los paneles está en `disposicion.py`.

## Uso

| Comando | Qué hace |
|---|---|
| `.venv\Scripts\manimgl escenas.py Cruce` | Vista previa de una escena en una ventana |
| `.venv\Scripts\manimgl escenas.py Cruce -w -l` | Escribe la escena en 480p, para revisar rápido |
| `.venv\Scripts\python renderizar.py` | Todas las escenas en 1080p y el video unido `salida/video_ags.mp4` |
| `.venv\Scripts\python renderizar.py --calidad l` | Lo mismo en 480p |
| `.venv\Scripts\python renderizar.py Cruce Mutacion` | Solo esas escenas, sin unir |

Escenas, en orden: Introduccion, Arquitectura, Cromosoma, CicloAG, Simulacion, Evaluacion, Seleccion,
Cruce, Mutacion, Elitismo, Evolucion, Resultados y Cierre. Los videos quedan en `salida/` (ignorada por git).
