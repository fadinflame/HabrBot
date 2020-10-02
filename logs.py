import logging
import datetime
import pytz


class Logging:
	def __init__(self, path):
		log = logging.getLogger('werkzeug')
		log.setLevel(logging.ERROR)
		logging.basicConfig(filename=path, level=logging.INFO)
		self.timezone = pytz.timezone("Europe/Moscow")

	def add_log(self, message):
		msg = f"[{datetime.datetime.now(tz=self.timezone).strftime('%H:%M:%S %d.%m.%Y')}] {message}"
		print(msg)
		logging.info(msg)

	def add_error(self, message):
		msg = f"[{datetime.datetime.now(tz=self.timezone).strftime('%H:%M:%S %d.%m.%Y')}] {message}"
		print(msg)
		logging.error(msg)

	def add_exception(self, exception):
		msg = f"[{datetime.datetime.now(tz=self.timezone).strftime('%H:%M:%S %d.%m.%Y')}] --- EXCEPTION ---\n{exception}"
		print(msg)
		logging.exception(msg)
