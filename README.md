# upmega

SGA prototype traffic lights project

### Links

This is a list of documentation used along the learning process and investigation.

- https://github.com/eclipse-sumo/sumo/tree/main/tests/complex/tutorial/hello/data
- https://sumo.dlr.de/docs/Tutorials/Hello_SUMO.html
-
- https://sumo.dlr.de/docs/TraCI.html#introduction_to_traci
- https://sumo.dlr.de/docs/Networks/Import/OpenStreetMap.html
-
-
-

### comandos para generar los poligonos:

- `netconvert --osm-files map.osm -o test.net.xml -t osmNetconvert.typ.xml --xml-validation never`
- `polyconvert --net-file test.net.xml --osm-files map.osm --type-file typemap.xml -o map.poly.xml --xml-validation never`

### para generar el archivo py

- `python randomTrips.py -n test.net.xml -r map.rou.xml -e 1000 -l --validate`
