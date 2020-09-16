from threading import Thread
from database import User
import pickle
from tools import get_posts
from routes import logs
import time


# поток для Flask
class Main(Thread):
	def __init__(self, name, func=None):
		Thread.__init__(self)
		self.name = name
		self.func = func

	def run(self):
		logs.add_log(f"Thread {self.name} is running")
		self.func()


# поток для сброса запросов
class Timer(Main):
	def run(self):
		while True:
			# обнуляем кол-во запросов у всех пользователей
			upd = User.update(requests=0).where(User.requests > 0)
			upd.execute()
			logs.add_log(f"[{self.name}] User requests reseted")
			time.sleep(86400)  # ждём сутки


# поток для кэширования публикаций
class Cacher(Main):
	def run(self):
		while True:
			# создаем словарь с публикациями
			data = {
			    "all": get_posts("all", use_cache=False),
			    "top_day": get_posts(use_cache=False),
			    "top_week": get_posts(date_filter="weekly", use_cache=False),
			    "top_month": get_posts(date_filter="monthly", use_cache=False)
			}
			# сохраняем словарь в файл
			with open('cache.bin', 'wb') as f:
				pickle.dump(data, f)
			logs.add_log(f"[{self.name}] New articles cached")
			time.sleep(300)  # в сон на 5 минут
