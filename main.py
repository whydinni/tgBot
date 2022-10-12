import sqlite3
import telebot
import requests
from telebot import types

bot = telebot.TeleBot("Вставьте свой токен")
api_key_news='Вставьте свой токен'

conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()

def convertList(news):
    str = ''
    for i in news:
        str += i+"\n"
    return str

@bot.message_handler(commands=['start'])
def send_welcome(message):
    login = message.from_user.id
    try:
        conn = sqlite3.connect('database.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users(login) VALUES(?)', (login,))
        conn.commit()
    except (sqlite3.Error):
        bot.send_message(message.from_user.id, "Добро пожаловать")
    else:
        bot.send_message(message.from_user.id, "Добро пожаловать")
    finally:
        print('fdds')

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    hello = types.KeyboardButton("👋 Поздороваться")
    category = types.KeyboardButton("🔎 Категории")
    sub = types.KeyboardButton("✉ Подписки")
    makesub = types.KeyboardButton("✅ Подписаться")
    unsub = types.KeyboardButton("❌ Отписаться")
    markup.add(hello, category, sub, makesub, unsub)
    bot.send_message(message.chat.id,text="Привет, {0.first_name}! Какие новости хочешь почитать сегодня?".format(message.from_user), reply_markup=markup)


@bot.message_handler(content_types=['text'])
def func(message):
    login = message.from_user.id
    if (message.text == "👋 Поздороваться"):
        bot.send_message(message.chat.id, text="Приветик! Спасибо, что пользуешься этим ботом!)")
    elif (message.text == "🔎 Категории"):
        markup = types.InlineKeyboardMarkup()
        user = conn.execute('''SELECT users.id FROM users WHERE login=?''', (login,)).fetchone()[0]
        sublist = conn.execute('''select categories.id, categories.name from categories
        INNER JOIN subscribes ON categories.id == subscribes.id_category
        INNER JOIN users ON users.id == subscribes.id_user
        where users.id=?
        ''', (user,)).fetchall()
        print(sublist)
        for category in sublist:
            markup.add(types.InlineKeyboardButton(category[1], callback_data=f'category-{category[0]}'))
        bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=markup)

    elif (message.text == "✉ Подписки"):
        user = conn.execute('''SELECT users.id FROM users WHERE login=?''', (login,)).fetchone()[0]
        sublist = conn.execute('''select name from categories
    INNER JOIN subscribes ON categories.id == subscribes.id_category
    INNER JOIN users ON users.id == subscribes.id_user
    where users.id=?
    ''',(user,)).fetchall()
        sublist = [*(x for t in sublist for x in t)]
        bot.send_message(message.chat.id, text=f'Ваши подписки: \n{convertList(sublist)} ')

    elif (message.text == "✅ Подписаться"):
        sub = types.InlineKeyboardMarkup()
        categories = cursor.execute('SELECT id, name FROM categories').fetchall()
        for category in categories:
            sub.add(types.InlineKeyboardButton(category[1], callback_data=f'sub-{category[0]}'))
        bot.send_message(message.chat.id, "На что хотите подписаться?", reply_markup=sub)

    elif (message.text == "❌ Отписаться"):
        unsub = types.InlineKeyboardMarkup()
        user = conn.execute('''SELECT users.id FROM users WHERE login=?''', (login,)).fetchone()[0]
        sublist = conn.execute('''select categories.id, categories.name from categories
        INNER JOIN subscribes ON categories.id == subscribes.id_category
        INNER JOIN users ON users.id == subscribes.id_user
        where users.id=?
        ''', (user,)).fetchall()
        print(sublist, type(sublist))
        for category in sublist:
            unsub.add(types.InlineKeyboardButton(category[1], callback_data=f'unsub-{category[0]}'))
        bot.send_message(message.chat.id, "От чего хотите отписаться?", reply_markup=unsub)


@bot.callback_query_handler(func=lambda call: True)
def category(call):
    command = call.data.split('-')[0]
    data = call.data.split('-')[1]
    cat = conn.execute("SELECT name FROM categories WHERE id = ?", (data,)).fetchone()[0]
    user = call.from_user.id
    if(command == 'category'):
        news = []
        a = requests.get(f'https://newsapi.org/v2/top-headlines?apiKey={api_key_news}&category={cat}&pageSize=3&country=ru')
        for i in a.json()['articles']:
            news.append([i['title'], i['publishedAt'], i['url']])
        answer = ""
        for line in news:
            answer += convertList(line) + "~~~~~~~~~~~~~~~~~~~~~~\n"
        bot.send_message(call.message.chat.id, answer)

    elif (command == 'unsub'):
        proverka = cursor.execute('SELECT login FROM users').fetchall()
        users = []
        for item in proverka:
            users.append(item[0])
        if (str(user) in users):
            proverkatwo = cursor.execute('SELECT name FROM categories').fetchall()
            categories = []
            for item in proverkatwo:
                categories.append(item[0])
            if (cat in categories):
                req = cursor.execute('''SELECT * From subscribes
                            INNER JOIN users ON users.id=id_user
                            INNER JOIN categories ON categories.id=id_category
                            WHERE users.login=? AND categories.name=?''', (user, cat)).fetchone()
                if req is not None:

                    cursor.execute('''DELETE FROM subscribes 
                    WHERE id_user=(SELECT id FROM users WHERE login=?) and
                    id_category=(SELECT id FROM categories WHERE name=?)''', (user, cat))
                    conn.commit()
                    bot.send_message(call.from_user.id, "Вы успешно отписались от категории ")
                    return True
                else:
                    return False
        else:
            print('!!!')

    elif(command == 'sub'):
        proverka = cursor.execute('SELECT login FROM users').fetchall()
        users = []
        for item in proverka:
            users.append(item[0])
        if (str(user) in users):
            proverkatwo = cursor.execute('SELECT name FROM categories').fetchall()
            categories = []
            for item in proverkatwo:
                categories.append(item[0])
            if (cat in categories):
                req=cursor.execute('''SELECT * From subscribes
                    INNER JOIN users ON users.id=id_user
                    INNER JOIN categories ON categories.id=id_category
                    WHERE users.login=? AND categories.name=?''', (user, cat)).fetchone()
                if req is None:

                    cursor.execute('''INSERT INTO subscribes(id_user, id_category) VALUES (
                            (SELECT id FROM users WHERE login=?),
                            (SELECT id FROM categories WHERE name=?)
                            )''', (user, cat))
                    conn.commit()
                    bot.send_message(call.from_user.id, "Вы успешно подписались на категорию ")
                    return True
                else:
                    bot.send_message(call.from_user.id, "Вы уже подписаны")
                    return False
        else:
            print('!!!')

    bot.answer_callback_query(call.id)

try:
    connect = sqlite3.connect('database.db')
    cursor = connect.cursor()
    cursor.execute ("""CREATE TABLE IF NOT EXISTS "users" (
	"id"	INTEGER NOT NULL,
	"login"	TEXT NOT NULL UNIQUE,
	PRIMARY KEY("id" AUTOINCREMENT)
    );""")

    cursor.execute ("""CREATE TABLE IF NOT EXISTS "categories" (
	"id"	INTEGER NOT NULL,
	"name"	TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
    );""")

    cursor.execute ("""CREATE TABLE IF NOT EXISTS "subscribes" (
	"id_user"	INTEGER NOT NULL,
	"id_category"	INTEGER NOT NULL
    );""")
    connect.commit()
except sqlite3.Error as error:
    print('Ошибка', error)
finally:
    # cursor.close()
    print('fdgd')

bot.infinity_polling()
