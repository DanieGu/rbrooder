import redis

class RedisQueue(object):
	"""Simple Queue with Redis Backend"""
	def __init__(self, name, namespace='queue', **redis_kwargs):
		"""The default connection parameters are: host='localhost', port=6379, db=0"""
		self.__db= redis.Redis(**redis_kwargs)
		self.key = '%s:%s' %(namespace, name)
		self.__max =  -1

	def qsize(self):
		"""Return the approximate size of the queue."""
		return self.__db.llen(self.key)

	def max(self, max):
		self.__max = max
	
	def empty(self):
		"""Return True if the queue is empty, False otherwise."""
		return self.qsize() == 0

	def clear(self):
		if self.__db.exists(self.key):
			self.__db.delete(self.key)
		
	def put(self, item):
		"""Put item into the queue."""
		self.__db.rpush(self.key, item)
		if self.__max > 0:
			while self.qsize() > self.__max:
				self.get()

	def get(self, block=True, timeout=None):
		"""Remove and return an item from the queue. 

		If optional args block is true and timeout is None (the default), block
		if necessary until an item is available."""
		if block:
			item = self.__db.blpop(self.key, timeout=timeout)
		else:
			item = self.__db.lpop(self.key)

		if item:
			item = item[1]
		return item
	
	def peek(self, index):
		item = self.__db.lindex(self.key, index)
		
		return item

	def getall(self):
		return self.__db.lrange(self.key, 0, self.qsize())
		
	def get_nowait(self):
		"""Equivalent to get(False)."""
		return self.get(False)