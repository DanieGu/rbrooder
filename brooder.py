import time               # Import time library
import datetime
import sys
import Adafruit_DHT
import math
import numpy
import pigpio
from enum import Enum
from collections import deque
import PID
import json
from brooderWeb.RedisQueue import RedisQueue
from MyDimmer import MyDimmer
import math

def readInput(initial):
	global targetTemp,minHeatIndex,maxHeatIndex,manualControl,manualHeatIndex,heatIndex,pidConf,pid
	
	try:
		config = json.load(open(configFileName))
		targetTempX = config['targetTemp']
		manualControl = config['manualControl']
		manualHeatIndex = config['manualHeatIndex']
		#only on initial load
		pidConfX = config['pid']
		if initial or pidConf != pidConfX or (not manualControl and pid == None):
			pidConf = pidConfX
			if not manualControl:
				initPid()
		
		if manualControl and pid:
			pid = None
		
		if targetTemp != targetTempX:
			print("Updating target temp to {0}".format(targetTempX))
			targetTemp = targetTempX
					
	except Exception as e:
		print("Error reading config file: {0}".format(str(e)))
		
	
	return

def initPid():
	global pid
	# {"P":0.2, "I":0.0, "D":0.0, "limitI":20.0, "responseTime":0.0, "minOutput":0, "maxOutput":100}
	print("initialize pid with {0}".format(str(pidConf)))
	pid = PID.PID(pidConf["P"], pidConf["I"], pidConf["D"])
	pid.setSampleTime(pidConf["responseTime"]) #integral time?
	pid.setWindup(pidConf["limitI"])
	pid.setRange(pidConf["minOutput"], pidConf["maxOutput"])
	pid.SetPoint=targetTemp
	pid.debug(True)
	q.clear()
	
def writeOutput():
	outputData['lastUpdateTime'] = lastUpdateTime
	outputData['currentTemp'] = currentTemp
	outputData['currentHumidity'] = currentHumidity
	outputData['message'] = message
	outputData['targetTemp'] = targetTemp
	outputData['brightness'] = heatIndex
	
	#depreciated
	#with open('currentBrooderStatus.txt', 'w') as outfile:
	#	json.dump(outputData, outfile)
	
	q.put(json.dumps(outputData))
	
	return

def millis():
	return int(round(time.time() * 1000))

# function which eliminates the noise
# by using a statistical model
# we determine the standard normal deviation and we exclude anything that goes beyond a threshold
# think of a probability distribution plot - we remove the extremes
# the greater the std_factor, the more "forgiving" is the algorithm with the extreme values
def eliminateNoise(values, std_factor = 2):
	mean = numpy.mean(values)
	standard_deviation = numpy.std(values)

	if standard_deviation == 0:
		return [element for element in values]

	if len(values) < 3:
		return [element for element in values]
		
	final_values = [element for element in values if element > mean - std_factor * standard_deviation]
	final_values = [element for element in final_values if element < mean + std_factor * standard_deviation]

	return final_values

	
def readSensor():
	return Adafruit_DHT.read_retry(22, 17)
	#return Adafruit_DHT.read_retry(11, 4)
	
def readEnvironment():
	global curTempIndex,curHumidIndex,currentTemp,currentHumidity,velocity,sensorError,prevTempMillis,lastUpdateTime
	
	if (currentMillis - prevTempMillis) < tempPolling:
		return

	prevTempMillis = currentMillis
	
	try:
		curHumid, curTemp = readSensor()
		sensorError = curHumid is None or curTemp is None or curTemp <= 0 or curHumid <= 0 or math.isnan(curTemp) or math.isnan(curHumid)
	except Exception as e:
		print(str(e))
		sensorError = True
		
	if sensorError:
		print("Environment sensor error!")
		return
	
	tempReadings.appendleft(curTemp)
	
	#filter bad values
	#take the most recent 3 valid readings and average them
	currentTemp = round(numpy.mean(eliminateNoise(tempReadings)[0:3]), 1)
	
	humidReadings.appendleft(curHumid)
	#get the total
	total = 0.0
	for t in humidReadings:
		total += t

	currentHumidity = total / maxHumidReadings
	currentHumidity = round(currentHumidity, 1)

	lastUpdateTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	
	return;

