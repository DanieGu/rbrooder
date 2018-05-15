# rbrooder
Rasberry PI Brooder control

## Architecture
Comes in two parts
brooder.py is a python script that reads the temperature from the DHT22 and attempts to adjust the heater accordingly.

brooderWeb is a virtual env that runs a flask web server.  The webserver reads data from a redis queue and displays it.

## requirements
Redis
Adafruit DHT library

