import logging


from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import time
from datetime import datetime, timedelta


from shop import inspector_phrases
from config import BOT_TOKEN
from shop import animals, food, EVENTS
import asyncio
import os
import csv
import random
import sqlite3

animals = animals  # словарь с животными
food = food  # словарь с кормом

players = {}  # словарь с пользователями

INCOME_TIMER = 1 * 60 # периодичность дохода в секундах
PRICE_EFFECT = 0.03  # базовое влияние цены билета на посетителей
ANIMALS_PER_PAGE = 5  # сколько кнопок с животными выводится на странице зоомагазина

FEEDING_INTERVAL = 20 * 60  # интервал кормления (В СЕКУНДАХ!)
INSPECTION_INTERVAL = 10 * 60  # интервал проверки инспектором (В СЕКУНДАХ)

MAX_WARNINGS = 3
RANDOM_EVENTS_INTERVAL = 60  # интервал случайных событий (В СЕКУНДАХ)

"""ДОБАВИТЬ

*Справочник по репутации /reputation
"""

"""ИЗМЕНИТЬ
*Время кормления и визита Инспектора на почасовое (!ПРОТЕСТИРОВАТЬ!)

"""

"""Доп.функции
*СЛУЧАЙНЫЕ СОБЫТИЯ☑️
*РАСШИРЕНИЕ ЗООПАРКА (+ лимит животных) 
*ПЕРСОНАЛ
*СИСТЕМА УРОВНЕЙ
"""




#  настройки базы данных
CSV_FILE = 'zoo_data.csv'
DEFAULT_PLAYER = {
    'money': 100,
    'ticket_price': 10,
    'feed': 10,
    'animals': {'кот': 1},
    'last_income': datetime.now().isoformat(),
    'last_fed': datetime.now().isoformat(),
    'warnings': 0,
    'reputation': 100,
    'optimal_price': 30,
    'base_visitors': 30,
    'max_animals': 5  #  максимум животных одного вида
}

###################

def get_db():
    conn = sqlite3.connect('zoo_bot.db')
    conn.row_factory = sqlite3.Row
    return conn


"""СОЗДАНИЕ DB"""  #  на случай удаления старой
def init_db():
    with get_db() as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            money INTEGER DEFAULT 100,
            ticket_price INTEGER DEFAULT 10,
            feed INTEGER DEFAULT 10,
            animals TEXT DEFAULT '{"кот": 1}',
            last_income TEXT DEFAULT CURRENT_TIMESTAMP,
            last_fed TEXT DEFAULT CURRENT_TIMESTAMP,
            warnings INTEGER DEFAULT 0,
            reputation INTEGER DEFAULT 100,
            optimal_price INTEGER DEFAULT 30,
            base_visitors INTEGER DEFAULT 30,
            max_animals INTEGER DEFAULT 5
        )
        """)


"""СОХРАНЕНИЕ ДАННЫХ ИГРОКА"""
def save_player(user_id, player_data):

    with get_db() as db:

        animals_str = str(player_data['animals'])

        db.execute("""
        INSERT OR REPLACE INTO players 
        (user_id, money, ticket_price, feed, animals, last_income, 
         last_fed, warnings, reputation, optimal_price, base_visitors, max_animals)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            player_data['money'],
            player_data['ticket_price'],
            player_data['feed'],
            animals_str,
            player_data['last_income'],
            player_data['last_fed'],
            player_data['warnings'],
            player_data['reputation'],
            player_data['optimal_price'],
            player_data['base_visitors'],
            player_data['max_animals']
        ))


"""ЗАГРУЗКА ДАННЫХ"""
def load_player(user_id):

    with get_db() as db:
        player = db.execute(
            "SELECT * FROM players WHERE user_id = ?",
            (user_id,)
        ).fetchone()

    if player:

        player_dict = dict(player)
        player_dict['animals'] = eval(player['animals'])
        return player_dict
    return None


"""СПИСОК ВСЕХ ИГРОКОВ"""
def get_all_players():

    with get_db() as db:
        players = db.execute("SELECT * FROM players").fetchall()

    return {
        row['user_id']: {
            **dict(row),
            'animals': eval(row['animals'])
        }
        for row in players
    }

# создание db
init_db()


