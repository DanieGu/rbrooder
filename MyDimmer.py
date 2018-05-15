import pigpio

#https://raspberrypi.stackexchange.com/questions/40243/pigpio-set-pwm-dutycycle-vs-hardware-pwm
class MyDimmer(object):
	def __init__(self, pi, gpio, hardwarePWM = True, frequency = 200):
		self.__gpio = gpio
		self.__io = pi
		self.__hardware = hardwarePWM
		self.__frequency = frequency
		if not hardwarePWM:
			self.__io.set_PWM_frequency(self.__gpio, frequency)
			self.__io.set_PWM_range(self.__gpio, 100)
	
	def set(self, percent):
		if self.__hardware:
			self.__io.hardware_PWM(self.__gpio, self.__frequency, 1000000 * (percent / 100.0))
		else:
			self.__io.set_PWM_dutycycle(self.__gpio, percent)
	
	def close(self):
		self.__io.stop()