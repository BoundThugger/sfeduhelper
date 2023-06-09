import datetime
import threading
import openai
import firebase_admin
import json
import requests
from firebase_admin import credentials, firestore
from telebot import types
import telebot
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from IRTSU import site_irtsu, pars_irtsu
from IUAS import site_iuas, pars_iuas

cred = credentials.Certificate('sfeduhelper-firebase-adminsdk-me8no-c11c100048.json')

app = firebase_admin.initialize_app(cred)

db = firestore.client()

openai.api_key = "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"

bot = telebot.TeleBot('6148192339:AAHYR-Er2NHMTgITNdfs448m9Gh8Pt1k91U')

####################################################################################################################
@bot.message_handler(commands=['gpt_new_dialog'])
def reminder_message(message):
    if not check_autorized(message):
        return
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
    messages.append({"role": role, "content": content})
    return messages


def get_response(messages):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return response['choices'][0]['message']['content']


####################################################################################################################

button = {'uni.ИКТИБ': 'ИКТИБ', 'uni.ИРТСУ': 'ИРТСУ', 'uni.ИУЭС': 'ИУЭС'}
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
            user = User(doc.to_dict()["Name"])
            user.Uni = doc.to_dict()["Uni"]
            user.isActive = True
            user_dict[message.chat.id] = user
            break

    if not isExist:
        bot.send_message(message.chat.id, 'Как к вам обращаться?')
        bot.register_next_step_handler(message, setname)


def setname(message):
    print(1)
    user = User(message.text)
    user_dict[message.chat.id] = user
    kb = types.InlineKeyboardMarkup()
    btn = []
    for i in button.items():
        key = types.InlineKeyboardButton(text=f'{i[1]}', callback_data=i[0])
        btn.append(key)
    kb.add(*btn)
    bot.send_message(message.chat.id, f'Отлично!{user.name}, теперь расскажи в каком ты учишься вузе?', reply_markup=kb)


def falserepl1(message):
    print(2)
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
    print(3)
    if call.data in button:
        user = user_dict[call.message.chat.id]
        user.Uni = call.data.split('.')[1]
        user_dict[call.message.chat.id] = user
        bot.send_message(call.message.chat.id,  f'Отлично!{user.name}, регистрация завершена!')
        registration(call.message)

        """bot.send_message(call.message.chat.id, f'Отлично!{user.name}, теперь скажи в какой ты группе?')
        bot.register_next_step_handler(call.message, group_info)"""


def group_info(message):
    print(4)
    user = user_dict[message.chat.id]
    user_dict[message.chat.id].group = message.text
    bot.send_message(message.chat.id, f'Отлично!{user.name}, регистрация завершена!')
    registration(message)


def registration(message):
    print(5)
    user_dict[message.chat.id].isActive = True
    user = user_dict[message.chat.id]
    doc_ref = db.collection(u'Users').document(str(message.chat.id))
    doc_ref.set({
        u'Name': user.name,
        u'Uni': user.Uni
    })
    start_mess_1 = f'Здравствуйте, <b>{user.name}</b>, это помощник студента ЮФУ'
    start_mess_2 = f'Я могу <u>помочь в решении любого вопроса с помощью <b>ChatGPT</b></u>, напоминать о твоих <u>дедлайнах</u> и <u>долгах</u> и показывать твоё <u>расписание</u>'
    start_mess_3 = f'Чтобы воспользоваться моими функциями, нажмите на кнопку <b>"Возможности"</b>'

    bot.send_message(message.chat.id, start_mess_1, parse_mode='html')
    bot.send_message(message.chat.id, start_mess_2, parse_mode='html')

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    opp = types.KeyboardButton('Возможности')
    markup.add(opp)
    bot.send_message(message.chat.id, start_mess_3, parse_mode='html', reply_markup=markup)


###################################################################################################################
@bot.message_handler(commands=['schedule'])
def start(message):
    if not check_autorized(message):
        return
    markup = types.ReplyKeyboardMarkup()
    IRTSU = types.KeyboardButton('ИРТСУ')
    IKTIB = types.KeyboardButton('ИКТИБ')
    IUAS = types.KeyboardButton('ИУЭС')
    markup.add(IRTSU, IKTIB, IUAS)
    bot.send_message(message.chat.id, 'Выберите институт', reply_markup=markup)
    bot.register_next_step_handler(message, get_text)


