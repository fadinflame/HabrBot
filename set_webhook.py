import requests
from config import TOKEN, WEBHOOK_URL


# установка вебхука для telegram
def set_webhook(url, token):
	data = {"url": url}
	req = requests.post(f"https://api.telegram.org/bot{token}/setWebhook",
	                    data=data)
	print(req.text)
	input()


if __name__ == "__main__":
	set_webhook(WEBHOOK_URL, TOKEN)

# Да, я в курсе про метод bot.set_webhook() в PyTelegramBotAPI
