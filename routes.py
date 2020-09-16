from app import app, bot
from flask import request, abort
from config import WELCOME_MESSAGE
import telebot
from telebot import types
import tools
from app import logs
from database import db, User, Favorite
from peewee import DoesNotExist, IntegrityError
import time

# словарь для проверки времени отправки последнего сообщения
message_list = {}


# принимаем данные от telegram для обработки
@app.route("/", methods=["POST"])
def get_updates():
	if request.headers.get('content-type') == 'application/json':
		json_string = request.get_data().decode('utf-8')
		update = types.Update.de_json(json_string)
		bot.process_new_updates([update])
		return 'ok'
	else:
		abort(403)


# обработка начала взаимодействия пользователя с ботом
@bot.message_handler(commands=["start"])
def send_welcome(message):
	logs.add_log("/start executed")
	if message.text == "/start":
		tg_id = message.from_user.id
		logs.add_log("Check user exist")
		# если пользователя не существует в БД, то создаем нового
		if not User.select().where(User.telegram_id == tg_id):
			logs.add_log("Couldn't find user in the db")
			new_user = User(username=message.from_user.username,
			                telegram_id=tg_id)
			logs.add_log(f"{new_user} created")
			new_user.save()
			logs.add_log("New user saved")
		else:
			logs.add_log("User already exist")
			tkeyboard = tools.generate_keyboard()
			bot.reply_to(message,
						WELCOME_MESSAGE,
						parse_mode="markdown",
						reply_markup=tkeyboard)


# обработка всех сообщений происходит здесь
@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_handler(message):
	# находим пользователя в БД
	user = User.get(User.telegram_id == message.from_user.id)
	# если у него есть 3 предупреждения, то игнорим
	if user.warns == 3:
		logs.add_log(f"{user} blocked and trying to send a message to the bot")
		return
	# проверяем сообщение на спам
	try:
		# если пользователь отправляем больще 1 запроса в секунду, то выдаем варн
		if time.time() - message_list[
		    message.from_user.id]["last_message"] < 1 and not user.is_admin():
			user.warns += 1
			user.save()
			logs.add_log(f"Add warn to {user}")
			bot.send_message(
			    message.from_user.id,
			    f"Вам выдано предупреждение за спам.\nПредупреждений: {user.warns}"
			)
			if user.warns == 3:
				bot.send_message(
				    message.from_user.id,
				    "Вы были *забанены* за нарушение правил.\nКонтакты: @fdnflm",
				    parse_mode="markdown")
			return
		else:
			# если не спам, то добавляем время отправки в словарь
			message_list[message.from_user.id] = {"last_message": time.time()}
	except KeyError:
		# если в словаре нет времени, то создаем ключ
		message_list[message.from_user.id] = {"last_message": time.time()}
		logs.add_error(f"{user} doesn't have last_message dict")
	if message.text == "📝 Статьи" or message.text == "⬅️ К статьям":
		tkeyboard = tools.generate_keyboard("articles")
		bot.send_message(message.from_user.id,
		                 "Выберите категорию",
		                 reply_markup=tkeyboard)
	elif message.text == "⭐️ Избранное":
		# получаем избранные посты из БД
		posts = Favorite.select().where(Favorite.user_id == user.id)
		completed_message = ""
		# проверка на наличие публикаций
		if len(posts) == 0:
			completed_message = "У вас нет избранных публикаций 🙁"
			bot.send_message(message.from_user.id, completed_message)
		else:
			# генерируем сообщение со всеми публикациями
			completed_message = "*Избранные публикации:*\n\n"
			completed_message += "\n\n".join(
			    f"{i+1}. [{posts[i].title}]({posts[i].liked_url})"
			    for i in range(len(posts)))
			# генерируем inline кнопку для удаления публикации из избранного
			tkeyboard = tools.generate_keyboard("delete_element")
			bot.send_message(message.from_user.id,
			                 completed_message,
			                 parse_mode="markdown",
			                 reply_markup=tkeyboard,
			                 disable_web_page_preview=True)
	# Лучшие публикации за определённый период
	elif message.text == "📈 Лучшие статьи":
		tkeyboard = tools.generate_keyboard("date")
		bot.send_message(message.from_user.id,
		                 "Выберите период",
		                 reply_markup=tkeyboard)
	# отправляем сгенерованное сообщение по дате пользователю
	elif message.text == "🟢 Сутки":
		bot.send_message(message.from_user.id,
		                 tools.generate_posts("day"),
		                 parse_mode="markdown")
	elif message.text == "🔵 Неделя":
		bot.send_message(message.from_user.id,
		                 tools.generate_posts("week"),
		                 parse_mode="markdown")
	elif message.text == "🟣 Месяц":
		bot.send_message(message.from_user.id,
		                 tools.generate_posts("month"),
		                 parse_mode="markdown")
	# последние сообщения
	elif message.text == "Все подряд":
		#tkeyboard = tools.generate_keyboard("pages")
		bot.send_message(message.from_user.id,
		                 tools.generate_posts("all"),
		                 parse_mode="markdown")
	elif message.text == "⬅️ На главную":
		tkeyboard = tools.generate_keyboard()
		bot.reply_to(message,
		             "Главная",
		             parse_mode="markdown",
		             reply_markup=tkeyboard)
	# обработка запроса на чтение публикации
	elif message.text.startswith("/read"):
		# если пользователь превысил лимит запросов в сутки, то уведомляем его
		if (user.status == 0 and user.requests <= 150) or user.status == 1:
			user.requests += 1
			user.save()
			# получаем публикацию из кэша
			link = tools.get_link(message)
			tkeyboard = None
			favorite = Favorite.select().where(
			    Favorite.liked_url == link.split("\n\n")[1])
			if len(favorite) == 0:  # проверка есть ли публикация в избранном
				tkeyboard = tools.generate_keyboard("favorite")
			else:
				tkeyboard = tools.generate_keyboard("unfavorite")
			bot.send_message(message.from_user.id,
			                 link,
			                 reply_markup=tkeyboard,
			                 parse_mode="markdown")
		else:
			bot.send_message(
			    message.from_user.id,
			    "Лимиты на запросы в день превышены. Ждём вас завтра! :)")


