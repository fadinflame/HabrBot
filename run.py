from routes import app, logs
from threads import Main, Timer, Cacher
import time

if __name__ == "__main__":
	logs.add_log("Creating main thread")
	main_thread = Main("main", app.run)  # запуск Flask
	logs.add_log("Creating timer thread")
	timer = Timer("timer")  # обнуление запросов на чтение раз в сутки
	logs.add_log("Creating cacher thread")
	cacher = Cacher("cacher")  # кэширование публикаций
	timer.start()
	cacher.start()
	time.sleep(10) # ждём кэширования, после можно запускать Flask
	main_thread.start()
