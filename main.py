import telebot
import datetime
import threading
import openai
import firebase_admin
from firebase_admin import credentials, firestore
from telebot import types

cred = credentials.Certificate('sfeduhelper-firebase-adminsdk-me8no-8e1a837f38.json')

app = firebase_admin.initialize_app(cred)

db = firestore.client()

openai.api_key = "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"
bot = telebot.TeleBot('6148192339:AAHYR-Er2NHMTgITNdfs448m9Gh8Pt1k91U')

####################################################################################################################
@bot.message_handler(commands=['gpt_new_dialog'])
def reminder_message(message):
    messages = []
    bot.send_message(message.chat.id, 'Новый диалог создан!')
    bot.register_next_step_handler(message, nextQW, messages)
def nextQW(message, messages):
    try:
        messages = update(messages, "user", message.text)
        model_res = get_response(messages)
        bot.send_message(message.chat.id,
                         model_res)
        bot.register_next_step_handler(message, nextQW, messages)
    except:
        bot.send_message(message.chat.id,
                         'Подождите минутку, слишком много вопросов!')
def update(messages, role, content):
    messages.append({"role":role, "content":content})
    return messages
def get_response(messages):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return response['choices'][0]['message']['content']

####################################################################################################################

button = {'uni.Иктиб': 'Иктиб', 'uni.РТСУ': 'РТСУ', 'uni.Еще1': 'Еще1', 'uni.Еще2': 'Еще2'}
user_dict = {}
class User:
    def __init__(self, name):
        self.name = name
        self.Uni = None
        self.id = None
        self.isActive = False
@bot.message_handler(commands=['start'])
def start(message):
    isExist = False
    users_ref = db.collection(u'Users')
    docs = users_ref.stream()
    for doc in docs:
        if doc.id == str(message.chat.id):
            isExist = True
            bot.send_message(message.chat.id, f'{doc.to_dict()["Name"]}, с возвращением!')
            break

    if not isExist:
        bot.send_message(message.chat.id, 'Как к вам обращаться?')
        bot.register_next_step_handler(message, setname)


def setname(message):
    user = User(message.text)
    user_dict[message.chat.id] = user
    kb = types.InlineKeyboardMarkup()
    btn = []
    for i in button.items():
        key = types.InlineKeyboardButton(text=f'кнопка {i[1]}', callback_data=i[0])
        btn.append(key)
    kb.add(*btn)
    bot.send_message(message.chat.id, f'Отлично!{user.name}, теперь расскажи в каком ты учишься вузе?', reply_markup=kb)
    bot.register_next_step_handler(message, falserepl1)

def falserepl1(message):
    user = user_dict[message.chat.id]
    if user.isActive:
        get_user_text(message)
    else:
        bot.delete_message(message.chat.id, message.message_id - 1)
        kb = types.InlineKeyboardMarkup()
        btn = []
        for i in button.items():
            key = types.InlineKeyboardButton(text=f'кнопка {i[1]}', callback_data=i[0])
            btn.append(key)
        kb.add(*btn)
        bot.send_message(message.chat.id, f'{user.name}, выберите 1 из кнопок', reply_markup=kb)
        bot.register_next_step_handler(message, falserepl1)
@bot.callback_query_handler(func=lambda call: call.data.startswith('uni.'))
def inline_kb(call):
    if call.data in button:
        user = user_dict[call.message.chat.id]
        user.uni = call.data.split('.')[1]
        bot.send_message(call.message.chat.id, f'Отлично!{user.name}, регистрация завершена!')
        registration(call.message)
def registration(message):
    user_dict[message.chat.id].isActive = True
    user = user_dict[message.chat.id]
    doc_ref = db.collection(u'Users').document(str(message.chat.id))
    doc_ref.set({
        u'Name':user.name,
        u'Uni':user.uni
    })
    start_mess_1 = f'Здравствуйте, <b>{user.name}</b>, это помощник студента ЮФУ'
    start_mess_2 = f'Я могу хранить все ваши <u>методические материалы</u>, напоминать о твоих <u>дедлайнах</u> и <u>долгах</u>'
    start_mess_3 = f'Чтобы воспользоваться моими функциями, нажмите на кнопку <b>"Возможности"</b>'

    bot.send_message(message.chat.id, start_mess_1, parse_mode='html')
    bot.send_message(message.chat.id, start_mess_2, parse_mode='html')

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    opp = types.KeyboardButton('Возможности')
    markup.add(opp)
    bot.send_message(message.chat.id, start_mess_3, parse_mode='html', reply_markup=markup)
###################################################################################################################
@bot.message_handler(commands=['addremind'])
def reminder_message(message):
    bot.send_message(message.chat.id, 'Введите название напоминания:')
    bot.register_next_step_handler(message, set_reminder_name)
def set_reminder_name(message, tmp = ''):
    user_data = {}
    if tmp!='':
        user_data[message.chat.id] = {'reminder_name': tmp}
    else:
        user_data[message.chat.id] = {'reminder_name': message.text}
    bot.send_message(message.chat.id,
                     'Введите дату и время, когда вы хотите получить напоминание в формате ГГГГ-ММ-ДД чч:мм')
    bot.register_next_step_handler(message, reminder_set, user_data)
def reminder_set(message, user_data):
    try:
        reminder_time = datetime.datetime.strptime(message.text, '%Y-%m-%d %H:%M')
        now = datetime.datetime.now()
        delta = reminder_time - now
        if delta.total_seconds() <= 0:
            bot.send_message(message.chat.id, 'Эта дата уже прошла')
        else:
            reminder_name = user_data[message.chat.id]['reminder_name']
            bot.send_message(message.chat.id,
                             f'Напоминание "<b>{reminder_name}</b>" установлено на <u>{reminder_time}</u>',
                             parse_mode='html')
            reminder_timer = threading.Timer(delta.total_seconds(), send_reminder, [message.chat.id, reminder_name])
            reminder_timer.start()
    except ValueError:
        bot.send_message(message.chat.id, 'Вы ввели неверный формат даты и времени, попробуйте ещё раз')
        set_reminder_name(message, user_data[message.chat.id]['reminder_name'])
def send_reminder(chat_id, reminder_name):
    bot.send_message(chat_id, f'Напоминание:\n{reminder_name}!', parse_mode='html')
#################################################################################################################

@bot.message_handler()
def get_user_text(message):
    if message.text == 'Возможности':
        mess_opp = f'Сохранить файл - <b>/savefile</b>\nПолучить файл - <b>/getfile</b>\nУзнать расписание - <b>/schedule</b>\nДобавить напоминание - <b>/addremind</b>\nСоздать новый диалог Chat GPT - <b>/gpt_new_dialog</b>'
        bot.send_message(message.chat.id, mess_opp, parse_mode='html')
    else:
        err_mess = 'Я тебя не понимаю'
        bot.send_message(message.chat.id, err_mess)


#################################################################################################################
# @bot.callback_query_handler(func=lambda call: True)
# def ansopp(call):
# if call.data == 'opp'


# @bot.message_handler(commands=['help'])

# @bot.message_handler(commands=['timetable'])
# def timetable(message):
#   if message.text == 'Узнать расписание':
#       gr_mess = 'Укажите свою группу'
#      bot.send_message(message.chat.id, gr_mess)


# @bot.message_handler()
# def get_user_text(message):


bot.polling(none_stop=True)