"""НАЧАЛО ИГРЫ"""
async def start(update, context):
    user_id = update.effective_user.id  # айди пользователя

    player = load_player(user_id)
    if not player:
        player = DEFAULT_PLAYER.copy()
        save_player(user_id, player)

    await update.message.reply_text(
        "🐾 Добро пожаловать в ваш зоопарк!\n"
        "🐱 У вас есть кот - ваш первый питомец.\n\n"

        "📌 Основные правила:\n"
        "- Устанавливайте цену на билеты (/price)\n"
        "- Посетители приносят доход каждую минуту\n"
        "- Покупайте корм и новых животных в зоомаркете (/shop)\n"
        "- Кормите животных регулярно (/feed)\n\n"
        "⚠️ Если не кормить животных, придет инспектор!\n\n"
        "Используйте /status для просмотра состояния зоопарка"
    )


"""ПОМОЩЬ ПО КОМАНДАМ"""


async def post_init(application):
    await application.bot.set_my_commands([
        ("start", "Начать игру"),
        ("status", "Статус зоопарка"),
        ("price", "Изменить цену билета"),
        ("shop", "Магазин животных и корма"),
        ("feed", "Покормить животных"),
        ("help", "Помощь по командам")
    ])


"""РАСЧЕТ ПОСЕТИТЕЛЕЙ"""


def calculate_visitors(player):
    animals_multiplier = sum(
        animals[key]['visitor_multiplier'] * value
        for key, value in player['animals'].items()
    )  # сложение множителей всех животных

    optimal_price = player['optimal_price'] + player['reputation'] / 10  # оптимальная цена

    ticket_price = player['ticket_price']

    price_impact = max(0, 1 - (ticket_price / optimal_price))

    visitors = int(player['base_visitors'] * animals_multiplier * price_impact)

    print(f"Price Impact: {price_impact}, Visitors: {visitors}")

    return visitors


"""УСТАНОВКА ЦЕНЫ НА БИЛЕТ"""


async def set_price(update, context):
    try:

        try:
            new_price = int(context.args[0])
            if new_price < 10:
                await update.message.reply_text("⚠️Цена на билет не может быть ниже 10 монет!")
                return
        except (IndexError, ValueError):  # если игрок не ввел число
            await update.message.reply_text(
                "🎫Вы можете установить новую цену на билеты.\n\n"
                "Использование: /price <новая цена>\n"
                "Например: /price 50\n\n"
                "👥Цена билета напрямую влияет на посетителей!\n"
                "💵Минимальная допустимая цена - 10 монет"

            )
            return

        user_id = update.effective_user.id
        player = load_player(user_id)

        player['ticket_price'] = new_price
        save_player(user_id, player)

        visitors = calculate_visitors(player)  # приток посетителей
        income_per_minute = visitors * new_price  # заработок в минуту

        await update.message.reply_text(
            f"🎫 Цена билета обновлена: {new_price}\n\n"
            f"📊 Прогноз посещаемости:\n"
            f"👥 Посетителей в минуту: {visitors}\n"
            f"💰 Доход в минуту: {income_per_minute}"
        )

        if visitors == 0:
            await update.message.reply_text(
                f"⚠️ВНИМАНИЕ⚠️\n"
                f"👥 Кажется у вашего зоопарка нет посетителей!\n\n"
                f"💵Попробуйте снизить цену на билеты и найти наиболее выгодную."
            )

    except Exception as e:
        await update.message.reply_text(
            f"Произошла ошибка в блоке set_price\n{e}"
        )



"""СТАТУС ЗООПАРКА"""