def adjustHeater(pct):
	dimmer.set(pct)
	#pwm.ChangeDutyCycle(pct)
	return;
	
def checkHeater():
	global heatIndex, prevHeaterMillis
	
	if (currentMillis - prevHeaterMillis) < heaterPolling:
		return

	prevHeaterMillis = currentMillis;
	
	if manualControl:
		heatIndexX = manualHeatIndex
	else:
		if targetTemp != pid.SetPoint:
			pid.SetPoint = targetTemp
			
		pid.update(currentTemp)
		heatIndexX = pid.output
		#shouldn't need this as the PID controller has a limit
		#heatIndexX = max(min(heatIndexX, 80), 20)
		heatIndexX = round(heatIndexX)
	
	if heatIndexX != heatIndex:
		heatIndex = heatIndexX
		print("Adjusting to {0}".format(heatIndex))
		adjustHeater(heatIndex)
	
	return;
	
def updateDisplay():
	global prevDisplayMillis
	
	if (currentMillis - prevDisplayMillis) < displayPolling:
		return

	prevDisplayMillis = currentMillis;
	
	print( 'Temp: {0:0.1f} C  Humidity: {1:0.1f} %'.format(currentTemp, currentHumidity))
	
	writeOutput()
	
	#could be done elsewhere I suppose
	readInput(False)
	
	return

def checkAlarm():
	global prevAlarmMillis,message
	if (currentMillis - prevAlarmMillis) < alarmPolling:
		return

	prevAlarmMillis = currentMillis

	shouldAlarm = sensorError

	if sensorError:
		message = "ALARM Sensor Error!"
	else:
		message = ""
	
	return
	
def runProgram():	
	global currentMillis
	
	# main loop of program
	print("\nPress Ctl C to quit \n")  # Print blank line before and after message.
	while True: 
		currentMillis = millis()	
		readEnvironment()
		checkHeater()
		checkAlarm()
		updateDisplay()
		time.sleep(0.5)#maximum resolution of half second

dimmerPin = 18
		
pi = pigpio.pi()
dimmer = MyDimmer(pi, dimmerPin, frequency=200)

currentTemp = 0.0 
currentHumidity = 0.0
currentHumidity, currentTemp = readSensor()

maxTempReadings = 10
tempReadings = deque([], maxTempReadings)

maxHumidReadings = 10
humidReadings = deque(maxHumidReadings*[currentHumidity], maxHumidReadings)

targetTemp = 0
heatIndex = 0
sensorError = False
manualControl = False
manualHeatIndex = 0

tempPolling = 3 * 1000
alarmPolling = 2 * 1000
heaterPolling = 30 * 1000
displayPolling = 10 * 1000

currentMillis = 0 
prevTempMillis = 0
prevAlarmMillis = 0
prevHeaterMillis = 0
prevDisplayMillis = 0

configFileName = 'brooderConfig.txt'
lastUpdateTime = ''
message = ''
outputData = {'currentTemp':currentTemp, 'currentHumidity':currentHumidity, 'lastUpdateTime':lastUpdateTime, 'message':message, 'targetTemp':targetTemp, 'brightness':heatIndex}
pidConf = {"P":0.2, "I":0.0, "D":0.0, "limitI":20.0, "responseTime":0.0, "minOutput":0.0, "maxOutput":100.0}

q = RedisQueue('brooder')
q.max(360)
q.clear()

pid = None

readInput(True)

try:
	runProgram()
except KeyboardInterrupt:
	print('cleaning up...')
	
	dimmer.close()
	sys.exit()
 
