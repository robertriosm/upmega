# upmega

## Prerrequisitos:

- python 3
- eclipse sumo


SGA prototype traffic lights project



### Links

This is a list of documentation used along the learning process and investigation.

- https://github.com/eclipse-sumo/sumo/tree/main/tests/complex/tutorial/hello/data
- https://sumo.dlr.de/docs/Tutorials/Hello_SUMO.html
- https://sumo.dlr.de/docs/TraCI.html#introduction_to_traci
- https://sumo.dlr.de/docs/Networks/Import/OpenStreetMap.html
- https://sumo.dlr.de/docs/Basics/Using_the_Command_Line_Applications.html
- https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.xhtml
- https://sumo.dlr.de/pydoc/traci.connection.html

### comandos para generar los poligonos:

- `netconvert --osm-files map.osm -o test.net.xml -t osmNetconvert.typ.xml --xml-validation never`
- `polyconvert --net-file test.net.xml --osm-files map.osm --type-file typemap.xml -o map.poly.xml --xml-validation never`

### para generar el archivo py

- `python randomTrips.py -n test.net.xml -r map.rou.xml -e 1000 -l --validate`


## generar random trips

[Referencia de generacion de viajes aleatorios](https://www.youtube.com/watch?v=NOPn9sE0AdY)

- traer un map.osm de openstreetmaps
- tener el osmNetconvert.typ.xml
- 