"""
guion de narracion del video, en bloques atados a los tiempos de cada escena.

Cada bloque tiene la escena, el segundo de la escena en que empieza (el momento
en que aparece en pantalla lo que narra) y el texto. Al correr este archivo se
genera guion.md con la duracion estimada de cada bloque y el tiempo que hoy le
da el video, para saber donde hay que alargar la escena.

Los mismos identificadores sirven para sincronizar: si cada bloque se graba en
un archivo propio (audio/01.wav, audio/02.wav, ...), se puede medir cuanto dura
y alargar la escena donde la voz no alcanza.

Uso:
    .venv\\Scripts\\python guion.py
"""

import re
from pathlib import Path

PALABRAS_POR_SEGUNDO = 2.5

# duracion de cada escena en el video actual (s)
DURACION = {"Introduccion": 21.3, "Arquitectura": 67.9, "Cromosoma": 51.7, "CicloAG": 29.9,
            "Evaluacion": 49.7, "Seleccion": 45.2, "Cruce": 29.1, "Mutacion": 25.9,
            "Elitismo": 22.4, "Evolucion": 24.9, "Resultados": 33.1, "Cierre": 21.8}

# (escena, segundo de inicio dentro de la escena, lo que aparece en pantalla, narracion)
BLOQUES = [
    ("Introduccion", 0.0, "Título",
     "En este video explico el algoritmo genético simple que desarrollé para programar los semáforos "
     "de la zona 1 de la ciudad de Guatemala."),
    ("Introduccion", 5.0, "Las tres tarjetas",
     "La red tiene 110 intersecciones con semáforo y la recorren 2002 vehículos con rutas fijas. Se "
     "parte de la programación que asigna netconvert: un ciclo de 90 segundos en todas y sin "
     "desfases."),
    ("Introduccion", 9.0, "La pregunta en amarillo",
     "La pregunta es qué programación semafórica reduce los tiempos de viaje y de espera de esos vehículos."),
    ("Introduccion", 14.5, "El índice",
     "Veremos la arquitectura, el cromosoma, el ciclo del algoritmo, cómo se mide cada solución, los "
     "operadores y los resultados."),

    ("Arquitectura", 0.0, "Las tres cajas",
     "El programa tiene tres partes: el algoritmo genético, implementado con PyGAD; un controlador; y "
     "SUMO, el simulador de tránsito."),
    ("Arquitectura", 5.5, "Flechas de TraCI",
     "Al arrancar, el controlador se conecta a SUMO por TraCI una sola vez, para leer cómo está armado "
     "cada uno de los 110 semáforos: sus fases, sus ámbares y sus verdes mínimos."),
    ("Arquitectura", 15.0, "Paso 1: evalúa este genoma",
     "Cada evaluación sigue seis pasos. Primero, el algoritmo le pide al controlador que evalúe un "
     "genoma de 440 genes; no sabe nada del simulador."),
    ("Arquitectura", 20.8, "Paso 2: archivo de red",
     "El controlador traduce ese genoma en un plan para cada uno de los 110 semáforos y lo escribe en "
     "un archivo de red."),
    ("Arquitectura", 27.9, "Paso 3: ejecuta SUMO",
     "Luego ejecuta SUMO como un proceso aparte, sin teletransportes y con la semilla fija, hasta que "
     "todos los vehículos llegan o se alcanzan 10 000 segundos."),
    ("Arquitectura", 36.6, "Paso 4: tripinfo.xml",
     "Al terminar, SUMO escribe el archivo tripinfo, con un registro por vehículo: 2002 registros con su "
     "tiempo de viaje y su tiempo de espera."),
    ("Arquitectura", 44.7, "Paso 5: tiempos de vuelta al AGS",
     "El controlador lee ese archivo y le devuelve al algoritmo los tiempos de cada vehículo."),
    ("Arquitectura", 51.2, "Paso 6: J y F",
     "Con esos tiempos, el algoritmo calcula J y la aptitud F. Esto se repite para cada individuo de cada "
     "generación."),
    ("Arquitectura", 58.6, "Las dos frases finales",
     "Así, el controlador orquesta las dos partes sin que una dependa de la otra. Y como cada "
     "evaluación es independiente, las de una generación corren en seis procesos de SUMO a la vez."),

    ("Cromosoma", 0.0, "La barra de 440 genes",
     "Cada individuo es un cromosoma de 440 genes en tres tramos: 110 ciclos, 220 pesos de reparto y "
     "110 desfases."),
    ("Cromosoma", 6.0, "Nota de los ámbares",
     "Los ámbares no son genes: se copian de la red, porque dependen de la velocidad y no del "
     "tránsito."),
    ("Cromosoma", 12.0, "Genes de una intersección",
     "Tomemos una intersección de cuatro fases: ciclo de 45 segundos, pesos 30 y 12, y desfase del 25 "
     "por ciento."),
    ("Cromosoma", 16.0, "Pasos 1 a 4",
     "De los 45 segundos, 12 son de ámbar y cada verde tiene un mínimo de 7. Los 19 que sobran se "
     "reparten en proporción 30 a 12, y con restos mayores los verdes quedan en 21 y 12 segundos: "
     "suman exactamente 45."),
    ("Cromosoma", 26.4, "Aparece el plan",
     "Ese es el plan de la intersección: verde, ámbar, verde, ámbar."),
    ("Cromosoma", 33.4, "El reloj y el desfase",
     "El desfase del 25 por ciento son 11 segundos: el ciclo arranca 11 segundos después del reloj "
     "común. No cambia ninguna duración, y es lo que permite coordinar intersecciones vecinas."),
    ("Cromosoma", 43.9, "Intersección real",
     "En esta intersección real, netconvert asigna 90 segundos sin desfase; la mejor solución, 51 "
     "segundos con un desfase de 47."),

    ("CicloAG", 0.0, "Las seis etapas y lo que pasa entre ellas",
     "El algoritmo repite seis etapas: la población de 30 se evalúa, la selección elige 12 padres, el "
     "cruce produce 29 hijos, la mutación los modifica y el elitismo completa otra vez 30."),
    ("CicloAG", 10.6, "Nota de la generación 0",
     "En la generación cero, el primer individuo es la configuración de netconvert y los otros 29 son "
     "aleatorios."),
    ("CicloAG", 15.6, "Contador de generaciones",
     "Ese ciclo se repite durante 150 generaciones, con 4380 evaluaciones en total: 30 al inicio y 29 en "
     "cada generación."),

    ("Evaluacion", 0.0, "Registro tripinfo",
     "Veamos cómo se mide una solución, con un registro real del archivo tripinfo."),
    ("Evaluacion", 4.5, "Las tres definiciones",
     "duration es el tiempo de viaje; waitingTime, el tiempo de espera, a 0.1 metros por segundo o "
     "menos; y timeLoss, el tiempo perdido, que sirve para verificar pero no entra en J."),
    ("Evaluacion", 12.9, "Barra del vehículo 0",
     "Este vehículo tarda 49 segundos: 37 en movimiento y 12 detenido."),
    ("Evaluacion", 17.9, "Promedios y penalización",
     "Para toda la red se promedian los 2002 vehículos. Al que no llega antes de 10 000 segundos se "
     "le cuentan 10 000, así que trabar la red se castiga con fuerza."),
    ("Evaluacion", 25.9, "Fórmula de J y de F",
     "J suma el viaje medio y 1.1 veces la espera media. PyGAD maximiza su inverso, la aptitud F, "
     "pero reportamos J en segundos: menos es mejor."),
    ("Evaluacion", 33.4, "Las dos cuentas",
     "Con la configuración de netconvert, J vale 878.11 segundos. Con la mejor solución, 428.80."),
    ("Evaluacion", 40.4, "Peso efectivo de 2.1",
     "Como el viaje ya incluye la espera, en realidad la espera pesa 2.1 dentro de J. Es justo la parte "
     "de la demora que el semáforo controla."),

    ("Seleccion", 0.0, "Barras de la población",
     "Ahora, los operadores. En la selección, cada barra es un individuo y su altura es su aptitud; "
     "la más alta es la configuración de netconvert."),
    ("Seleccion", 8.0, "Los dos primeros torneos",
     "Para elegir un padre se sortean cinco individuos, con reemplazo, y gana el de mayor aptitud. Ese "
     "ganador pasa al grupo de padres."),
    ("Seleccion", 17.0, "Torneos rápidos",
     "Se hacen doce torneos independientes, uno por cada padre."),
    ("Seleccion", 30.5, "Nota de los repetidos",
     "Un mismo individuo puede ganar varios torneos, así que algunos padres se repiten."),
    ("Seleccion", 35.3, "Nota de la escala",
     "El torneo solo compara aptitudes; por eso no importa la escala de F."),
    ("Seleccion", 39.1, "Nota de la presión selectiva",
     "Con torneos de cinco la presión es alta: actuando sola, la selección llenaría la población con "
     "el mejor en unas tres generaciones."),

    ("Cruce", 0.0, "Anillo de padres",
     "Los doce padres forman un anillo, y cada hijo sale de dos padres consecutivos, hasta completar "
     "29."),
    ("Cruce", 9.5, "Monedas y armado del hijo",
     "Para cada gen se lanza una moneda: si sale azul, hereda del padre A; si sale naranja, del padre "
     "B."),
    ("Cruce", 16.5, "Notas del cruce",
     "Como cada gen se hereda por separado, el orden de los genes en el cromosoma no influye. Y todos los "
     "descendientes pasan por el cruce."),

    ("Mutacion", 0.0, "Sorteos por gen",
     "En la mutación, cada gen sortea un número entre cero y uno; si sale menor que 0.02, se "
     "reemplaza por un valor al azar dentro de su rango."),
    ("Mutacion", 9.6, "Ejemplo del gen de ciclo",
     "Aquí, el gen de ciclo pasa de 45 a 83 segundos."),
    ("Mutacion", 13.6, "Notas de la mutación",
     "Así cambian, en promedio, unos nueve de los 440 genes de cada hijo. Como cada mutación es un "
     "salto grande, la probabilidad se mantiene baja, como recomienda la literatura."),

    ("Elitismo", 0.0, "La élite y los hijos forman la nueva generación",
     "Por último, el elitismo. El mejor individuo de la generación pasa intacto a la siguiente, junto con "
     "los 29 hijos mutados."),
    ("Elitismo", 9.2, "Notas del elitismo",
     "Así, la mejor aptitud nunca empeora. Pero eso no garantiza el óptimo global en 150 "
     "generaciones: esa garantía es asintótica."),
    ("Elitismo", 16.8, "Vuelta a la evaluación",
     "La nueva población de 30 vuelve a la evaluación, y el ciclo empieza otra vez."),

    ("Evolucion", 0.0, "Se dibuja la curva",
     "Esta es la evolución real de la búsqueda: la J del mejor individuo en cada generación."),
    ("Evolucion", 7.0, "Las tres marcas",
     "Empieza en 878.1 segundos, la configuración de netconvert; en la generación 50 está en 473.8, y "
     "la mejor aparece en la 126, con 428.8."),
    ("Evolucion", 13.6, "Nota del 90%",
     "El 90 por ciento de la mejora llega en las primeras 50 generaciones."),
    ("Evolucion", 18.6, "Nota de las evaluaciones trabadas",
     "Al inicio, 18 de los 29 individuos aleatorios traban la red; después, entre el 3 y el 7 por "
     "ciento."),

    ("Resultados", 0.0, "Cómo se obtienen",
     "Para obtener los resultados, al terminar se vuelven a simular la configuración de netconvert y la "
     "mejor solución, pidiendo a SUMO todas sus salidas."),
    ("Resultados", 6.0, "Barras de las cuatro métricas",
     "El viaje medio baja 42.53 por ciento; la espera media, 62.34; el tiempo perdido, 49.59; y J, "
     "51.17."),
    ("Resultados", 15.6, "Robustez: medianas",
     "Pero esa es la demanda con la que se optimizó. Con 35 combinaciones de demanda y de semilla, la "
     "mediana de J es 911.4 con netconvert, 555.5 con el algoritmo y 715 con el ciclo uniforme."),
    ("Resultados", 22.3, "El algoritmo gana en las 35",
     "El algoritmo gana en las 35 combinaciones, con una mediana de las reducciones de 40.3 por "
     "ciento, y nunca traba la red."),
    ("Resultados", 26.8, "Ajuste a la realización",
     "Como 428.8 es el mejor de los 35 casos, parte del 51 por ciento es un ajuste a ese escenario."),

    ("Cierre", 0.0, "Primeros dos puntos",
     "En resumen: el controlador separa al algoritmo del simulador y orquesta cada evaluación, y cada "
     "individuo es un plan completo para los 110 semáforos."),
    ("Cierre", 8.2, "Puntos tres y cuatro",
     "Selección, cruce, mutación y elitismo transforman la población generación tras generación, y J "
     "resume el viaje y la espera de los 2002 vehículos."),
    ("Cierre", 15.4, "Último punto",
     "La mejor solución reduce J en 51 por ciento y, con otros escenarios, mantiene una mediana de "
     "40.3 sin trabar la red. Gracias por su atención."),
]