async def status(update, context):

    user_id = update.effective_user.id
    player = load_player(user_id)

    animals_list = "\n".join(
        f"{animals[key]['emoji']} {key.capitalize()}: {value} шт. (корм: {animals[key]['feed_cost'] * value}/день)"
        for key, value in player['animals'].items() if value > 0
    )  # список животных

    now = datetime.now()
    visitors = calculate_visitors(player)
    income = visitors * player['ticket_price']


    #  ПОСЛЕДНЕЕ КОРМЛЕНИЕ
    last_fed = datetime.fromisoformat(player['last_fed'])
    now = datetime.now()
    time_since_fed = now - last_fed

    hours = time_since_fed.total_seconds() // 3600
    minutes = (time_since_fed.seconds % 3600) // 60

    print(f'с последнего кормления прошло {minutes} минут')


    #СТАТУС ЖИВОТНЫХ
    status = []
    if minutes <= FEEDING_INTERVAL // 60 // 2:
        status = ['сыты', '🟢']
    elif minutes > FEEDING_INTERVAL // 60 // 2 and minutes < FEEDING_INTERVAL // 60:
        status = ['голодны', '🟡']
    else:
        status = ['очень голодны', '🔴']

    await update.message.reply_text(
        f"🏠 Ваш зоопарк:\n\n"
        f"💰 Баланс: {player['money']}\n"
        f"🌟 Репутация зоопарка: {player['reputation']}\n"
        f"🎫 Цена билета: {player['ticket_price']}\n"
        f"👥 Посетителей/мин: ~{visitors}\n"
        f"💵 Доход/мин: ~{income}\n"
        f"🌾 Корма: {player['feed']}\n\n"
        f"🐾 Ваши животные:\n{animals_list}\n\n"
        f"⏳ Последнее кормление: {minutes} мин. назад\n"
        f"{status[-1]} Ваши животные {status[0]}\n\n"
        f"⚠️ Предупреждения: {player['warnings']}"
    )


"""ЕЖЕМИНУТНЫЙ ДОХОД"""


async def process_income(context):
    players = get_all_players()
    for user_id, player in players.items():
        now = datetime.now().isoformat()
        income = player['ticket_price'] * calculate_visitors(player)
        print(f'visitors: {calculate_visitors(player)}')

        updated_player = player.copy()
        updated_player['money'] += int(income)
        updated_player['last_income'] = now

        #await context.bot.send_message(
           #chat_id=user_id,
            #text=f"‼️ТЕСТОВОЕ СООБЩЕНИЕ‼️\n + {income} монет"
        #)

        save_player(user_id, updated_player)


"""МАГАЗИН (МЕНЮ ВЫБОРА)"""


async def shop(update, context):
    keyboard = shop_keyboard()

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🏪 Добро пожаловать в зоомаркет!", reply_markup=reply_markup)


def shop_keyboard():
    keyboard = [
        [InlineKeyboardButton("🌾 Купить корм", callback_data='buy_feed')],
        [InlineKeyboardButton("🐾 Купить животных", callback_data='buy_animals')],
    ]
    return keyboard


"ЖИВОТНЫЕ ДЛЯ ПОКУПКИ"


def animals_keyboard(page=0):
    animal_keys = list(animals.keys())  # список с видами животных

    start_idx = page * ANIMALS_PER_PAGE
    end_idx = start_idx + ANIMALS_PER_PAGE

    current_animals = animal_keys[start_idx:end_idx]

    keyboard = []

    for animal in current_animals:
        emoji = animals[animal]['emoji']
        price = animals[animal]['price']
        keyboard.append([InlineKeyboardButton(
            f"{emoji} {animal.capitalize()} - {price}$",
            callback_data=f'animal_{animal}'
        )])

    nav_buttons = []  # кнопки навигации
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f'animals_page_{page - 1}'))
    if end_idx < len(animal_keys):
        nav_buttons.append(InlineKeyboardButton("Далее ➡️", callback_data=f'animals_page_{page + 1}'))

    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_shop')])

    return keyboard


"""ОБРАБОТКА НАЖАТИЙ КНОПКИ"""


