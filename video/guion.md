# Guion de narración del video del AGS

Video actual: 7:02.9. Narración estimada: 9:26.3 a 2.5 palabras por segundo. Si el video se alarga donde la voz no alcanza, quedaría de unos 9:48.1.

Cada bloque empieza cuando aparece en pantalla lo que narra. La columna de tiempo indica dónde está ese momento en el video unido actual; el aviso indica cuántos segundos le faltan al video para que quepa la voz. Conviene grabar cada bloque en un archivo propio con su número (01.wav, 02.wav...), para poder alargar cada escena a la medida de la grabación.

## Introduccion

**01** · 0:00.0 · Título · faltan unos 4 s

> En este video explico el algoritmo genético simple que desarrollé para programar los semáforos de la zona 1 de la ciudad de Guatemala.

**02** · 0:05.0 · Las tres tarjetas · faltan unos 12 s

> La red tiene 110 intersecciones con semáforo y la recorren 2002 vehículos con rutas fijas. Se parte de la programación que asigna netconvert: un ciclo de 90 segundos en todas y sin desfases.

**03** · 0:09.0 · La pregunta en amarillo · faltan unos 1 s

> La pregunta es qué programación semafórica reduce los tiempos de viaje y de espera de esos vehículos.

**04** · 0:14.5 · El índice · faltan unos 1 s

> Veremos la arquitectura, el cromosoma, el ciclo del algoritmo, cómo se mide cada solución, los operadores y los resultados.

## Arquitectura

**05** · 0:21.3 · Las tres cajas · faltan unos 2 s

> El programa tiene tres partes: el algoritmo genético, implementado con PyGAD; un controlador; y SUMO, el simulador de tránsito.

**06** · 0:26.8 · Flechas de TraCI · faltan unos 4 s

> Al arrancar, el controlador se conecta a SUMO por TraCI una sola vez, para leer cómo está armado cada uno de los 110 semáforos: sus fases, sus ámbares y sus verdes mínimos.

**07** · 0:36.3 · Paso 1: evalúa este genoma · faltan unos 5 s

> Cada evaluación sigue seis pasos. Primero, el algoritmo le pide al controlador que evalúe un genoma de 440 genes; no sabe nada del simulador.

**08** · 0:42.1 · Paso 2: archivo de red · faltan unos 3 s

> El controlador traduce ese genoma en un plan para cada uno de los 110 semáforos y lo escribe en un archivo de red.

**09** · 0:49.2 · Paso 3: ejecuta SUMO · faltan unos 3 s

> Luego ejecuta SUMO como un proceso aparte, sin teletransportes y con la semilla fija, hasta que todos los vehículos llegan o se alcanzan 10 000 segundos.

**10** · 0:57.9 · Paso 4: tripinfo.xml · faltan unos 3 s

> Al terminar, SUMO escribe el archivo tripinfo, con un registro por vehículo: 2002 registros con su tiempo de viaje y su tiempo de espera.

**11** · 1:06.0 · Paso 5: tiempos de vuelta al AGS · cabe

> El controlador lee ese archivo y le devuelve al algoritmo los tiempos de cada vehículo.

**12** · 1:12.5 · Paso 6: J y F · faltan unos 1 s

> Con esos tiempos, el algoritmo calcula J y la aptitud F. Esto se repite para cada individuo de cada generación.

**13** · 1:19.9 · Las dos frases finales · faltan unos 4 s

> Así, el controlador orquesta las dos partes sin que una dependa de la otra. Y como cada evaluación es independiente, las de una generación corren en seis procesos de SUMO a la vez.

## Cromosoma

**14** · 1:29.2 · La barra de 440 genes · faltan unos 5 s

> Cada individuo es un cromosoma de 440 genes en tres tramos: 110 ciclos, 220 pesos de reparto y 110 desfases.

**15** · 1:35.2 · Nota de los ámbares · faltan unos 2 s

> Los ámbares no son genes: se copian de la red, porque dependen de la velocidad y no del tránsito.

**16** · 1:41.2 · Genes de una intersección · faltan unos 6 s

> Tomemos una intersección de cuatro fases: ciclo de 45 segundos, pesos 30 y 12, y desfase del 25 por ciento.

**17** · 1:45.2 · Pasos 1 a 4 · faltan unos 11 s