def get_text(message):
    user = user_dict[message.chat.id]
    if message.text == 'ИРТСУ':
        markup1 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        a1 = types.KeyboardButton('1 курс')
        a2 = types.KeyboardButton('2 курс')
        a3 = types.KeyboardButton('3 курс')
        a4 = types.KeyboardButton('4 курс')
        a5 = types.KeyboardButton('5 курс')
        a6 = types.KeyboardButton('6 курс')
        markup1.add(a1, a2, a3, a4, a5, a6)
        bot.send_message(message.chat.id, 'Выберите курс', reply_markup=markup1)
        bot.register_next_step_handler(message, irtsu_courses)

    if message.text == 'ИКТИБ':
        bot.send_message(message.chat.id, 'Введите название группы Пример: Ктбо1-7')
        bot.register_next_step_handler(message, ictis_rasp)
        """ if user.Uni == 'ИКТИБ':
                url = "https://webictis.sfedu.ru/schedule-api/?query=" + user.group
                ans = ""
                response = requests.get(url)
                json_object = json.loads(response.text)
                table = json_object["table"]["table"]
                for i in range(2, 7):
                    ans += table[i][0] + "\n"
                    for j in range(7):
                        if table[i][j + 1] != "":
                            ans += f"{j + 1} пара" + "\n"
                            ans += table[i][j + 1] + "\n"
            bot.send_message(message.chat.id, ans)
        else:
            print(user.Uni)
            bot.send_message(message.chat.id, 'Вы не состоите в этом вузе!')"""

    if message.text == 'ИУЭС':
        markup3 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        a1 = types.KeyboardButton('1 курс')
        a2 = types.KeyboardButton('2 курс')
        a3 = types.KeyboardButton('3 курс')
        a4 = types.KeyboardButton('4 курс')
        a5 = types.KeyboardButton('5 курс')
        a6 = types.KeyboardButton('Школа')
        markup3.add(a1, a2, a3, a4, a5, a6)
        bot.send_message(message.chat.id, 'Выберите курс', reply_markup=markup3)
        bot.register_next_step_handler(message, iuas_courses)