async def shop_button_handler(update, context):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    player = load_player(user_id)

    """ПОДТВЕРЖДЕНИЕ ПОКУПКИ ЕДЫ"""
    if query.data == 'buy_feed':

        keyboard = [
            [InlineKeyboardButton("⬅️ Вернуться к выбору", callback_data='back_to_shop')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        context.user_data['awaiting_feed_quantity'] = True
        food_price = food['корм']['price']

        await query.edit_message_text(
            "🌾 Введите количество корма для покупки.\n\n"
            f"💵 Стоимость единицы корма: {food_price} монет.\n\n"
            f"💰 Ваш баланс: {player['money']}$",
            reply_markup=reply_markup
        )
        return

    elif query.data == 'confirm_feed':
        purchase = context.user_data.get('purchase_data')

        if not purchase:
            await query.edit_message_text("❌ Данные покупки устарели")
            return

        if player['money'] >= purchase['total_price']:
            player['money'] -= purchase['total_price']
            print(player['feed'])
            print(purchase['quantity'])
            player['feed'] += purchase['quantity']
            print(player['feed'])
            save_player(user_id, player)

            await query.edit_message_text(
                f"✅ Покупка завершена!\n\n"
                f"🌾 +{purchase['quantity']} корма\n"
                f"💸 -{purchase['total_price']} монет\n"
                f"💰 Остаток: {player['money']} монет"
                f"u vas {player['feed']}"
            )
            await asyncio.sleep(1)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🏪 Чтобы продолжить покупки используйте /shop"
            )
            await asyncio.sleep(1)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="🐾 Чтобы просмотреть статус зоопарка используйте /status"
            )


        else:
            need = purchase['total_price'] - player['money']
            await query.edit_message_text(
                f"❌ Недостаточно денег!\n"
                f"Необходимо {need} монет."
            )


    elif query.data == 'back_to_shop':
        context.user_data.pop('awaiting_feed_quantity', None)
        context.user_data.pop('purchase_data', None)
        await query.edit_message_text(
            text="🏪 Добро пожаловать в зоомаркет!",
            reply_markup=InlineKeyboardMarkup(shop_keyboard())
        )


    elif query.data == 'cancel_feed':
        await query.edit_message_text("❌ Покупка отменена")

    """ПОДТВЕРЖДЕНИЕ ПОКУПКИ ЖИВОТНЫХ"""
    if query.data == 'buy_animal':

        keyboard = [
            [InlineKeyboardButton("⬅️ Вернуться к выбору", callback_data='back_to_shop')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        context.user_data['awaiting_feed_quantity'] = True

        animal_name = context.user_data['selected_animal']
        animal_data = animals.get(animal_name)

        await query.edit_message_text(
            f"🛒 Вы выбрали: {animal_data['emoji']} {animal_name.capitalize()}\n"
            f"🐾 У вас имеется {player[animal_name.capitalize()]}/{player['max_animals']}\n\n"
            f"⭐ Минимальная репутация для покупки: {animal_data['min_rep']}\n"
            f"💵 Цена: {animal_data['price']}$\n"
            f"👥 Привлекает посетителей: +{animal_data['visitor_multiplier']}\n"
            f"🍗 Расход корма: {animal_data['feed_cost']}/день\n\n"
            f"💰 Ваш баланс: {player['money']}$\n"
            f"🌟 Ваша репутация: {player['reputation']}\n\n"
            
            "Введите количество для покупки",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад к списку", callback_data='buy_animals')]
            ])
        )


    #ПОДТВЕРЖДЕНИЕ ПОКУПКИ ЖИВОТНЫХ
    elif query.data == 'confirm_animal':
        purchase = context.user_data.get('purchase_data')

        if not purchase:
            await query.edit_message_text("❌ Данные покупки устарели")
            return

        animal_name = context.user_data['selected_animal']
        to_buy = player['animals'].get(animal_name, 0) + purchase['quantity'] # сколько животных после покупки

        print(f'репутация игрока {player['reputation']}')
        print(f'необходимая репутация {animals[purchase['animal']]['min_rep']}')

        if player['reputation'] < animals[purchase['animal']]['min_rep']:

            need_rep = animals[purchase['animal']]['min_rep'] - player['reputation']
            await query.edit_message_text(
                f"❕ У вашего зоопарка низкая репутация ❕\n\n"
                f"🌟 Текущая репутация: {player['reputation']}\n"
                f"⭐ Необходимая репутация: {animals[purchase['animal']]['min_rep']}\n"
                f"📉 Нужно ещё {need_rep} очков репутации.\n\n"
                f"📄 Чтобы узнать, как повысить репутацию используйте /reputation"

            )
            return


        elif to_buy >= player['max_animals']: # если достигнут лимит животных
            available = max([player['max_animals'] - player['animals'][animal_name], 0])
            emoji = animals[animal_name]['emoji']

            await query.edit_message_text(
                f"❕ Вы превысили лимит животных ❕\n\n"
                f"{emoji} У вас: {player['animals'][animal_name]}/{player['max_animals']}\n"
                f"🛒 Выбрано для покупки: {purchase['quantity']}\n"
                f"☑️ Доступно для покупки: {available}"

            )
            return

        if player['money'] >= purchase['total_price']:  # если достаточно денег
            player['money'] -= purchase['total_price']

            if animal_name in player['animals']:
                player['animals'][animal_name] += purchase['quantity']
            else:
                player['animals'][animal_name] = purchase['quantity']

            save_player(user_id, player)

            await query.edit_message_text(
                f"✅ Покупка завершена!\n\n"
                f"{animals[animal_name]['emoji']} +{purchase['quantity']} {animal_name.capitalize()}\n"
                f"💸 -{purchase['total_price']} монет\n"
                f"💰 Остаток: {player['money']} монет\n\n"
                f"🏪 Чтобы продолжить покупки используйте /shop\n"
                f"🐾 Чтобы просмотреть статус зоопарка используйте /status"
            )


        else:
            need = purchase['total_price'] - player['money']
            await query.edit_message_text(
                f"❌ Недостаточно денег!\n"
                f"Необходимо ещё {need} монет."
            )

    elif query.data == 'back_to_shop':
        context.user_data.pop('awaiting_feed_quantity', None)
        context.user_data.pop('purchase_data', None)
        await query.edit_message_text(
            text="🏪 Добро пожаловать в зоомаркет!",
            reply_markup=InlineKeyboardMarkup(shop_keyboard())
        )


    elif query.data == 'cancel_feed' or query.data == 'cancel_animal':
        await query.edit_message_text("❌ Покупка отменена")

    context.user_data.pop('awaiting_feed_quantity', None)
    context.user_data.pop('purchase_data', None)

    # магазин животных
    if query.data == 'buy_animals':
        await query.edit_message_text(
            "🐾 Выберите животное для покупки:",
            reply_markup=InlineKeyboardMarkup(animals_keyboard())
        )
        return

    # переключение страниц с животными
    elif query.data.startswith('animals_page_'):
        page = int(query.data.split('_')[2])
        await query.edit_message_text(
            "🐾 Выберите животное для покупки:",
            reply_markup=InlineKeyboardMarkup(animals_keyboard(page))
        )
        return

    # выбор конкретного животного
    elif query.data.startswith('animal_'):
        animal = query.data.split('_', 1)[1]
        animal_data = animals.get(animal)

        if not animal_data:
            await query.edit_message_text("❌ Животное не найдено!\n Ошибка в блоке shop_button_handler")
            return

        context.user_data['selected_animal'] = animal
        await query.edit_message_text(
            f"🛒 Вы выбрали: {animal_data['emoji']} {animal.capitalize()}\n"
            f"🐾 У вас имеется: {player['animals'].get(animal, 0)}/{player['max_animals']}\n\n"
            f"⭐ Минимальная репутация для покупки: {animal_data['min_rep']}\n"
            f"💵 Цена: {animal_data['price']}$\n"
            f"👥 Множитель посещений: +{animal_data['visitor_multiplier']}\n"
            f"🍗 Расход корма: {animal_data['feed_cost']}/день\n\n"
            f"💰 Ваш баланс: {player['money']}$\n"
            f"🌟 Ваша репутация: {player['reputation']}\n\n"

            "Введите количество для покупки",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад к списку", callback_data='buy_animals')]
            ])
        )
    context.user_data['awaiting_animal_quantity'] = True  # флаг (ожидание ввода количества покупаемых животных)
    return


