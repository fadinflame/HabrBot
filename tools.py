from bs4 import BeautifulSoup
import requests
from telebot import types
import pickle
from app import logs


# получаем публикации с хабра
def get_posts(category="top", date_filter="", page=1, use_cache=True):
	"""
	category: str
		available params - top, all
	date_filter: str
		available params - empty, weekly, monthly
	page: int
		number of page where category is 'all'
	
	returns list
	"""
	logs.add_log(
	    f"New request ct={category}|df={date_filter}|page={page}|cache={use_cache}"
	)
	container = []
	# возвращаем кэшированные статьи
	if use_cache:
		logs.add_log("Using cached posts from file")
		data = pickle.load(open("cache.bin", "rb"))
		if category == "all":
			container = data["all"]
		elif category == "top":
			if not date_filter:
				container = data["top_day"]
			elif date_filter == "weekly":
				container = data["top_week"]
			elif date_filter == "monthly":
				container = data["top_month"]
	# возвращаем статьи с хабра
	else:
		url = ""
		if category == "top":
			url = f"https://habr.com/ru/top/{date_filter}"
		elif category == "all":
			url = f"https://habr.com/ru/all/page{page}"
		request = requests.get(url)
		logs.add_log(f"GET {url} ({request.status_code})")
		# парсим загаловок и ссылку из html
		soup = BeautifulSoup(request.text, 'lxml')
		for hub in soup.find_all("a", class_="post__title_link"):
			# добавляем в список
			container.append((hub.text, hub["href"]))
	return container


# генерация кнопок для взаимодействия
def generate_keyboard(keyboard_type="welcome"):
	"""
	keyboard_type: str
		available params:
			"welcome" - main menu,
			"articles" - choose category,
			"date" - choose date,
			"favorite" - add to favorite btn,
			"unfavorite" - del favorite btn,
			"delete_element" - del favorite from the list,
	
	returns keyboard instance 
	"""
	tkeyboard = types.ReplyKeyboardMarkup(row_width=1)
	if keyboard_type == "welcome":
		# "главное меню"
		show_article = types.KeyboardButton("📝 Статьи")
		favorite = types.KeyboardButton("⭐️ Избранное")
		tkeyboard.add(show_article, favorite)
	elif keyboard_type == "articles":
		# выбор категории
		top_articles = types.KeyboardButton("📈 Лучшие статьи")
		all_articles = types.KeyboardButton("Все подряд")
		to_start = types.KeyboardButton("⬅️ На главную")
		tkeyboard.add(top_articles, all_articles, to_start)
	elif keyboard_type == "date":
		# выбор периода времени
		today = types.KeyboardButton("🟢 Сутки")
		week = types.KeyboardButton("🔵 Неделя")
		month = types.KeyboardButton("🟣 Месяц")
		to_articles = types.KeyboardButton("⬅️ К статьям")
		tkeyboard.add(today, week, month, to_articles)
	# elif keyboard_type == "pages":
	# 	tkeyboard = types.InlineKeyboardMarkup(row_width=3)
	# 	for index in range(1, 10):
	# 		if index % 3 == 0:
	# 			tkeyboard.add(types.InlineKeyboardButton(index - 2, callback_data=f"page{index - 2}"),
	# 						  types.InlineKeyboardButton(index - 1, callback_data=f"page{index - 1}"),
	# 						  types.InlineKeyboardButton(index, callback_data=f"page{index}"),)
	elif keyboard_type == "favorite":
		# кнопка для добавления в избранное под отправленной публикацией
		tkeyboard = types.InlineKeyboardMarkup(row_width=1)
		add_favorite = types.InlineKeyboardButton("Добавить в избранное ❤️",
		                                          callback_data="add_favorite")
		tkeyboard.add(add_favorite)
	elif keyboard_type == "unfavorite":
		# кнопка для удаления из избранного под отправленной публикацией
		tkeyboard = types.InlineKeyboardMarkup(row_width=1)
		delete_favorite = types.InlineKeyboardButton(
		    "Добавлено в избранное ✅", callback_data="delete_favorite")
		tkeyboard.add(delete_favorite)
	elif keyboard_type == "delete_element":
		# кнопка для публикации под списком избранного
		tkeyboard = types.InlineKeyboardMarkup(row_width=1)
		delete_favorite = types.InlineKeyboardButton(
		    "Удалить элемент ❌", callback_data="delete_element")
		to_main = types.InlineKeyboardButton("На главную ⬅️",
		                                     callback_data="to_main")
		tkeyboard.add(to_main, delete_favorite)
	return tkeyboard


# генерация сообщения с публикациями
def generate_posts(category="all", page=1):
	"""
	category: str
		available params:
			all, top
	page: int
		number of page where category is 'all'

	returns string
	"""
	posts = []
	completed_message = ""
	if category == "all":
		posts = get_posts("all", page=page)
		completed_message = "*Вот последние статьи:*\n\n"
		completed_message += "\n\n".join(f"_{posts[i][0]}_\n/readall{i}"
		                                 for i in range(len(posts)))
	elif category == "day":
		posts = get_posts(page=page)
		completed_message = "*Вот статьи за сутки:*\n\n"
		completed_message += "\n\n".join(f"_{posts[i][0]}_\n/readday{i}"
		                                 for i in range(len(posts)))
	elif category == "week":
		posts = get_posts(date_filter="weekly", page=page)
		completed_message = "*Вот статьи за неделю:*\n\n"
		completed_message += "\n\n".join(f"_{posts[i][0]}_\n/readweek{i}"
		                                 for i in range(len(posts)))
	elif category == "month":
		posts = get_posts(date_filter="monthly", page=page)
		completed_message = "*Вот статьи за неделю:*\n\n"
		completed_message += "\n\n".join(f"_{posts[i][0]}_\n/readmonth{i}"
		                                 for i in range(len(posts)))
	return completed_message


# получение публикации из списка
def get_link(message, page=1):
	"""
	message: str
		telegram message from user
	page: int
		number of page where category is 'all'

	returns string
	"""
	posts = []
	article = 0
	if message.text.startswith("/readall"):
		posts = get_posts("all", page=page)
		article = int(message.text.split("readall")[1])
	if message.text.startswith("/readday"):
		posts = get_posts(page=page)
		article = int(message.text.split("readday")[1])
	if message.text.startswith("/readweek"):
		posts = get_posts(date_filter="weekly", page=page)
		article = int(message.text.split("readweek")[1])
	if message.text.startswith("/readmonth"):
		posts = get_posts(date_filter="monthly", page=page)
		article = int(message.text.split("readmonth")[1])
	return f"*{posts[article][0]}*\n\n{posts[article][1]}"