def ictis_rasp(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    opp = types.KeyboardButton('Возможности')
    markup.add(opp)
    try:
        url = "https://webictis.sfedu.ru/schedule-api/?query=" + message.text
        ans = ""
        response = requests.get(url)
        json_object = json.loads(response.text)
        table = json_object["table"]["table"]
        for i in range(2, 7):
            ans += table[i][0] + "\n"
            for j in range(7):
                if table[i][j + 1] != "":
                    ans += f"{j + 1} пара" + "\n"
                    ans += table[i][j + 1] + "\n"
        bot.send_message(message.chat.id, ans, reply_markup=markup)
    except:
        bot.send_message(message.chat.id, "Такой группы не существует!", reply_markup=markup)
def irtsu_courses(message):
    if message.text == '1 курс':
        markup1 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        a1 = types.KeyboardButton('РТао1-12')
        a2 = types.KeyboardButton('РТао1-22')
        a3 = types.KeyboardButton('РТао1-32')
        a4 = types.KeyboardButton('РТао1-42')
        a5 = types.KeyboardButton('РТао1-52')
        b1 = types.KeyboardButton('РТбо1-12')
        b2 = types.KeyboardButton('РТбо1-22')
        b3 = types.KeyboardButton('РТбо1-32')
        b4 = types.KeyboardButton('РТбо1-42')
        b5 = types.KeyboardButton('РТбо1-52')
        b6 = types.KeyboardButton('РТбо1-62')
        b7 = types.KeyboardButton('РТбо1-72')
        b8 = types.KeyboardButton('РТбо1-92')
        b9 = types.KeyboardButton('РТбо1-102')
        m1 = types.KeyboardButton('РТмо1-12')
        m2 = types.KeyboardButton('РТмо1-22')
        m3 = types.KeyboardButton('РТмо1-32')
        m4 = types.KeyboardButton('РТмо1-42')
        m5 = types.KeyboardButton('РТмо1-52')
        m6 = types.KeyboardButton('РТмо1-62')
        m7 = types.KeyboardButton('РТмо1-72')
        m8 = types.KeyboardButton('РТмо1-82')
        s1 = types.KeyboardButton('РТсо1-12')
        s2 = types.KeyboardButton('РТсо1-22')
        s3 = types.KeyboardButton('РТсо1-32')
        s4 = types.KeyboardButton('РТсо1-42')
        s5 = types.KeyboardButton('РТсо1-52')
        s6 = types.KeyboardButton('РТсо1-62')
        s7 = types.KeyboardButton('РТсо1-72')
        s8 = types.KeyboardButton('РТсо1-82')
        bv1 = types.KeyboardButton('РТбв1-82')
        bv2 = types.KeyboardButton('РТбв1-102')
        markup1.add(a1, a2, a3, a4, a5, b1, b2, b3, b4, b5, b6, b7, b8, b9, m1, m2, m3, m4, m5, m6, m7, m8, s1, s2, s3,
                    s4, s5, s6, s7, s8, bv1, bv2)
        bot.send_message(message.chat.id, 'Укажите вашу группу:', reply_markup=markup1)
        bot.register_next_step_handler(message, first_course)

    if message.text == '2 курс':
        markup2 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        a1 = types.KeyboardButton('РТао2-11')
        a2 = types.KeyboardButton('РТао2-21')
        a3 = types.KeyboardButton('РТао2-31')
        a4 = types.KeyboardButton('РТао2-41')
        b1 = types.KeyboardButton('РТбо2-11')
        b2 = types.KeyboardButton('РТбо2-21')
        b3 = types.KeyboardButton('РТбо2-31')
        b4 = types.KeyboardButton('РТбо2-41')
        b5 = types.KeyboardButton('РТбо2-61')
        b6 = types.KeyboardButton('РТбо2-71')
        b7 = types.KeyboardButton('РТбо2-81')
        b8 = types.KeyboardButton('РТбо2-91')
        m1 = types.KeyboardButton('РТмо2-11')
        m2 = types.KeyboardButton('РТмо2-21')
        m3 = types.KeyboardButton('РТмо2-31')
        m4 = types.KeyboardButton('РТмо2-41')
        m5 = types.KeyboardButton('РТмо2-51')
        m6 = types.KeyboardButton('РТмо2-61')
        m7 = types.KeyboardButton('РТмо2-71')
        m8 = types.KeyboardButton('РТмо2-81')
        s1 = types.KeyboardButton('РТсо2-11')
        s2 = types.KeyboardButton('РТсо2-21')
        s3 = types.KeyboardButton('РТсо2-41')
        s4 = types.KeyboardButton('РТсо2-51')
        s5 = types.KeyboardButton('РТсо2-61')
        markup2.add(a1, a2, a3, a4, b1, b2, b3, b4, b5, b6, b7, b8, m1, m2, m3, m4, m5, m6, m7, m8, s1, s2,
                    s3, s4, s5)
        bot.send_message(message.chat.id, 'Укажите вашу группу:', reply_markup=markup2)
        bot.register_next_step_handler(message, second_course)

    if message.text == '3 курс':
        markup3 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        a1 = types.KeyboardButton('РТао3-10')
        a2 = types.KeyboardButton('РТао3-20')
        a3 = types.KeyboardButton('РТао3-30')
        a4 = types.KeyboardButton('РТао3-40')
        b1 = types.KeyboardButton('РТбо3-10')
        b2 = types.KeyboardButton('РТбо3-20')
        b3 = types.KeyboardButton('РТбо3-30')
        b4 = types.KeyboardButton('РТбо3-40')
        b5 = types.KeyboardButton('РТбо3-60')
        b6 = types.KeyboardButton('РТбо3-70')
        b7 = types.KeyboardButton('РТбо3-80')
        s1 = types.KeyboardButton('РТсо3-10')
        s2 = types.KeyboardButton('РТсо3-20')
        s3 = types.KeyboardButton('РТсо3-30')
        s4 = types.KeyboardButton('РТсо3-40')
        s5 = types.KeyboardButton('РТсо3-50')
        s6 = types.KeyboardButton('РТсо3-60')
        markup3.add(a1, a2, a3, a4, b1, b2, b3, b4, b5, b6, b7, s1, s2,
                    s3, s4, s5, s6)
        bot.send_message(message.chat.id, 'Укажите вашу группу:', reply_markup=markup3)
        bot.register_next_step_handler(message, third_course)

    if message.text == '4 курс':
        markup4 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        a1 = types.KeyboardButton('РТао4-19')
        a2 = types.KeyboardButton('РТао4-29')
        a3 = types.KeyboardButton('РТао4-39')
        a4 = types.KeyboardButton('РТао4-49')
        b1 = types.KeyboardButton('РТбо4-19')
        b2 = types.KeyboardButton('РТбо4-39')
        b3 = types.KeyboardButton('РТбо4-59')
        b4 = types.KeyboardButton('РТбо4-69')
        b5 = types.KeyboardButton('РТбо4-79')
        b6 = types.KeyboardButton('РТбо4-89')
        b7 = types.KeyboardButton('РТбо4-99')
        s1 = types.KeyboardButton('РТсо4-19')
        s2 = types.KeyboardButton('РТсо4-29')
        s3 = types.KeyboardButton('РТсо4-39')
        s4 = types.KeyboardButton('РТсо4-49')
        s5 = types.KeyboardButton('РТсо4-59')
        s6 = types.KeyboardButton('РТсо4-69')
        markup4.add(a1, a2, a3, a4, b1, b2, b3, b4, b5, b6, b7, s1, s2,
                    s3, s4, s5, s6)
        bot.send_message(message.chat.id, 'Укажите вашу группу:', reply_markup=markup4)
        bot.register_next_step_handler(message, fourth_course)

    if message.text == '5 курс':
        markup5 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        s1 = types.KeyboardButton('РТсо5-18')
        s2 = types.KeyboardButton('РТсо5-28')
        s3 = types.KeyboardButton('РТсо5-48')
        s4 = types.KeyboardButton('РТсо5-68')
        markup5.add(s1, s2, s3, s4)
        bot.send_message(message.chat.id, 'Укажите вашу группу:', reply_markup=markup5)
        bot.register_next_step_handler(message, fifth_course)

    if message.text == '6 курс':
        markup6 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        s1 = types.KeyboardButton('РТсо6-57')
        dpo = types.KeyboardButton('ДПО')
        lyc = types.KeyboardButton('Лицей 4')
        rt_i = types.KeyboardButton('РТ-И')
        inzh_sc = types.KeyboardButton('Инженер. школа')
        inzh_sc2 = types.KeyboardButton('Инженер. шк. 2')
        M1 = types.KeyboardButton('М-12')
        M2 = types.KeyboardButton('М-22')
        M3 = types.KeyboardButton('М-32')
        M4 = types.KeyboardButton('М-11')
        M5 = types.KeyboardButton('М-21')
        M6 = types.KeyboardButton('М-31')
        M7 = types.KeyboardButton('М-10')
        M8 = types.KeyboardButton('М-30')
        M9 = types.KeyboardButton('М-19')
        M10 = types.KeyboardButton('М-29')
        T1 = types.KeyboardButton('Т-12')
        sau1 = types.KeyboardButton('САУ-1')
        sau2 = types.KeyboardButton('САУ-2')
        sau3 = types.KeyboardButton('САУ-3')
        dig_kaf = types.KeyboardButton('Циф. каф.')
        markup6.add(s1, dpo, lyc, rt_i, inzh_sc, inzh_sc2, M1, M2, M3, M4, M5, M6, M7, M8, M9, M10, T1, sau1, sau2,
                    sau3, dig_kaf)
        bot.send_message(message.chat.id, 'Укажите вашу группу:', reply_markup=markup6)
        bot.register_next_step_handler(message, sixth_course)


def iuas_courses(message):
    if message.text == '1 курс':
        markup1 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        b1 = types.KeyboardButton('УЭбо1-4')
        b2 = types.KeyboardButton('УЭбо1-3')
        b3 = types.KeyboardButton('УЭбо1-2')
        m1 = types.KeyboardButton('УЭмо1-6')
        m2 = types.KeyboardButton('УЭмо1-5')
        m3 = types.KeyboardButton('УЭмо1-4')
        m4 = types.KeyboardButton('УЭмв1-2')
        m5 = types.KeyboardButton('УЭмз1-5')
        s1 = types.KeyboardButton('УЭсо1-5')
        s2 = types.KeyboardButton('УЭсо1-6 (1п.)')
        s3 = types.KeyboardButton('УЭсо1-6 (2п.)')
        s4 = types.KeyboardButton('УЭсо1-16 (1п.)')
        s5 = types.KeyboardButton('УЭсо1-16 (2п.)')
        markup1.add(b1, b2, b3, m1, m2, m3, m4, m5, s1, s2, s3, s4, s5)
        bot.send_message(message.chat.id, 'Укажите вашу группу:', reply_markup=markup1)
        bot.register_next_step_handler(message, first_course_iuas)

    if message.text == '2 курс':
        markup2 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        b1 = types.KeyboardButton('УЭбо2-4')
        b2 = types.KeyboardButton('УЭбо2-3')
        b3 = types.KeyboardButton('УЭбо2-2')
        m1 = types.KeyboardButton('УЭмо2-7')
        m2 = types.KeyboardButton('УЭмо2-6')
        m3 = types.KeyboardButton('УЭмо2-5')
        m4 = types.KeyboardButton('УЭмв2-1')
        m5 = types.KeyboardButton('УЭмз2-5')
        s1 = types.KeyboardButton('УЭсо2-5')
        s2 = types.KeyboardButton('УЭсо2-16')
        s3 = types.KeyboardButton('УЭсо2-6 (2п.)')
        s4 = types.KeyboardButton('УЭсо2-6 (1п.)')
        markup2.add(b1, b2, b3, m1, m2, m3, m4, m5, s1, s2, s3, s4)
        bot.send_message(message.chat.id, 'Укажите вашу группу:', reply_markup=markup2)
        bot.register_next_step_handler(message, second_course_iuas)

    if message.text == '3 курс':
        markup3 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        b1 = types.KeyboardButton('УЭбо3-4')
        b2 = types.KeyboardButton('УЭбо3-3')
        b3 = types.KeyboardButton('УЭбо3-2')
        m1 = types.KeyboardButton('УЭмз3-5')
        m2 = types.KeyboardButton('УЭмв3-4')
        s1 = types.KeyboardButton('УЭсо3-5')
        s2 = types.KeyboardButton('УЭсо3-6 (1п.)')
        s3 = types.KeyboardButton('УЭсо3-6 (2п.)')
        s4 = types.KeyboardButton('УЭсо3-6 (3п.)')
        markup3.add(b1, b2, b3, m1, m2, s1, s2, s3, s4)
        bot.send_message(message.chat.id, 'Укажите вашу группу:', reply_markup=markup3)
        bot.register_next_step_handler(message, third_course_iuas)

    if message.text == '4 курс':
        markup4 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        b1 = types.KeyboardButton('УЭбо4-4')
        b2 = types.KeyboardButton('УЭбо4-3')
        b3 = types.KeyboardButton('УЭбз4-2')
        s1 = types.KeyboardButton('УЭсо4-5')
        markup4.add(b1, b2, b3, s1)
        bot.send_message(message.chat.id, 'Укажите вашу группу:', reply_markup=markup4)
        bot.register_next_step_handler(message, fourth_course_iuas)

    if message.text == '5 курс':
        markup5 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        s1 = types.KeyboardButton('УЭсо5-5')
        s2 = types.KeyboardButton('УЭсо5-6 (1п.)')
        s3 = types.KeyboardButton('УЭсо5-6 (2п.)')
        s4 = types.KeyboardButton('УЭсо5-6 (3п.)')
        markup5.add(s1, s2, s3, s4)
        bot.send_message(message.chat.id, 'Укажите вашу группу:', reply_markup=markup5)
        bot.register_next_step_handler(message, fifth_course_iuas)

    if message.text == 'Школа':
        markup6 = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        s1 = types.KeyboardButton('9 класс (1п.)')
        s2 = types.KeyboardButton('10 класс (1п.)')
        s3 = types.KeyboardButton('11 класс (1п.)')
        s4 = types.KeyboardButton('11 класс (2п.)')
        s5 = types.KeyboardButton('11 класс (3п.)')
        markup6.add(s1, s2, s3, s4, s5)
        bot.send_message(message.chat.id, 'Укажите вашу группу:', reply_markup=markup6)
        bot.register_next_step_handler(message, school_iuas)


def first_course(message):
    if message.text == 'РТао1-12':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s1'))
    elif message.text == 'РТао1-22':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s2'))
    elif message.text == 'РТао1-32':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s3'))
    elif message.text == 'РТао1-42':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s4'))
    elif message.text == 'РТао1-52':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s5'))
    elif message.text == 'РТбо1-12':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s6'))
    elif message.text == 'РТбо1-22':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s7'))
    elif message.text == 'РТбо1-32':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s8'))
    elif message.text == 'РТбо1-42':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s9'))
    elif message.text == 'РТбо1-52':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s10'))
    elif message.text == 'РТбо1-62':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s11'))
    elif message.text == 'РТбо1-72':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s12'))
    elif message.text == 'РТбо1-92':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s13'))
    elif message.text == 'РТбо1-102':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s14'))
    elif message.text == 'РТмо1-12':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s15'))
    elif message.text == 'РТмо1-22':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s16'))
    elif message.text == 'РТмо1-32':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s17'))
    elif message.text == 'РТмо1-42':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s18'))
    elif message.text == 'РТмо1-52':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s19'))
    elif message.text == 'РТмо1-62':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s20'))
    elif message.text == 'РТмо1-72':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s21'))
    elif message.text == 'РТмо1-82':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s22'))
    elif message.text == 'РТсо1-12':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s23'))
    elif message.text == 'РТсо1-22':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s24'))
    elif message.text == 'РТсо1-32':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s25'))
    elif message.text == 'РТсо1-42':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s26'))
    elif message.text == 'РТсо1-52':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s27'))
    elif message.text == 'РТсо1-62':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s28'))
    elif message.text == 'РТсо1-72':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s29'))
    elif message.text == 'РТсо1-82':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s30'))
    elif message.text == 'РТбв1-82':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s31'))
    elif message.text == 'РТбв1-102':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s32'))
    else:
        mess = "Такой группы не существует!"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    opp = types.KeyboardButton('Возможности')
    markup.add(opp)
    bot.send_message(message.chat.id, mess, parse_mode='html', reply_markup=markup)


def second_course(message):
    if message.text == 'РТао2-11':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s33'))

    elif message.text == 'РТао2-21':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s34'))

    elif message.text == 'РТао2-31':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s35'))

    elif message.text == 'РТао2-41':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s36'))

    elif message.text == 'РТбо2-11':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s37'))

    elif message.text == 'РТбо2-21':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s38'))

    elif message.text == 'РТбо2-31':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s39'))

    elif message.text == 'РТбо2-41':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s40'))

    elif message.text == 'РТбо2-61':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s41'))

    elif message.text == 'РТбо2-71':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s42'))

    elif message.text == 'РТбо2-81':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s43'))

    elif message.text == 'РТбо2-91':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s44'))

    elif message.text == 'РТмо2-11':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s45'))

    elif message.text == 'РТмо2-21':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s46'))

    elif message.text == 'РТмо2-31':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s47'))

    elif message.text == 'РТмо2-41':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s48'))

    elif message.text == 'РТмо2-51':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s49'))

    elif message.text == 'РТмо2-61':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s50'))

    elif message.text == 'РТмо2-71':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s51'))

    elif message.text == 'РТмо2-81':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s52'))

    elif message.text == 'РТсо2-11':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s53'))

    elif message.text == 'РТсо2-21':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s54'))

    elif message.text == 'РТсо2-41':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s55'))

    elif message.text == 'РТсо2-51':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s56'))

    elif message.text == 'РТсо2-61':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s57'))
    else:
        mess = "Такой группы не существует!"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    opp = types.KeyboardButton('Возможности')
    markup.add(opp)
    bot.send_message(message.chat.id, mess, parse_mode='html', reply_markup=markup)


def third_course(message):
    if message.text == 'РТао3-10':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s58'))

    elif message.text == 'РТао3-20':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s59'))

    elif message.text == 'РТао3-30':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s60'))

    elif message.text == 'РТао3-40':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s61'))

    elif message.text == 'РТбо3-10':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s62'))

    elif message.text == 'РТбо3-20':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s63'))

    elif message.text == 'РТбо3-30':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s64'))

    elif message.text == 'РТбо3-40':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s65'))

    elif message.text == 'РТбо3-60':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s66'))

    elif message.text == 'РТбо3-70':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s67'))

    elif message.text == 'РТбо3-80':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s68'))

    elif message.text == 'РТсо3-10':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s69'))

    elif message.text == 'РТсо3-20':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s70'))

    elif message.text == 'РТсо3-30':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s71'))

    elif message.text == 'РТсо3-40':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s72'))

    elif message.text == 'РТсо3-50':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s73'))

    elif message.text == 'РТсо3-60':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s74'))
    else:
        mess = "Такой группы не существует!"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    opp = types.KeyboardButton('Возможности')
    markup.add(opp)
    bot.send_message(message.chat.id, mess, parse_mode='html', reply_markup=markup)


def fourth_course(message):
    if message.text == 'РТао4-19':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s75'))

    elif message.text == 'РТао4-29':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s76'))

    elif message.text == 'РТао4-39':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s77'))

    elif message.text == 'РТао4-49':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s78'))

    elif message.text == 'РТбо4-19':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s79'))

    elif message.text == 'РТбо4-39':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s80'))

    elif message.text == 'РТбо4-59':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s81'))

    elif message.text == 'РТбо4-69':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s82'))

    elif message.text == 'РТбо4-79':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s83'))

    elif message.text == 'РТбо4-89':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s84'))

    elif message.text == 'РТбо4-99':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s85'))

    elif message.text == 'РТсо4-19':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s86'))

    elif message.text == 'РТсо4-29':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s87'))

    elif message.text == 'РТсо4-39':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s88'))

    elif message.text == 'РТсо4-49':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s89'))

    elif message.text == 'РТсо4-59':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s90'))

    elif message.text == 'РТсо4-69':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s91'))
    else:
        mess = "Такой группы не существует!"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    opp = types.KeyboardButton('Возможности')
    markup.add(opp)
    bot.send_message(message.chat.id, mess, parse_mode='html', reply_markup=markup)


def fifth_course(message):
    if message.text == 'РТсо5-18':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s92'))

    elif message.text == 'РТсо5-28':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s93'))

    elif message.text == 'РТсо5-48':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s94'))

    elif message.text == 'РТсо5-68':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s95'))
    else:
        mess = "Такой группы не существует!"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    opp = types.KeyboardButton('Возможности')
    markup.add(opp)
    bot.send_message(message.chat.id, mess, parse_mode='html', reply_markup=markup)


def sixth_course(message):
    if message.text == 'РТсо6-57':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s96'))

    elif message.text == 'ДПО':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s97'))

    elif message.text == 'Лицей 4':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s98'))

    elif message.text == 'РТ-И':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s99'))

    elif message.text == 'Инженер. школа':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s100'))

    elif message.text == 'Инженер.шк.2':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s101'))

    elif message.text == 'М-12':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s102'))

    elif message.text == 'М-22':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s103'))

    elif message.text == 'М-32':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s104'))

    elif message.text == 'Т-12':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s105'))

    elif message.text == 'М-11':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s106'))

    elif message.text == 'М-21':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s107'))

    elif message.text == 'М-31':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s108'))

    elif message.text == 'М-10':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s109'))

    elif message.text == 'М-30':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s110'))

    elif message.text == 'М-19':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s111'))

    elif message.text == 'М-29':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s112'))

    elif message.text == 'САУ-1':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s113'))

    elif message.text == 'САУ-2':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s114'))

    elif message.text == 'САУ-3':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s115'))

    elif message.text == 'Циф.каф.':
        mess = pars_irtsu(site_irtsu('https://rtf.sfedu.ru/raspis/?s116'))
    else:
        mess = "Такой группы не существует!"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    opp = types.KeyboardButton('Возможности')
    markup.add(opp)
    bot.send_message(message.chat.id, mess, parse_mode='html', reply_markup=markup)


def first_course_iuas(message):
    if message.text == 'УЭмо1-6':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/1.html'))

    elif message.text == 'УЭмо1-5':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/2.html'))

    elif message.text == 'УЭмо1-4':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/3.html'))

    elif message.text == 'УЭмв1-2':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/4.html'))

    elif message.text == 'УЭбо1-4':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/5.html'))

    elif message.text == 'УЭбо1-3':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/6.html'))

    elif message.text == 'УЭбо1-2':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/7.html'))

    elif message.text == 'УЭсо1-5':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/8.html'))

    elif message.text == 'УЭсо1-6 (1п.)':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/9.html'))

    elif message.text == 'УЭсо1-6 (2п.)':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/10.html'))

    elif message.text == 'УЭсо1-16 (1п.)':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/11.html'))

    elif message.text == 'УЭсо1-16 (2п.)':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/12.html'))

    elif message.text == 'УЭмз1-5':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/13.html'))

    else:
        mess = "Такой группы не существует!"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    opp = types.KeyboardButton('Возможности')
    markup.add(opp)
    bot.send_message(message.chat.id, mess, parse_mode='html', reply_markup=markup)


def second_course_iuas(message):
    if message.text == 'УЭмо2-7':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/14.html'))

    elif message.text == 'УЭмо2-6':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/15.html'))

    elif message.text == 'УЭмо2-5':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/16.html'))

    elif message.text == 'УЭмв2-1':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/17.html'))

    elif message.text == 'УЭмз2-5':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/18.html'))

    elif message.text == 'УЭбо2-4':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/19.html'))

    elif message.text == 'УЭбо2-3':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/20.html'))

    elif message.text == 'УЭбо2-2':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/21.html'))

    elif message.text == 'УЭсо2-5':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/22.html'))

    elif message.text == 'УЭсо2-16':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/23.html'))

    elif message.text == 'УЭсо2-6 (2п.)':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/24.html'))

    elif message.text == 'УЭсо2-6 (1п.)':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/25.html'))

    else:
        mess = "Такой группы не существует!"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    opp = types.KeyboardButton('Возможности')
    markup.add(opp)
    bot.send_message(message.chat.id, mess, parse_mode='html', reply_markup=markup)


def third_course_iuas(message):
    if message.text == 'УЭбо3-4':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/26.html'))

    elif message.text == 'УЭбо3-3':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/27.html'))

    elif message.text == 'УЭбо3-2':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/28.html'))

    elif message.text == 'УЭсо3-5':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/29.html'))

    elif message.text == 'УЭсо3-6 (1п.)':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/30.html'))

    elif message.text == 'УЭсо3-6 (2п.)':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/31.html'))

    elif message.text == 'УЭсо3-6 (3п.)':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/32.html'))

    elif message.text == 'УЭмз3-5':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/33.html'))

    elif message.text == 'УЭмв3-4':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/34.html'))

    else:
        mess = "Такой группы не существует!"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    opp = types.KeyboardButton('Возможности')
    markup.add(opp)
    bot.send_message(message.chat.id, mess, parse_mode='html', reply_markup=markup)


def fourth_course_iuas(message):
    if message.text == 'УЭбо4-4':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/35.html'))

    elif message.text == 'УЭбо4-3':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/36.html'))

    elif message.text == 'УЭсо4-5':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/37.html'))

    elif message.text == 'УЭбз4-2':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/38.html'))

    else:
        mess = "Такой группы не существует!"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    opp = types.KeyboardButton('Возможности')
    markup.add(opp)
    bot.send_message(message.chat.id, mess, parse_mode='html', reply_markup=markup)


def fifth_course_iuas(message):
    if message.text == 'УЭсо5-5':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/39.html'))

    elif message.text == 'УЭсо5-6 (1п.)':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/40.html'))

    elif message.text == 'УЭсо5-6 (2п.)':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/41.html'))

    elif message.text == 'УЭсо5-6 (3п.)':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/42.html'))

    else:
        mess = "Такой группы не существует!"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    opp = types.KeyboardButton('Возможности')
    markup.add(opp)
    bot.send_message(message.chat.id, mess, parse_mode='html', reply_markup=markup)


def school_iuas(message):
    if message.text == '9 класс (1п.)':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/43.html'))

    elif message.text == '10 класс (1п.)':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/44.html'))

    elif message.text == '11 класс (1п.)':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/45.html'))

    elif message.text == '11 класс (2п.)':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/46.html'))

    elif message.text == '11 класс (3п.)':
        mess = pars_iuas(site_iuas('https://iues.sfedu.ru/raspv/HTML/47.html'))

    else:
        mess = "Такой группы не существует!"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    opp = types.KeyboardButton('Возможности')
    markup.add(opp)
    bot.send_message(message.chat.id, mess, parse_mode='html', reply_markup=markup)


###################################################################################################################
@bot.message_handler(commands=['addremind'])
def reminder_message(message):
    if not check_autorized(message):
        return
    bot.send_message(message.chat.id, 'Введите название напоминания:')
    bot.register_next_step_handler(message, set_reminder_name)


def set_reminder_name(message, tmp=''):
    user_data = {}
    if tmp != '':
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
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            opp = types.KeyboardButton('Возможности')
            markup.add(opp)
            reminder_name = user_data[message.chat.id]['reminder_name']
            bot.send_message(message.chat.id,
                             f'Напоминание "<b>{reminder_name}</b>" установлено на <u>{reminder_time}</u>',
                             parse_mode='html', reply_markup=markup)
            reminder_timer = threading.Timer(delta.total_seconds(), send_reminder, [message.chat.id, reminder_name])
            reminder_timer.start()
    except ValueError:
        bot.send_message(message.chat.id, 'Вы ввели неверный формат даты и времени, попробуйте ещё раз')
        set_reminder_name(message, user_data[message.chat.id]['reminder_name'])


def send_reminder(chat_id, reminder_name):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    opp = types.KeyboardButton('Возможности')
    markup.add(opp)
    bot.send_message(chat_id, f'Напоминание:\n{reminder_name}!', parse_mode='html', reply_markup=markup)
#################################################################################################################
@bot.message_handler(commands=['suggestions'])
def reminder_message(message):
    if not check_autorized(message):
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    opp = types.KeyboardButton('Возможности')
    markup.add(opp)
    bot.send_message(message.chat.id, 'Напишите вашу идею или предложение 1 сообщением, при необходимости мы с вами свяжемся', reply_markup=markup)
    bot.register_next_step_handler(message, suggestions)
def suggestions(message):
    bot.send_message(753990423,str(message.chat.id) + "\n"+
                     message.text)

    bot.send_message(message.chat.id,
                     'Спасибо за обратную связь!')

#################################################################################################################
@bot.message_handler(commands=['contacts'])
def reminder_message(message):
    if not check_autorized(message):
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    opp = types.KeyboardButton('Возможности')
    markup.add(opp)
    bot.send_message(message.chat.id, 'Наши контакты: \n <b>Давид</b> - \n https://vk.com/davidbazhenov \n <b>Иван</b> - \n https://vk.com/prettyjem', parse_mode='html', reply_markup=markup)

#################################################################################################################
@bot.message_handler(commands=['whoami'])
def reminder_message(message):
    if not check_autorized(message):
        return
    user = user_dict[message.chat.id]
    bot.send_message(message.chat.id, f'Ваше имя: <b>{user.name}</b> \nВаш вуз: <b>{user.Uni}</b>', parse_mode='html')

#################################################################################################################
@bot.message_handler()
def get_user_text(message):
    if not check_autorized(message):
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    opp = types.KeyboardButton('Возможности')
    markup.add(opp)
    if message.text == 'Возможности':
        mess_opp = f'Узнать расписание - <b>/schedule</b>\nДобавить напоминание - <b>/addremind</b>' \
                   f' \n Создать новый диалог Chat GPT - <b>/gpt_new_dialog</b>\nИдеи и предложения для бота - ' \
                   f'<b>/suggestions</b>\nКонтакты разработчиков - <b>/contacts</b>\nИнформация о вас - <b>/whoami</b>'
        bot.send_message(message.chat.id, mess_opp, parse_mode='html')
    else:
        err_mess = 'Я тебя не понимаю'
        bot.send_message(message.chat.id, err_mess, reply_markup=markup)


#################################################################################################################
def check_autorized(message):
    if message.chat.id not in user_dict:
        tmp = False
        users_ref = db.collection(u'Users')
        docs = users_ref.stream()
        for doc in docs:
            if doc.id == str(message.chat.id):
                tmp = True
                user = User(doc.to_dict()["Name"])
                user.Uni = doc.to_dict()["Uni"]
                user.isActive = True
                user_dict[message.chat.id] = user
        if tmp:
            return True
        else:
            bot.send_message(message.chat.id, "Вы не зарегистрированы! \nИспользуйте команду <b>/start</b>",
                             parse_mode='html')
            return False
    else:
        return True


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