"""ОБРАБОТЧИК ТЕКСТА"""  # покупки


async def handle_input(update, context):
    query = update.callback_query

    user_id = update.effective_user.id
    player = load_player(user_id)

    if context.user_data.get('awaiting_feed_quantity'):  # если режим покупки корма

        try:
            quantity = int(update.message.text)
            if quantity <= 0:
                raise ValueError

            total_price = quantity * food['корм']['price']

            context.user_data['purchase_data'] = {
                'quantity': quantity,
                'total_price': total_price
            }

            keyboard = [
                [InlineKeyboardButton("✅ Подтвердить", callback_data='confirm_feed')],
                [InlineKeyboardButton("↩️ Назад", callback_data='buy_feed')],
                [InlineKeyboardButton("❌ Отменить", callback_data='cancel_feed')]
            ]

            await update.message.reply_text(
                f"🛒 Подтвердите покупку:\n\n"
                f"🌾 Количество: {quantity}\n"
                f"💵 Стоимость: {context.user_data['purchase_data']['total_price']}$\n"
                f"💰 Ваш баланс: {player['money']}$",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except ValueError:
            await update.message.reply_text("⚠️ Введите целое число больше 0!")


    elif context.user_data.get('awaiting_animal_quantity'):
        try:

            quantity = int(update.message.text)
            if quantity <= 0:
                raise ValueError

            animal_name = context.user_data['selected_animal']
            animal_data = animals.get(animal_name)
            print(animal_data)

            total_price = quantity * animal_data['price']

            keyboard = [
                [InlineKeyboardButton("✅ Подтвердить", callback_data='confirm_animal')],
                [InlineKeyboardButton("↩️ Назад", callback_data='buy_animal')],
                [InlineKeyboardButton("❌ Отменить", callback_data='cancel_animal')]
            ]

            context.user_data['purchase_data'] = {
                'quantity': quantity,
                'total_price': total_price,
                'animal': animal_name
            }

            await update.message.reply_text(
                f"🛒 Подтвердите покупку:\n\n"
                f"{animal_data['emoji']} Количество: {quantity}\n"
                f"💵 Стоимость: {context.user_data['purchase_data']['total_price']}$\n"
                f"💰 Ваш баланс: {player['money']}$",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except ValueError:
            await update.message.reply_text("⚠️ Введите целое число больше 0!")


"""КОРМЛЕНИЕ ЖИВОТНЫХ"""


async def feed(update, context):

    user_id = update.effective_user.id
    player = load_player(user_id)

    now = datetime.now()

    total_feed_cost = sum(
        animals[animal]['feed_cost'] * count
        for animal, count in player['animals'].items()
    )  # общая стоимость

    if player['feed'] < total_feed_cost:
        await update.message.reply_text(
            f"❌ Не хватает корма!\n"
            f"Нужно: {total_feed_cost} 🌾\n"
            f"Имеется: {player['feed']} 🌾\n"
            f"Необходимо еще {total_feed_cost - player['feed']} ед. корма"
        )
        return

    last_fed = datetime.fromisoformat(player['last_fed'])
    now = datetime.now()
    time_since_fed = now - last_fed
    FEEDING_INTERVAL - time_since_fed.total_seconds()


    if time_since_fed.total_seconds() < FEEDING_INTERVAL // 2:  #  если с последнего кормления прошло недостаточно времени

        time_left = (FEEDING_INTERVAL // 2) - time_since_fed.total_seconds()
        minutes_left = int(time_left // 60)

        await update.message.reply_text(
            f"🍽️ Ваши животные сыты!\n"
            f"🌾 Вы сможете покормить их снова через {minutes_left} мин."
        )
        return

    updated_player = player.copy()
    updated_player['last_fed'] = datetime.now().isoformat()
    updated_player['feed'] -= total_feed_cost
    save_player(user_id, updated_player)
    minutes = FEEDING_INTERVAL // 60

    can_feed = max([minutes - (minutes // 2), 0])

    await update.message.reply_text(
        f"🍽️ Животные накормлены!\n"
        f"🌾 Израсходовано корма: {total_feed_cost}\n"
        f"⏰ Последнее кормление: {now.strftime('%H:%M:%S')}\n"
        f"😸 Кормление будет доступно через {can_feed} мин.\n"
        f"⚠️ Осталось времени до голодания: {minutes} мин."
    )


"""ПРОВЕРКА ГОЛОДНЫХ ЖИВОТНЫХ"""


async def check_hunger(context):
    now = datetime.now()
    players = get_all_players()
    for user_id, player in players.items():
        time_since_fed = (now - datetime.fromisoformat(player['last_fed'])).total_seconds()

        #  предупреждение о проверке
        if FEEDING_INTERVAL < time_since_fed:
            time_left = INSPECTION_INTERVAL - time_since_fed  # время до визита инспектора
            if time_left <=  0:
                return
            minutes_left = int(time_left // 60)
            await context.bot.send_message(
                chat_id=user_id,
                text=f"⚠️ Внимание! Животные голодны!\n"
                     f"Инспектор придет через {minutes_left} мин.\n"
                     f"Срочно покормите животных командой /feed"
            )


"""ПРОВЕРКА ИНСПЕКТОРОМ"""


async def inspection(context):

    players = get_all_players()
    now = datetime.now()

    for user_id, player in players.items():

        # ПРЕДУПРЕЖДЕНИЕ О НЕОБХОДИМОСТИ ПОКОРМИТЬ ЖИВОТНЫХ (!!изменить время!!)
        #  ПОСЛЕДНЕЕ КОРМЛЕНИЕ
        last_fed = datetime.fromisoformat(player['last_fed'])
        time_since_fed = (now - last_fed).total_seconds()  #  время с последней кормежки в секундах

        if time_since_fed > FEEDING_INTERVAL // 2: # если животные давно не ели (в случае с кормежкой раз в 10 минут если до голодания осталось 5 минут)
            print(f'Время с последнего кормления {time_since_fed}')
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🥩 Ваши животные давно не ели!\n"
                     f"👮 Вам следует покормить их перед следующим визитом Инспектора.")



        if time_since_fed > FEEDING_INTERVAL:
            player['warnings'] += 1

            minute_income = player['ticket_price'] * calculate_visitors(player)  # ежеминутный доход
            hour_income = minute_income * 60  # доход в час
            mulct = hour_income * player['warnings']  # денежный штраф
            phrase = random.choice(inspector_phrases)  # фраза инспектора
            if player['reputation'] > 10:
                print('репутация > 10')
                rep = 10
                player['reputation'] -= 10  # зоопарк теряет репутацию
            else:
                rep = 0
                player['reputation'] = 0
            await context.bot.send_message(
                chat_id=user_id,
                text=f"{phrase}\n\n"
                     f"⚠️ Получено предупреждений: {player['warnings']}\n"
                     f"📉 Репутация зоопарка: -{rep}\n\n"
                     f"🌟 Текущая репутация зоопарка: {player['reputation']}\n"
                     f"🥩 Срочно покормите животных командой /feed")

        else:

            if player['warnings'] > 0: # если у игрока есть предупреждения
                player['warnings'] -= 1
                if player['reputation'] + 10 <= 100:
                    rep = 10
                    player['reputation'] += 10
                else:
                    rep = 0
                    player['reputation'] = 100

                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"👮 Инспектор посетил ваш зоопарк и остался доволен!\n"
                         f"🌟 Текущая репутация зоопарка: +{rep}\n"
                         f"🕐 Следующий визит через {INCOME_TIMER} секунд!\n"
                         f"😸 Продолжайте кормить животных вовремя, чтобы увеличить репутацию зоопарка!")

            else: # если предупреждений нет
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"👮 Инспектор посетил ваш зоопарк и остался доволен!\n"
                         f"🕐 Следующий визит через {INCOME_TIMER} секунд!\n"
                         f"😸 Продолжайте кормить животных вовремя, чтобы поддерживать репутацию зоопарка!!")


        save_player(user_id, player)


"""СЛУЧАЙНЫЕ СОБЫТИЯ"""
async def random_events(context):
    print('СЛУЧАЙНОЕ СОБЫТИЕ!')
    players = get_all_players()
    for user_id, player in players.items():
        event_name = random.choice(list(EVENTS.keys()))
        event = EVENTS[event_name]
        message = ""


        if event["type"] in ["money", 'food', 'reputation']:
            type = event["type"]
            amount = random.randint(event["min_amount"], event["max_amount"])  # случайное число из диапазона
            if "amount" in event["message"]:
                message = event["message"].format(amount=amount)
                player[type] += amount


        if message:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"{event['emoji']} *Событие!* {event['emoji']}\n{message}"
            )
            save_player(user_id, player)


def main():
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("price", set_price))
    application.add_handler(CommandHandler("shop", shop))
    application.add_handler(CommandHandler("feed", feed))

    application.add_handler(CallbackQueryHandler(shop_button_handler))
    application.add_handler(CallbackQueryHandler(
        shop_button_handler,
        pattern='^(confirm_feed|cancel_feed|buy_feed|back_to_confirm)'
    ))

    #  периодический доход
    job_queue = application.job_queue
    job_queue.run_repeating(
        process_income,
        interval=INCOME_TIMER,
        first=1.0
    )

    # периодическая проверка на голод
    job_queue.run_repeating(
        check_hunger,
        interval=60.0,
        first=0.0
    )

    # периодический визит инспекторы
    job_queue.run_repeating(
        inspection,
        interval=INSPECTION_INTERVAL,
        first=0.0
    )

    # периодические случайные события
    application.job_queue.run_repeating(
        random_events,
        interval=RANDOM_EVENTS_INTERVAL,
        first=0
    )

    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_input
    ))

    application.run_polling()


if __name__ == '__main__':
    main()
