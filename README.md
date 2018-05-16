# rbrooder
Rasberry PI Brooder control

## Architecture
Comes in two parts
brooder.py is a python script that reads the temperature from the DHT22 and attempts to adjust the heater accordingly.

brooderWeb is a virtual env that runs a flask web server.  The webserver reads data from a redis queue and displays it.

## requirements
Redis
Adafruit DHT library

## Dimmer
I created a dimmer making some minor modifications to this design. http://www.instructables.com/id/AC-PWM-Dimmer-for-Arduino/  The major modifications made are to make sure that
the dimmer is off when no PWM input is present.

## Connections
Pin 12 (GPIO 18) is the edge pin of the dimmer.  GPIO 18 is used because it can generate a hardware PWM signal.
Pin 14 (or any other ground) can connect to the other pin of the dimmer.
AC 120 is connected to bridge rectifier side of the dimmer and the bulb load to the other.

DHT22
Pin 9 (or other ground) is connected to ground
Pin 11 (GPIO 17) is connected to data
Pin 1(or other 3.3V) is connected to +
10K (br bk or) bridges data and +

