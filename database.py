from peewee import *
import datetime
from config import DB_PATH, ADMIN_ID

db = SqliteDatabase(DB_PATH)


# создаем модель для наследования
class BaseModel(Model):
	date_created = DateTimeField(default=datetime.datetime.utcnow)

	class Meta:
		database = db


# модель пользователя ( внезапно :D )
class User(BaseModel):
	username = CharField(unique=True, null=True)
	telegram_id = IntegerField(unique=True)
	warns = IntegerField(default=0)
	requests = IntegerField(default=0)
	status = IntegerField(default=0)

	def is_admin(self):  # проверка на владельца бота
		if self.telegram_id == ADMIN_ID:
			return True
		return False

	def __str__(self):  # Для логирования, __repr__ перезаписывается peewee
		return f"<User_{self.telegram_id}>"


# модель избранной публикации
class Favorite(BaseModel):
	user = ForeignKeyField(User, backref='favorites')
	title = CharField()
	liked_url = CharField(unique=True)


db.connect()

# создаем таблицы, если этот файл был исполняемым
if __name__ == "__main__":
	db.create_tables([User, Favorite])