# следуюший шаг для удаления публикации из избранного
# функция передается в next_step_handler()
def get_element(message):
	tkeyboard = tools.generate_keyboard()
	# если пользователь ошибся, он может отменить действие
	if message.text == "/cancel":
		bot.send_message(message.from_user.id,
		                 "Действие отменено",
		                 reply_markup=tkeyboard)
		return
	# обрабатываем ввод пользователя
	user = None
	try:
		index = int(message.text)
		user = User.get(User.telegram_id == message.from_user.id)
		# получаем публикации в список
		favorites = Favorite.select().where(Favorite.user_id == user.id)
		# находим экземпляр модели в списке
		# (список публикаций в сообщении начиниается с единицы, поэтому отнимаем единицу)
		like = favorites[index - 1]
		like.delete_instance()  # удалаем экземпляр из БД
		bot.send_message(message.chat.id, "Публикация удалена из списка")
		# получаем список избранного
		posts = Favorite.select().where(Favorite.user_id == User.get(
		    User.telegram_id == message.from_user.id).id)
		completed_message = ""
		if len(posts) == 0:  # проверка на наличие публикаций
			completed_message = "У вас нет избранных публикаций 🙁"
			bot.send_message(message.from_user.id,
			                 completed_message,
			                 reply_markup=tkeyboard)
		else:
			completed_message = "*Избранные публикации:*\n\n"
			completed_message += "\n\n".join(
			    f"{i+1}. [{posts[i].title}]({posts[i].liked_url})"
			    for i in range(len(posts)))
			tkeyboard = tools.generate_keyboard("delete_element")
			bot.send_message(message.from_user.id,
			                 completed_message,
			                 parse_mode="markdown",
			                 reply_markup=tkeyboard,
			                 disable_web_page_preview=True)
	except Exception as e:
		logs.add_exception(e)
		logs.add_error(f"{user} - got an exception")
		bot.send_message(message.from_user.id,
		                 "Действие отменено. Введите верный номер публикации.",
		                 reply_markup=tkeyboard)
		return


# handling callback requests
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
	chat_id = call.message.chat.id
	if call.data == "add_favorite":  # добавление статьи в избранное
		# собираем данные
		user = User.get(User.telegram_id == chat_id)
		title = call.message.text.split("\n\n")[0]
		url = call.message.text.split("\n\n")[1]
		tkeyboard = tools.generate_keyboard("unfavorite")
		# создаем новую статью в БД
		try:
			like = Favorite(user=user, title=title, liked_url=url)
			like.save()
			# уведомляем пользователя о добавлении статьи в избранное
			# + добавляем к сообщение кнопку для удаления
			bot.answer_callback_query(call.id,
			                          "Добавлено в избранные публикации",
			                          show_alert=True)
			bot.edit_message_reply_markup(chat_id=chat_id,
			                              message_id=call.message.message_id,
			                              reply_markup=tkeyboard)
		except IntegrityError:
			bot.answer_callback_query(call.id,
			                          "Уже добавлено в избранные публикации",
			                          show_alert=True)
			bot.edit_message_reply_markup(chat_id=chat_id,
			                              message_id=call.message.message_id,
			                              reply_markup=tkeyboard)
	elif call.data == "delete_favorite":  # delete favorite article from the db
		user = User.get(User.telegram_id == chat_id)
		tkeyboard = tools.generate_keyboard("favorite")
		# проверяем существование публикации в избранном
		# это нужно, в случае нажатия по кнопке на старом сообщении
		try:
			like = Favorite.get(
			    Favorite.liked_url == call.message.text.split("\n\n")[1])
			like.delete_instance()
		except DoesNotExist:
			logs.add_error(f"{user} - got an exception DoesNotExist")
			bot.answer_callback_query(
			    call.id,
			    "Публикация уже удалена из списка избранного",
			    show_alert=True)
			bot.edit_message_reply_markup(chat_id=chat_id,
			                              message_id=call.message.message_id,
			                              reply_markup=tkeyboard)
			return
		bot.answer_callback_query(call.id,
		                          "Удалено из избранных публикаций",
		                          show_alert=True)
		bot.edit_message_reply_markup(chat_id=chat_id,
		                              message_id=call.message.message_id,
		                              reply_markup=tkeyboard)
	elif call.data == "delete_element":
		# удаление публикации из избранного с ипсользование следующего шага
		markup = types.ForceReply(selective=False)
		bot.send_message(
		    chat_id,
		    "Введите номер публикации\n/cancel - отменить действие",
		    reply_markup=markup)
		bot.register_next_step_handler(call.message, get_element)
	elif call.data == "to_main":
		# вернуть reply keyboard по нажатию на inline кнопку
		tkeyboard = tools.generate_keyboard()
		bot.send_message(chat_id, "Главная", reply_markup=tkeyboard)