> De los 45 segundos, 12 son de ámbar y cada verde tiene un mínimo de 7. Los 19 que sobran se reparten en proporción 30 a 12, y con restos mayores los verdes quedan en 21 y 12 segundos: suman exactamente 45.

**18** · 1:55.6 · Aparece el plan · cabe

> Ese es el plan de la intersección: verde, ámbar, verde, ámbar.

**19** · 2:02.6 · El reloj y el desfase · faltan unos 3 s

> El desfase del 25 por ciento son 11 segundos: el ciclo arranca 11 segundos después del reloj común. No cambia ninguna duración, y es lo que permite coordinar intersecciones vecinas.

**20** · 2:13.1 · Intersección real · faltan unos 2 s

> En esta intersección real, netconvert asigna 90 segundos sin desfase; la mejor solución, 51 segundos con un desfase de 47.

## CicloAG

**21** · 2:20.9 · Las seis etapas y lo que pasa entre ellas · faltan unos 4 s

> El algoritmo repite seis etapas: la población de 30 se evalúa, la selección elige 12 padres, el cruce produce 29 hijos, la mutación los modifica y el elitismo completa otra vez 30.

**22** · 2:31.5 · Nota de la generación 0 · faltan unos 3 s

> En la generación cero, el primer individuo es la configuración de netconvert y los otros 29 son aleatorios.

**23** · 2:36.5 · Contador de generaciones · cabe

> Ese ciclo se repite durante 150 generaciones, con 4380 evaluaciones en total: 30 al inicio y 29 en cada generación.

## Evaluacion

**24** · 2:50.8 · Registro tripinfo · faltan unos 1 s

> Veamos cómo se mide una solución, con un registro real del archivo tripinfo.

**25** · 2:55.3 · Las tres definiciones · faltan unos 5 s

> duration es el tiempo de viaje; waitingTime, el tiempo de espera, a 0.1 metros por segundo o menos; y timeLoss, el tiempo perdido, que sirve para verificar pero no entra en J.

**26** · 3:03.7 · Barra del vehículo 0 · faltan unos 1 s

> Este vehículo tarda 49 segundos: 37 en movimiento y 12 detenido.

**27** · 3:08.7 · Promedios y penalización · faltan unos 9 s

> Para toda la red se promedian los 2002 vehículos. Al que no llega antes de 10 000 segundos se le cuentan 10 000, así que trabar la red se castiga con fuerza.

**28** · 3:16.7 · Fórmula de J y de F · faltan unos 3 s

> J suma el viaje medio y 1.1 veces la espera media. PyGAD maximiza su inverso, la aptitud F, pero reportamos J en segundos: menos es mejor.

**29** · 3:24.2 · Las dos cuentas · faltan unos 1 s

> Con la configuración de netconvert, J vale 878.11 segundos. Con la mejor solución, 428.80.

**30** · 3:31.2 · Peso efectivo de 2.1 · faltan unos 2 s

> Como el viaje ya incluye la espera, en realidad la espera pesa 2.1 dentro de J. Es justo la parte de la demora que el semáforo controla.

## Seleccion

**31** · 3:40.5 · Barras de la población · faltan unos 2 s

> Ahora, los operadores. En la selección, cada barra es un individuo y su altura es su aptitud; la más alta es la configuración de netconvert.

**32** · 3:48.5 · Los dos primeros torneos · cabe

> Para elegir un padre se sortean cinco individuos, con reemplazo, y gana el de mayor aptitud. Ese ganador pasa al grupo de padres.

**33** · 3:57.5 · Torneos rápidos · cabe

> Se hacen doce torneos independientes, uno por cada padre.

**34** · 4:11.0 · Nota de los repetidos · cabe

> Un mismo individuo puede ganar varios torneos, así que algunos padres se repiten.

**35** · 4:15.8 · Nota de la escala · faltan unos 1 s

> El torneo solo compara aptitudes; por eso no importa la escala de F.

**36** · 4:19.6 · Nota de la presión selectiva · faltan unos 3 s

> Con torneos de cinco la presión es alta: actuando sola, la selección llenaría la población con el mejor en unas tres generaciones.

## Cruce

**37** · 4:25.7 · Anillo de padres · cabe

> Los doce padres forman un anillo, y cada hijo sale de dos padres consecutivos, hasta completar 29.

