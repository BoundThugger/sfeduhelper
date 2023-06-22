import requests
import schedule
import time
import firebase_admin
from firebase_admin import credentials, firestore

token = "6148192339:AAHYR-Er2NHMTgITNdfs448m9Gh8Pt1k91U"

cred = credentials.Certificate('sfeduhelper-firebase-adminsdk-me8no-c11c100048.json')

app = firebase_admin.initialize_app(cred)

db = firestore.client()

day_count = 1
def send_daily_message():
    # Код для отправки ежедневного сообщения
    global day_count
    message = "Привет! Это ежедневное сообщение. \n Анекдот дня \n"
    users_ref = db.collection(u'Users')
    jokes_ref = db.collection(u'jokes')
    docs = users_ref.stream()
    jokes = jokes_ref.stream()
    for j in jokes:
        message = j.to_dict()[str(day_count)]
    print(message, day_count)
    day_count += 1
    for doc in docs:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage?chat_id={doc.id}&text={message}")

schedule.every().day.at("10:00").do(send_daily_message)

while True:
    schedule.run_pending()
    time.sleep(1)