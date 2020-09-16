from flask import Flask
from config import TOKEN
from telebot import TeleBot
from logs import Logging

# Инициализируем основные экземпляры классов
app = Flask(__name__)
bot = TeleBot(TOKEN)
logs = Logging("logs.txt")
logs.add_log("Instances initialized")