def palabras_habladas(texto):
    """palabras que se pronuncian: un numero como 878.11 se dice con varias"""
    total = 0.0
    for tok in texto.split():
        digitos = re.sub(r"\D", "", tok)
        total += 1 + 0.7 * len(digitos) if digitos else 1
    return total


def mmss(s):
    return f"{int(s // 60)}:{s % 60:04.1f}"


def tabla():
    escenas = list(DURACION)
    inicio_escena, acum = {}, 0.0
    for e in escenas:
        inicio_escena[e] = acum
        acum += DURACION[e]
    filas = []
    for i, (esc, t, pantalla, texto) in enumerate(BLOQUES):
        sig = BLOQUES[i + 1] if i + 1 < len(BLOQUES) else None
        fin = sig[1] if sig and sig[0] == esc else DURACION[esc]
        necesita = palabras_habladas(texto) / PALABRAS_POR_SEGUNDO
        filas.append({"id": f"{i + 1:02d}", "escena": esc, "inicio": inicio_escena[esc] + t,
                      "ventana": fin - t, "necesita": necesita, "pantalla": pantalla, "texto": texto})
    return filas, acum


def escribir_md(destino="guion.md"):
    filas, total = tabla()
    voz = sum(f["necesita"] for f in filas)
    faltan = sum(max(0.0, f["necesita"] - f["ventana"]) for f in filas)
    l = ["# Guion de narración del video del AGS", "",
         f"Video actual: {mmss(total)}. Narración estimada: {mmss(voz)} a {PALABRAS_POR_SEGUNDO} palabras "
         f"por segundo. Si el video se alarga donde la voz no alcanza, quedaría de unos "
         f"{mmss(total + faltan)}.", "",
         "Cada bloque empieza cuando aparece en pantalla lo que narra. La columna de tiempo indica dónde "
         "está ese momento en el video unido actual; el aviso indica cuántos segundos le faltan al video "
         "para que quepa la voz. Conviene grabar cada bloque en un archivo propio con su número "
         "(01.wav, 02.wav...), para poder alargar cada escena a la medida de la grabación.", ""]
    escena = None
    for f in filas:
        if f["escena"] != escena:
            escena = f["escena"]
            l += [f"## {escena}", ""]
        holgura = f["ventana"] - f["necesita"]
        aviso = f"faltan unos {-holgura:.0f} s" if holgura < -0.5 else "cabe"
        l += [f"**{f['id']}** · {mmss(f['inicio'])} · {f['pantalla']} · {aviso}", "",
              f"> {f['texto']}", ""]
    Path(destino).write_text("\n".join(l), encoding="utf-8")
    return filas, total, voz, faltan


if __name__ == "__main__":
    filas, total, voz, faltan = escribir_md()
    print(f"video {mmss(total)}, voz {mmss(voz)}, faltan {faltan:.0f} s; bloques {len(filas)}")
    for f in filas:
        if f["necesita"] - f["ventana"] > 0.5:
            print(f"  {f['id']} {f['escena']:12s} ventana {f['ventana']:5.1f} s, voz {f['necesita']:5.1f} s")