**38** · 4:35.2 · Monedas y armado del hijo · faltan unos 1 s

> Para cada gen se lanza una moneda: si sale azul, hereda del padre A; si sale naranja, del padre B.

**39** · 4:42.2 · Notas del cruce · cabe

> Como cada gen se hereda por separado, el orden de los genes en el cromosoma no influye. Y todos los descendientes pasan por el cruce.

## Mutacion

**40** · 4:54.8 · Sorteos por gen · faltan unos 2 s

> En la mutación, cada gen sortea un número entre cero y uno; si sale menor que 0.02, se reemplaza por un valor al azar dentro de su rango.

**41** · 5:04.4 · Ejemplo del gen de ciclo · faltan unos 2 s

> Aquí, el gen de ciclo pasa de 45 a 83 segundos.

**42** · 5:08.4 · Notas de la mutación · cabe

> Así cambian, en promedio, unos nueve de los 440 genes de cada hijo. Como cada mutación es un salto grande, la probabilidad se mantiene baja, como recomienda la literatura.

## Elitismo

**43** · 5:20.7 · La élite y los hijos forman la nueva generación · cabe

> Por último, el elitismo. El mejor individuo de la generación pasa intacto a la siguiente, junto con los 29 hijos mutados.

**44** · 5:29.9 · Notas del elitismo · faltan unos 1 s

> Así, la mejor aptitud nunca empeora. Pero eso no garantiza el óptimo global en 150 generaciones: esa garantía es asintótica.

**45** · 5:37.5 · Vuelta a la evaluación · faltan unos 1 s

> La nueva población de 30 vuelve a la evaluación, y el ciclo empieza otra vez.

## Evolucion

**46** · 5:43.1 · Se dibuja la curva · cabe

> Esta es la evolución real de la búsqueda: la J del mejor individuo en cada generación.

**47** · 5:50.1 · Las tres marcas · faltan unos 8 s

> Empieza en 878.1 segundos, la configuración de netconvert; en la generación 50 está en 473.8, y la mejor aparece en la 126, con 428.8.

**48** · 5:56.7 · Nota del 90% · faltan unos 1 s

> El 90 por ciento de la mejora llega en las primeras 50 generaciones.

**49** · 6:01.7 · Nota de las evaluaciones trabadas · faltan unos 3 s

> Al inicio, 18 de los 29 individuos aleatorios traban la red; después, entre el 3 y el 7 por ciento.

## Resultados

**50** · 6:08.0 · Cómo se obtienen · faltan unos 4 s

> Para obtener los resultados, al terminar se vuelven a simular la configuración de netconvert y la mejor solución, pidiendo a SUMO todas sus salidas.

**51** · 6:14.0 · Barras de las cuatro métricas · faltan unos 2 s

> El viaje medio baja 42.53 por ciento; la espera media, 62.34; el tiempo perdido, 49.59; y J, 51.17.

**52** · 6:23.6 · Robustez: medianas · faltan unos 11 s

> Pero esa es la demanda con la que se optimizó. Con 35 combinaciones de demanda y de semilla, la mediana de J es 911.4 con netconvert, 555.5 con el algoritmo y 715 con el ciclo uniforme.

**53** · 6:30.3 · El algoritmo gana en las 35 · faltan unos 6 s

> El algoritmo gana en las 35 combinaciones, con una mediana de las reducciones de 40.3 por ciento, y nunca traba la red.

**54** · 6:34.8 · Ajuste a la realización · faltan unos 4 s

> Como 428.8 es el mejor de los 35 casos, parte del 51 por ciento es un ajuste a ese escenario.

## Cierre

**55** · 6:41.1 · Primeros dos puntos · faltan unos 2 s

> En resumen: el controlador separa al algoritmo del simulador y orquesta cada evaluación, y cada individuo es un plan completo para los 110 semáforos.

**56** · 6:49.3 · Puntos tres y cuatro · faltan unos 3 s

> Selección, cruce, mutación y elitismo transforman la población generación tras generación, y J resume el viaje y la espera de los 2002 vehículos.

**57** · 6:56.5 · Último punto · faltan unos 5 s

> La mejor solución reduce J en 51 por ciento y, con otros escenarios, mantiene una mediana de 40.3 sin trabar la red. Gracias por su atención.
