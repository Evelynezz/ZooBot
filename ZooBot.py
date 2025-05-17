import logging


from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import time
from datetime import datetime, timedelta


from shop import inspector_phrases
from config import BOT_TOKEN
from shop import ANIMALS, FOOD, EVENTS, LEVELS, STAFF, STAFF_NAME_TO_ID
import asyncio
import os
import csv
import random
import sqlite3
import json
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from telegram import ReplyKeyboardMarkup, KeyboardButton


players = {}  # словарь с пользователями

INCOME_TIMER = 1 * 60 # периодичность дохода в секундах
PRICE_EFFECT = 0.03  # базовое влияние цены билета на посетителей
ANIMALS_PER_PAGE = 4  # сколько кнопок с животными выводится на странице зоомагазина

FEEDING_INTERVAL = 60 * 60 * 12 # интервал кормления (В СЕКУНДАХ!) раз в 12 часов
INSPECTION_INTERVAL = 60 * 60 * 4  # интервал проверки инспектором (В СЕКУНДАХ) раз в 4 ч

MAX_WARNINGS = 3 # максимум предупреждений
RANDOM_EVENTS_INTERVAL = 60 * 15 # интервал случайных событий (В СЕКУНДАХ) раз в 15 минут

MAX_LEVEL = 5 # максимальный уровень игрока
SALARY_PERCENT_LIMIT = 30 # лимит на зп сотрудников в %

MULTIPLIER = 1.5 # множитель для формулы (при подсчете стоимости животных)

SALARY_INTERVAL = 60 # интервал зарплаты сотрудникам

STAFF_LIMIT = 3 # Максимальное количество одновременно нанятых сотрудников


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
    'max_animals': 3,  #  максимум животных одного вида
    'features': ['basic_gameplay'], # доступные функции
    'level': 1,
    'xp': 0,
    'staff': [],
    'staff_income_percent': 0 # процент от дохода (зп персонала)

}


Base = declarative_base()
engine = create_engine("sqlite:///zoo_bot.db", echo=False, future=True)
Session = sessionmaker(bind=engine)

inspector_phrases = inspector_phrases
###################


from telegram import ReplyKeyboardMarkup, KeyboardButton

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("🏠 Статус зоопарка "), KeyboardButton("🛒 Магазин")],
        [KeyboardButton("👨‍🔧 Персонал"), KeyboardButton("🌾 Покормить животных")],
        [KeyboardButton("🏆 Топ игроков"),  KeyboardButton("🐘 Спросить слона")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
)


class Player(Base):
    __tablename__ = "players"

    user_id = Column(Integer, primary_key=True)
    money = Column(Integer, default=100)
    ticket_price = Column(Integer, default=10)
    feed = Column(Integer, default=10)
    animals = Column(Text, default=json.dumps({"кот": 1}))
    last_income = Column(Text)
    last_fed = Column(Text)
    warnings = Column(Integer, default=0)
    reputation = Column(Integer, default=100)
    optimal_price = Column(Integer, default=30)
    base_visitors = Column(Integer, default=30)
    max_animals = Column(Integer, default=3)
    level = Column(Integer, default=1)
    xp = Column(Integer, default=0)
    features = Column(Text, default=json.dumps(["basic_gameplay"]))
    staff = Column(Text, default=json.dumps([]))
    staff_income_percent = Column(Integer, default=0)



"""СОЗДАНИЕ DB"""
def init_db():
    Base.metadata.create_all(engine)

"""СОХРАНЕНИЕ ДАННЫХ ИГРОКА"""
def save_player(user_id, player_data):
    session = Session()

    player = session.get(Player, user_id)
    if not player:
        player = Player(user_id=user_id)

    player.money = player_data['money']
    player.ticket_price = player_data['ticket_price']
    player.feed = player_data['feed']
    player.animals = json.dumps(player_data['animals'])
    player.last_income = player_data['last_income']
    player.last_fed = player_data['last_fed']
    player.warnings = player_data['warnings']
    player.reputation = player_data['reputation']
    player.optimal_price = player_data['optimal_price']
    player.base_visitors = player_data['base_visitors']
    player.max_animals = player_data['max_animals']
    player.level = player_data['level']
    player.xp = player_data['xp']
    player.features = json.dumps(player_data['features'])
    player.staff = json.dumps(player_data['staff'])
    player.staff_income_percent = player_data['staff_income_percent']

    session.add(player)
    session.commit()
    session.close()


"""ЗАГРУЗКА ДАННЫХ"""
def load_player(user_id):
    session = Session()
    player = session.get(Player, user_id)
    session.close()

    if player:
        return {
            'money': player.money,
            'ticket_price': player.ticket_price,
            'feed': player.feed,
            'animals': json.loads(player.animals),
            'last_income': player.last_income,
            'last_fed': player.last_fed,
            'warnings': player.warnings,
            'reputation': player.reputation,
            'optimal_price': player.optimal_price,
            'base_visitors': player.base_visitors,
            'max_animals': player.max_animals,
            'level': player.level,
            'xp': player.xp,
            'features': json.loads(player.features),
            'staff': json.loads(player.staff),
            'staff_income_percent': player.staff_income_percent
        }

    return None


"""СПИСОК ВСЕХ ИГРОКОВ"""
def get_all_players():
    session = Session()
    players = session.query(Player).all()
    session.close()

    return {
        player.user_id: {
            **{
                'user_id': player.user_id,
                'money': player.money,
                'ticket_price': player.ticket_price,
                'feed': player.feed,
                'last_income': player.last_income,
                'last_fed': player.last_fed,
                'warnings': player.warnings,
                'reputation': player.reputation,
                'optimal_price': player.optimal_price,
                'base_visitors': player.base_visitors,
                'max_animals': player.max_animals,
                'level': player.level,
                'xp': player.xp,
                'staff_income_percent': player.staff_income_percent
            },
            'animals': json.loads(player.animals),
            'features': json.loads(player.features),
            'staff': json.loads(player.staff)
        }
        for player in players
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
        "Используйте /status для просмотра состояния зоопарка\n"
        "🐘 Остались вопросы? -- спроси слона! (/ask_elephant)",
        reply_markup=MAIN_KEYBOARD
    )


"""ПОМОЩЬ ПО КОМАНДАМ"""


async def post_init(application):
    await application.bot.set_my_commands([
        ("start", "Начать игру"),
        ("status", "Статус зоопарка"),
        ("price", "Изменить цену билета"),
        ("shop", "Магазин животных и корма"),
        ("feed", "Покормить животных"),
        ("hire", "Нанять персонал"),
        ("fire", "Уволить персонал"),
        ("top", "Топ игроков"),
        ("ask_elephant", "Спросить слона"),

    ])


"""РАСЧЕТ ПОСЕТИТЕЛЕЙ"""


def calculate_visitors(player):
    animals_multiplier = sum(
        ANIMALS[key]['visitor_multiplier'] * value
        for key, value in player['animals'].items()
    )  # сложение множителей всех животных

    optimal_price = player['optimal_price'] + player['reputation'] / 10  # оптимальная цена

    ticket_price = player['ticket_price']

    price_impact = max(0, 1 - (ticket_price / optimal_price))

    visitors = int(player['base_visitors'] * animals_multiplier * price_impact)

    print(f"Price Impact: {price_impact}, Visitors: {visitors}")

    if "cleaner" in player['staff']:  # если у игрока нанят уборщик
        print(f'Было {visitors}')
        visitors *= 1.1 # увеличиваем количество посетителей на 10%
        print(f'Стало {visitors}')


    return int(visitors)


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
        f"{ANIMALS[key]['emoji']} {key.capitalize()}: {value} шт. (корм: {ANIMALS[key]['feed_cost'] * value}/день)"
        for key, value in player['animals'].items() if value > 0
    )  # список животных

    staff_list = "\n".join(
        f"{STAFF[key]['emoji']} {STAFF[key]['name'].capitalize()}: {STAFF[key]['salary']}$/час"
        for key in player['staff']
    )


    now = datetime.now()
    visitors = calculate_visitors(player)
    income = visitors * player['ticket_price']

    if 'cashier' in player['staff']:
        income *= 1.1  # если у игрока нанят кассир


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


    next_level = min(player['level'] + 1, MAX_LEVEL)
    xp_req = LEVELS[next_level]['xp']

    width = 22  # ширина рамки
    inner_width = width - 2

    def format_line(text, width): # форматируем текст
        return text + ' ' * (width - len(text))

    frame = (
        f"╔{'═' * width}╗\n"
        f"{format_line(f'🔹 Уровень: {player['level']}  🔸Опыт: {player['xp']}/{xp_req}', inner_width)} \n"
        f"╚{'═' * width}╝\n"
    )
    

    await update.message.reply_text(
        f"🏠 Ваш зоопарк:\n\n"
        f"{frame}\n"
        f"──────────────────\n"
        f" 💰 Баланс: {player['money']}\n"
        f" 🌟 Репутация зоопарка: {player['reputation']}\n"
        f" 🎫 Цена билета: {player['ticket_price']}\n"
        f" 👥 Посетителей/мин: ~{visitors}\n"
        f" 💵 Доход/мин: ~{int(income)}\n"
        f" 🌾 Корма: {player['feed']}\n"
        f"──────────────────\n\n"
        f"🐾 Ваши животные:\n\n{animals_list}\n\n"
        f"──────────────────\n\n"
        f"🧑‍🔧 Ваш персонал:\n\n{staff_list}\n\n"
        f"──────────────────\n\n"
        f"⏳ Последнее кормление: {minutes} мин. назад\n"
        f"{status[-1]} Ваши животные {status[0]}\n\n"
        f"⚠️ Предупреждения: {player['warnings']}/{MAX_WARNINGS}"
    )


"""ЕЖЕМИНУТНЫЙ ДОХОД"""


async def process_income(context):
    players = get_all_players()
    for user_id, player in players.items():
        now = datetime.now().isoformat()
        income = player['ticket_price'] * calculate_visitors(player)
        print(f'visitors: {calculate_visitors(player)}')
        if 'cashier' in player['staff']:
            income = int(income * 1.1) # если у игрока нанят кассир


        updated_player = player.copy()
        updated_player['money'] += int(income)
        updated_player['last_income'] = now

        save_player(user_id, updated_player)


def calculate_income(player):
    visitors = calculate_visitors(
        player)
    ticket_price = player['ticket_price']


    base_income = visitors * ticket_price

    if 'cashier' in player['staff']:
        base_income *= 1.1
    return int(base_income)


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

def calculate_animal_total_price(base_price, current_count, quantity): # Рассчитываем стоимость нескольких животных по формуле
    total_price = 0
    for i in range(quantity):
        price_for_one = base_price * (MULTIPLIER ** (current_count + i))
        total_price += price_for_one
    return int(total_price)

def animals_keyboard(page, update):
    user_id = update.effective_user.id
    player = load_player(user_id)

    animal_keys = list(ANIMALS.keys())  # список с видами животных



    start_idx = page * ANIMALS_PER_PAGE
    end_idx = start_idx + ANIMALS_PER_PAGE

    current_animals = animal_keys[start_idx:end_idx]

    keyboard = []

    for animal in current_animals:
        emoji = ANIMALS[animal]['emoji']
        price = ANIMALS[animal]['price']
        current_count = player['animals'].get(animal, 0)
        price_for_one = int(price * (MULTIPLIER ** (current_count)))

        if player['level'] < ANIMALS[animal]['required_level']: # если уровень игрока слишком низкий
            keyboard.append([InlineKeyboardButton(
                f"{emoji} {animal.capitalize()} - {price_for_one}$ 🔒(уровень {ANIMALS[animal]['required_level']})",
                callback_data=f'animal_{animal}'
            )])
        else:
            keyboard.append([InlineKeyboardButton(
                f"{emoji} {animal.capitalize()} - {price_for_one}$",
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
        food_price = FOOD['корм']['price']

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

        """УСПЕШНАЯ ПОКУПКА КОРМА"""

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
                f"💸 -{purchase['total_price']} монет\n\n"
                f"💰 Остаток: {player['money']} монет\n"
                f"🌾 Всего корма:  {player['feed']}\n\n"
                f"🏪 Чтобы продолжить покупки используйте /shop\n"
                "🐾 Для просмотра статуса зоопарка используйте /status"
            )

            xp = max(purchase['total_price'] // 100, 1)
            # ПОЛУЧЕНИЕ ОПЫТА
            await add_xp(context, update.effective_user.id, xp)



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
        animal_data = ANIMALS.get(animal_name)

        price = animal_data['price']
        count = player['animals'].get(animal_name, 0)
        price_for_one = int(price * (MULTIPLIER ** count))

        await query.edit_message_text(
            f"🛒 Вы выбрали: {animal_data['emoji']} {animal_name.capitalize()}\n"
            f"🐾 У вас имеется {player[animal_name.capitalize()]}/{player['max_animals']}\n\n"
            f"⭐ Минимальная репутация для покупки: {animal_data['min_rep']}\n"
            f"💵 Цена: {price_for_one}$\n"
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
        print(f'необходимая репутация {ANIMALS[purchase['animal']]['min_rep']}')

        if player['reputation'] < ANIMALS[purchase['animal']]['min_rep']:

            need_rep = ANIMALS[purchase['animal']]['min_rep'] - player['reputation']
            await query.edit_message_text(
                f"❕ У вашего зоопарка низкая репутация ❕\n\n"
                f"🌟 Текущая репутация: {player['reputation']}\n"
                f"⭐ Необходимая репутация: {ANIMALS[purchase['animal']]['min_rep']}\n"
                f"📉 Нужно ещё {need_rep} очков репутации.\n\n"
                f"📄 Чтобы узнать, как повысить репутацию используйте /reputation"

            )
            return


        elif to_buy > player['max_animals']: # если достигнут лимит животных
            available = max([player['max_animals'] - player['animals'].get(animal_name, 0), 0])
            emoji = ANIMALS[animal_name]['emoji']

            count = player['animals'].get(animal_name, 0)

            await query.edit_message_text(
                f"❕ Вы превысили лимит животных ❕\n\n"
                f"{emoji} У вас: {count}/{player['max_animals']}\n"
                f"🛒 Выбрано для покупки: {purchase['quantity']}\n"
                f"☑️ Доступно для покупки: {available}"

            )
            return

        """УСПЕШНАЯ ПОКУПКА ЖИВОТНЫХ"""

        if player['money'] >= purchase['total_price']:  # если достаточно денег
            player['money'] -= purchase['total_price']

            if animal_name in player['animals']:
                player['animals'][animal_name] += purchase['quantity']
            else:
                player['animals'][animal_name] = purchase['quantity']


            if player['reputation'] != 100:
                rep = 5 * purchase['quantity']
                if player['reputation'] + rep > 100:
                    rep = 100 - player['reputation']
                player['reputation'] += rep
            else:
                rep = 0

            save_player(user_id, player)

            await query.edit_message_text(
                f"✅ Покупка завершена!\n\n"
                f"{ANIMALS[animal_name]['emoji']} +{purchase['quantity']} {animal_name.capitalize()}\n"
                f"💸 -{purchase['total_price']} монет\n"
                f"💰 Остаток: {player['money']} монет\n\n"
                f"⭐ Получено очков репутации: {rep}\n\n"
                f"🏪 Чтобы продолжить покупки используйте /shop\n"
                f"🐾 Для просмотра статуса зоопарка используйте /status"
            )


            xp = purchase['total_price'] // 100
            # ПОЛУЧЕНИЕ ОПЫТА
            await add_xp(context, update.effective_user.id, xp)


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
    if query.data == 'buy_animals' or query.data.startswith('animals_page_'):

        page = 0
        if query.data.startswith('animals_page_'):
            page = int(query.data.split('_')[2])

        await query.edit_message_text(
            "🐾 Выберите животное для покупки:",
            reply_markup=InlineKeyboardMarkup(animals_keyboard(page, update))
        )
        return


    # выбор конкретного животного
    elif query.data.startswith('animal_'):
        animal = query.data.split('_', 1)[1]
        animal_data = ANIMALS.get(animal)

        if not animal_data:
            await query.edit_message_text("❌ Животное не найдено!\n Ошибка в блоке shop_button_handler")
            return

        if player['level'] < animal_data['required_level']: #  если уровень слишком низкий
            await context.bot.send_message(
                chat_id=user_id,
                text=f"Вы выбрали: {animal_data['emoji']} {animal.capitalize()}\n\n"
                     f"🔺 Требуется уровень {animal_data['required_level']}\n🔹 Ваш уровень: {player['level']}"
            )
            return



        context.user_data['selected_animal'] = animal

        price = animal_data['price']
        count = player['animals'].get(animal, 0)
        price_for_one = int(price * (MULTIPLIER ** count))

        await query.edit_message_text(
            f"🛒 Вы выбрали: {animal_data['emoji']} {animal.capitalize()}\n"
            f"🐾 У вас имеется: {player['animals'].get(animal, 0)}/{player['max_animals']}\n\n"
            f"⭐ Минимальная репутация для покупки: {animal_data['min_rep']}\n"
            f"💵 Цена: {price_for_one}$\n"
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

    message = update.message.text
    # Обработчик команд
    if message == '🏠 Статус зоопарка':
        await status(update, context)
        return
    elif message == '🛒 Магазин':
        await shop(update, context)
        return
    elif message == '🌾 Покормить животных':
        await feed(update, context)
        return
    elif message == '👨‍🔧 Персонал':
        await hire(update, context)
        return
    elif message == '🐘 Спросить слона':
        await help_command(update, context)
        return
    elif message == '🏆 Топ игроков':
        await top_players(update, context)
        return



    if context.user_data.get('awaiting_feed_quantity'):  # если режим покупки корма

        try:
            quantity = int(update.message.text)
            if quantity <= 0:
                raise ValueError

            total_price = quantity * FOOD['корм']['price']

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
            animal_data = ANIMALS.get(animal_name)
            print(animal_data)

            current_count = player['animals'].get(animal_name, 0)
            base_price = animal_data['price']

            total_price = calculate_animal_total_price(base_price, current_count, quantity)

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


"""ПЕРЕВОД ВРМЕМЕНИ В МИНУТЫ И ЧАСЫ"""

def format_minutes_to_hm(total_minutes: int) -> tuple[int, int]:
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return hours, minutes


"""КОРМЛЕНИЕ ЖИВОТНЫХ"""


async def feed(update, context):

    user_id = update.effective_user.id
    player = load_player(user_id)

    now = datetime.now()

    total_feed_cost = sum(
        ANIMALS[animal]['feed_cost'] * count
        for animal, count in player['animals'].items()
    )  # общая стоимость

    last_fed = datetime.fromisoformat(player['last_fed'])
    now = datetime.now()
    time_since_fed = (now - last_fed)
    starving = int((FEEDING_INTERVAL - time_since_fed.total_seconds()) // 60) # время до голода в минутах

    hours_left = starving // 60
    minutes_left = starving % 60

    feeding_interval_min = FEEDING_INTERVAL // 60

    if time_since_fed.total_seconds() < FEEDING_INTERVAL // 2:  #  если с последнего кормления прошло недостаточно времени

        await update.message.reply_text(
            f"🍽️ Ваши животные сыты!\n"
            f"🌾 Вы сможете покормить их снова через {int(hours_left // 2)} ч. {int(minutes_left // 2)} мин.\n"
            f"⚠️ Осталось времени до голодания: {int(hours_left)} ч. {int(minutes_left)} мин."
        )

        return

    if player['feed'] < total_feed_cost:
        await update.message.reply_text(
            f"❌ Не хватает корма!\n"
            f"Нужно: {total_feed_cost} 🌾\n"
            f"Имеется: {player['feed']} 🌾\n"
            f"Необходимо еще {total_feed_cost - player['feed']} ед. корма"
        )
        return

    updated_player = player.copy()
    updated_player['last_fed'] = datetime.now().isoformat()
    updated_player['feed'] -= total_feed_cost
    save_player(user_id, updated_player)
    minutes = FEEDING_INTERVAL // 60

    can_feed = max([minutes - (minutes // 2), 0])
    time_left = (FEEDING_INTERVAL // 2) - time_since_fed.total_seconds()

    time_since_fed = (now - last_fed)
    starving = (FEEDING_INTERVAL - time_since_fed.total_seconds()) // 60 # время до голода

    hours_left = starving // 60
    minutes_left = starving % 60

    await update.message.reply_text(
        f"🍽️ Животные накормлены!\n"
        f"🌾 Израсходовано корма: {total_feed_cost}\n"
        f"⏰ Последнее кормление: {now.strftime('%H:%M:%S')}\n"
        f"😸 Кормление будет доступно через {FEEDING_INTERVAL // 60 // 60 // 2} ч. 0 мин.\n"
        f"⚠️ Осталось времени до голодания: {FEEDING_INTERVAL // 60 // 60} ч. 0 мин."
    )


"""ПРОВЕРКА ГОЛОДНЫХ ЖИВОТНЫХ"""


async def check_hunger(context):
    now = datetime.now()
    players = get_all_players()
    for user_id, player in players.items():
        time_since_fed = (now - datetime.fromisoformat(player['last_fed'])).total_seconds()

        #  предупреждение о проверке
        if FEEDING_INTERVAL < time_since_fed:
            if 'feeder' in player['staff']: # если у игрока нанят кормильщик
                total_feed_cost = sum(
                    ANIMALS[animal]['feed_cost'] * count
                    for animal, count in player['animals'].items()
                )  # необходимая еда

                econome_feed = int(total_feed_cost * 0.8)  # сэкономлено корма

                if player['feed'] < econome_feed: # если у игрока не хватает корма
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"👩‍🌾 Смотритель зоопарка хотел покормить животных,\n"
                             f"но обнаружил нехватку корма на складе!\n\n"
                             f"🌾 Чтобы смотритель зоопарка вернулся к работе, пополните запасы корма.\n\n"
                             f"Необходимо купить: {econome_feed} ед. корма\n"

                    )
                else:



                    last_fed = datetime.fromisoformat(player['last_fed'])
                    now = datetime.now()
                    time_since_fed = now - last_fed
                    FEEDING_INTERVAL - time_since_fed.total_seconds()

                    updated_player = player.copy()
                    updated_player['last_fed'] = datetime.now().isoformat()
                    updated_player['feed'] -= econome_feed
                    save_player(user_id, updated_player)


                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"👩‍🌾 Смотритель зоопарка покормил животных!\n"
                             f"⬇ Потрачено корма: {econome_feed}\n"
                             f"⬆ Сэкономлено корма: {total_feed_cost - econome_feed} (20%)\n\n"
                             f"🌾 Чтобы смотритель зоопарка смог кормить животных, не забывайте пополнять запасы корма корма."
                    )

                    return

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
                text=f"🌾 Ваши животные давно не ели!\n"
                     f"👮 Вам следует покормить их перед следующим визитом Инспектора.")



        if time_since_fed > FEEDING_INTERVAL:
            if player['warnings'] < MAX_WARNINGS:
                player['warnings'] += 1

            minute_income = player['ticket_price'] * calculate_visitors(player)  # ежеминутный доход
            hour_income = minute_income * 60 * 12 # доход в 12ч.
            mulct = hour_income * player['warnings']  # денежный штраф

            if player['warnings'] >= MAX_WARNINGS:
                mulct = 0
            player['money'] -= mulct # штрафуем игрока
            phrase = random.choice(inspector_phrases)  # фраза инспектора
            if player['reputation'] > 33:
                print('репутация > 10')
                rep = 33
                player['reputation'] -= rep  # зоопарк теряет репутацию
            else:
                rep = 0
                player['reputation'] = 0
            await context.bot.send_message(
                chat_id=user_id,
                text=f"{phrase}\n\n"
                     f"Вы получили штраф: {mulct} монет\n"
                     f"⚠️ Получено предупреждений: {player['warnings']}\n"
                     f"📉 Репутация зоопарка: -{rep}\n\n"
                     f"🌟 Текущая репутация зоопарка: {player['reputation']}\n"
                     f"🌾 Срочно покормите животных командой /feed")

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
                         f"🕐 Следующий визит через {INSPECTION_INTERVAL // 60 // 60} ч.\n"
                         f"😸 Продолжайте кормить животных вовремя, чтобы увеличить репутацию зоопарка!")

            else: # если предупреждений нет
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"👮 Инспектор посетил ваш зоопарк и остался доволен!\n"
                         f"🕐 Следующий визит через {INSPECTION_INTERVAL // 60 // 60} ч.\n"
                         f"😸 Продолжайте кормить животных вовремя, чтобы поддерживать репутацию зоопарка!!")


        save_player(user_id, player)


"""СЛУЧАЙНЫЕ СОБЫТИЯ"""


async def random_events(context):
    print('СЛУЧАЙНОЕ СОБЫТИЕ!')
    players = get_all_players()

    for user_id, player in players.items():
        if not "random_events" in player['features']:
            print(f'У игрока {user_id} нет доступа к случайным событиям')
            print(player['features'])
            continue


        positive_events = {k: v for k, v in EVENTS.items() if v.get('positive', False)}
        negative_events = {k: v for k, v in EVENTS.items() if not v.get('positive', True)}


        special_events = ['animal_birth', 'animal_escape']
        random_animal = random.choice([animal for animal, count in player['animals'].items() if count > 0])
        regular_negative_events = {k: v for k, v in negative_events.items() if k not in special_events}


        if random.random() > 0.2: # обычное событие

            # позитивное (50%) негативное (50%) событие

            guard_message = ''

            if random.random() < 0.5:
                # Позитивное событие
                event_name = random.choice(list(positive_events.keys()))
                event = positive_events[event_name]
            else:
                #
                if random.random() < 0.4:  # 40% шанс на болезнь
                    event_name = "illness"
                    event = EVENTS["illness"]

                    if 'vet' in player['staff']: # если у игрока есть ветеринар
                        emoji = ANIMALS[random_animal]['emoji']
                        message = f"🧑‍⚕️ {random_animal} заболел(-а), но ваш ветеринар успешно справился со своей работой!"
                        message_rep = '⭐ На данный момент у вас максимальная репутация.'
                        rep = 5

                        if player['reputation'] + 5 < 100: # если у игрока не максимальная репутация
                            message_rep = '\n⭐ Вы получили 5 очков репутации!'
                            player['reputation'] += 5

                        elif player['reputation'] < 100:
                            rep = 100 - player['reputation']
                            message_rep = f'\n⭐ Вы получили {rep} очков репутации!'
                            player['reputation'] += rep
                        save_player(user_id, player)

                        await context.bot.send_message(
                            chat_id=user_id,
                            text=f"{message}{message_rep}"
                        )

                        return

                else:  # 50% на другие негативные события (кражи и тд)

                    guard_message = ''

                    if 'guard' in player['staff']: # если у игрока нанят сторож
                        chance = random.random()
                        if chance > 0.7: # предотвращение кражи

                            guard_message = f"" + \
                                        f"🛡️ Сторож заметил подозрительное движение в зоопарке и успешно предотвратил кражу"

                            await context.bot.send_message(
                                chat_id=user_id,
                                text=f" {guard_message}"
                            )

                            return

                        else: # не смогли предотвратить кражу
                            guard_message = f"😪 Упс! Кажется наш сторож Петрович уснул прямо на посту...*\n\n"

                    event_name = random.choice(list(regular_negative_events.keys()))
                    event = regular_negative_events[event_name]

            # обработка события
            message = ""
            if event["type"] in ["money", 'food', 'reputation']:
                amount = random.randint(event["min_amount"], event["max_amount"])


                if event["type"] == 'money':

                    income = calculate_income(player)

                    expense_multiplier = 19 # игрок теряет заработанные за 10 минут монеты
                    expenses = int(income * expense_multiplier)

                    amount = expenses

                    e_type = event["type"]
                    if expenses < 0 and player[event["type"]] + expenses < 0:
                        amount = -player[event["type"]]
                        print(f'У игрока {amount} {event["type"]}')

                    player[event["type"]] += amount

                elif event["type"] == 'food':

                    food = player['food']
                    food_minus = int(food * 0.15) # игрок теряет 15% корма

                    amount = food_minus

                    if food_minus < 0 and player[event["type"]] + food_minus < 0:
                        amount = -player[event["type"]]
                        print(f'У игрока {amount} {event["type"]}')

                    player[event["type"]] += amount

                else: # если репутация

                    if player[event["type"]] >= 100:
                        amount = 0
                    elif player[event["type"]] + amount > 100:
                        player[event["type"]] = 100
                    else:
                        player[event["type"]] += amount

                save_player(user_id, player)
                message = event["message"].format(amount=amount)

            if message:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"{guard_message}{event['emoji']} *Событие!* {event['emoji']}\n{message}"
                )


        # Специальные события (рождение/побег)
        if random.random() < 0.3:  # 30% шанс на специальное событие
            await special_event(context, user_id, player)


"""СПЕЦИАЛЬНЫЕ СОБЫТИЯ"""
async def special_event(context, user_id, player):

    bad_relevant_animals = [
        a for a, count in player['animals'].items() if count >= 2
        and ANIMALS[a]['price'] <= 100000  # побег животного
    ]
    good_relevant_animals = [
        a for a, count in player['animals'].items() if count >= 2
        and ANIMALS[a]['price'] ] # рождение животного

    if not good_relevant_animals and not bad_relevant_animals:  # если нет подходящих животных
        return

    good_selected_animal = random.choice(good_relevant_animals)
    bad_selected_animal = random.choice(bad_relevant_animals)

    if player['animals'][good_selected_animal] < 2 and player['animals'][bad_selected_animal] < 2:
        return

    chance = random.random()
    birth_chance = 0.4
    if 'vet' in player['staff']:
        birth_chance = 0.6 # увеличенный шанс на рождение

    selected_animal = ''

    if chance > birth_chance: # побег животного

        guard_message = 0

        if 'guard' in player['staff']:  # если у игрока нанят сторож
            chance = random.random()
            if chance > 0.7:  # предотвращение кражи

                guard_message = f"" + \
                                f"🛡️ {bad_selected_animal.capitalize()} хотел(-а) совершить грандиозный побег, но сторож успешно справился со своей работой."

                await context.bot.send_message(
                    chat_id=user_id,
                    text=f" {guard_message}"
                )

                return

            else:  # не смогли предотвратить побег
                guard_message = f"😪 Упс! Кажется наш сторож Петрович уснул прямо на посту...*\n\n"




        event = event = EVENTS["animal_escape"]
        player['animals'][bad_selected_animal] -= 1
        selected_animal = bad_selected_animal
    else: # рождение животного

        event = event = EVENTS["animal_birth"]
        player['animals'][good_selected_animal] += 1
        selected_animal = good_selected_animal

    await context.bot.send_message(
        chat_id=user_id,
        text=f"{event['emoji']} *Событие!* {event['emoji']}\n\n" +
             event['message'].format(
                 animal=selected_animal.capitalize(),
                 animal_emoji=ANIMALS[selected_animal]['emoji'],
                 new_count=player['animals'][selected_animal]
             )
    )

    save_player(user_id, player)



"""ПОВЫШЕНИЕ УРОВНЯ"""
async def add_xp(context, user_id, amount):

    player = load_player(user_id)
    current_level = player['level']
    new_xp = player['xp'] + amount

    max_level = int(max(LEVELS.keys()))
    print(f'max level == {max_level} ')

    while current_level < max_level:
        next_level = current_level + 1
        print(LEVELS[next_level])
        xp_req = LEVELS[next_level]['xp']  # необходимый опыт
        if new_xp >= xp_req: # если игрок повышает уровень
            current_level = next_level
        else:
            break

    if current_level > player['level']: #  игрок повысил уровень

        classic_message = "Улучшения:\n ◆ Оптимальная цена билета ↑\n ◆ Базовое количество посетителей ↑\n ◆ Лимит животных +1 ↑" # стандартные улучшения

        message = LEVELS[current_level]['message']
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🚀 Вы достигли уровня {current_level}!\n\n{message}\n{classic_message}"
        )

        player['features'].append(LEVELS[current_level]['features']) # добавляем игроку новый функционал

    # обновление параметров игрока
    player['level'] = current_level
    player['xp'] = new_xp


    if current_level >= max_level:
        # максимальный уровень достигнут
        await context.bot.send_message(
            chat_id=user_id,
            text=f"✨ Получено опыта: +{amount}\n"
                 f"🚀 Текущий уровень: {current_level}\n"
                 f"🎉 Достигнут максимальный уровень!"
        )

    else:

        player['optimal_price'] += 5
        player['base_visitors'] += 5
        player['max_animals'] += 1

        next_xp = LEVELS[current_level + 1]['xp']
        remaining_xp = next_xp - new_xp  # опыт до следующего уровня
        # информация о прогрессе (если НЕ максимальный уровень)
        await context.bot.send_message(
            chat_id=user_id,
            text=f"✨ Получено опыта: +{amount}xp\n"
                 f"🚀 Текущий уровень: {current_level}\n\n"
                 f"▲ До следующего уровня: {remaining_xp}xp"
        )

    save_player(user_id, player)


"""НАНИМАЕМ СОТРУДНИКОВ"""
async def hire(update, context):
    user_id = update.effective_user.id
    player = load_player(user_id)

    staff_list = [] #Список персонала

    for staff in STAFF:
        if staff in player['staff']: # если сотрудник нанят
            status = 'Нанят'
            emoji = "✅"
        else:
            status = 'Не нанят'
            emoji = "❌"

        is_locked = ''

        if STAFF[staff]['level'] > player['level']:
            is_locked = f'🔒(уровень {STAFF[staff]['level']})\n\n'

        staff_info = (f"{STAFF[staff]['emoji']} {STAFF[staff]['name']} {STAFF[staff]['emoji']}\n"
                      f'{is_locked}'
                       f"{STAFF[staff]['description']}\n\n"
                      f"{emoji} Статус: {status}\n"
                      f"💵 Фиксированная зарплата: {STAFF[staff]['salary']}$/час \n"
                      f"────────────────────────────────────")

        staff_list.append(staff_info)

    # Если наняты все
    if len(staff_list) == len(STAFF) and all(staff in player['staff'] for staff in STAFF):
        await update.message.reply_text("🚫 У вас уже наняты все доступные сотрудники!")
        return

    if not context.args: # не переданы аргументы
        await update.message.reply_text(
            f"🎩 Доступный персонал:\n\n" + "\n\n".join(staff_list) +
            "\n\n►  Каждый нанятый сотрудник получает фиксированную зарплату\n"
            "\n► Сотрудники получают зарплату каждый час игрового времени"
            f"\n► Одновременно могут быть наняты только 3 сотрудника"
            "\n\n Чтобы нанять сотрудника используйте /hire .\n Например: '/hire уборщик'"
            "\n\n Чтобы уволить сотрудника используйте /fire .\n Например: '/fire кассир'"

        )

    # если передана профессия
    if context.args:

        staff_choice = context.args[0].lower()
        print(staff_choice)



        if staff_choice not in STAFF_NAME_TO_ID: # если такой профессии нет
            await update.message.reply_text("❌ Неверная профессия.")
            return

        staff_choice = STAFF_NAME_TO_ID[staff_choice]

        if staff_choice in player['staff']: # Если уже нанят
            await update.message.reply_text(f"❌ {STAFF[staff_choice]['name'].capitalize()} уже нанят.")
            return

        if player['level'] < STAFF[staff_choice]['level']:
            await update.message.reply_text(f"❌ Необходим уровень {STAFF[staff_choice]['level']}\n"
                                            f"Текущий уровень: {player['level']}")
            return

        count = len(player['staff']) # кол-во сотрудников

        if count >= STAFF_LIMIT:
            await update.message.reply_text(
                f"❌ {STAFF[staff_choice]['name'].capitalize()} не может быть нанят!\n\n"
                f"У вас нанято: {count}\n"
                f"Лимит на количество сотрудников: {STAFF_LIMIT}\n"
                f"Чтобы нанять новый персонал увольте старый с помощью команды /fire"
            )
            return

        # нанимаем сотрудника

        visitors = calculate_visitors(player)
        income = visitors * player['ticket_price']

        if 'cashier' in player['staff']:
            income = int(income * 1.1) # если у игрока нанят кассир

        hourly_income = income * 60

        choise_salary = STAFF[staff_choice]['salary']
        total_staff_salary = sum(STAFF[person]['salary'] for person in player['staff'])

        if total_staff_salary + choise_salary > hourly_income: # если у игрока слишком низкий доход
            await update.message.reply_text(
                f"❌ {STAFF[staff_choice]['name'].capitalize()} не может быть нанят!\n\n"
                f"Ваша зарплата не позволяет нанять сотрудников с такой высокой зарплатой.\n"
                f"Текущий доход: {hourly_income} монет/час.\n"
                f"Суммарная зарплата уже нанятых сотрудников: {total_staff_salary} монет/час."
            )
            return

        player['staff'].append(staff_choice)

        save_player(user_id, player)

        await update.message.reply_text(
            f"✅ Вами был нанят {STAFF[staff_choice]['name']}!\n"
            f"💵 Зарплата: {STAFF[staff_choice]['salary']} монет/час\n"
            f"🎉 Бонусы: {STAFF[staff_choice]['description']}\n"
        )


"""УВОЛЬНЕНИЕ СОТРУДНИКОВ"""
async def fire(update, context):
    user_id = update.effective_user.id
    player = load_player(user_id)

    if not context.args:
        await update.message.reply_text(
            "❌ Для увольнения сотрудника укажите его профессию.\n\n"
            "Например: /fire кассир"
        )
        return

    staff_choice = context.args[0].lower()


    if staff_choice not in STAFF_NAME_TO_ID:  # если профессия не существует
        await update.message.reply_text("❌ Неверная профессия.")
        return

    staff_choice = STAFF_NAME_TO_ID[staff_choice]

    if staff_choice not in player['staff']:  # если сотрудник не нанят
        await update.message.reply_text(f"❌ {STAFF[staff_choice]['name']} не нанят.")
        return


    player['staff'].remove(staff_choice)

    save_player(user_id, player)


    await update.message.reply_text(
        f"✅ {STAFF[staff_choice]['name']} был уволен!\n"
    )



async def process_salaries(context):  # зарплата сотрудникам
    players = get_all_players()
    for user_id, player in players.items():
        now = datetime.now().isoformat()

        total_salary = 0
        staff = player['staff']

        for person in staff:
            salary = STAFF[person]['salary']  # Фиксированная зарплата

            total_salary += salary

        if total_salary > 0:
            updated_player = player.copy()
            updated_player['money'] -= total_salary

            # Отправляем уведомление игроку
            await context.bot.send_message(
                chat_id=user_id,
                text=f"💸 Зарплата персонала была списана:\n- {total_salary} монет."
            )

            save_player(user_id, updated_player)

        await asyncio.sleep(1)


"""ПОМОЩЬ"""
async def help_command(update, context):

    help_text = (
        "🐘 *Спроси Слона*\n\n"

        "❓ *Какова цель игры?*\n"
        "Вы управляете зоопарком: покупаете животных, нанимаете персонал, следите за кормом и репутацией.\n\n"

        "❓ *Как заработать деньги?*\n"
        "Доход зависит от животных, множителей, цены билета и персонала (например, кассир увеличивает доход).\n\n"

        "❓ *Что такое репутация?*\n"
        "Репутация показывает статус зоопарка. Чем выше — тем больше посетителей. Уменьшается при нарушениях.\n\n"

        "❓ *Как улучшить репутацию?*\n"
        "Кормите животных, нанимайте персонал и покупайте новых животных.\n\n"

        "❓ *Зачем нужен персонал?*\n"
        "Персонал следит за зоопарком (подробнее - /hire)\n\n"

        "❓ *Что делает инспектор?*\n"
        "Инспектор проверяет ваш зоопарк, штрафует и снижает репутацию при нарушениях.\n\n"

        "❓ *Что будет, если не кормить животных?*\n"
        "Инспектор будет вами ОЧЕНЬ недоволен.\n\n"
    )


    with open("help.png", "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption=help_text,
            parse_mode='Markdown'
        )

    command_guide = (
        "📖 *Основные команды:*\n"
        "🔹 /start — начать игру\n"
        "🔹 /status — текущий статус зоопарка\n"
        "🔹 /shop — магазин животных и кормов\n"
        "🔹 /feed — покормить животных\n"
        "🔹 /hire — нанять сотрудника\n"
        "🔹 /fire — уволить сотрудника\n"
        "🔹 /price — изменить цену билета\n"
    )

    await update.message.reply_text(command_guide, parse_mode='Markdown')


from telegram import Bot


async def top_players(update, context):
    players = get_all_players()
    bot = context.bot  # Получаем объект бота, чтобы использовать API Telegram

    # Сортировка по деньгам
    top_money = sorted(players.items(), key=lambda x: x[1]['money'], reverse=True)[:5]

    # Сортировка по доходу в час
    top_income = sorted(players.items(), key=lambda x: calculate_income(x[1]), reverse=True)[:5]

    # Сортировка по опыту
    top_xp = sorted(players.items(), key=lambda x: x[1]['xp'], reverse=True)[:5]


    top_message = "🏆 *Топ игроков* \n\n"

    top_message += "💰 Топ-5 по деньгам:\n"
    for i, (player_id, player) in enumerate(top_money, 1):
        username = await get_username_from_id(bot, player_id)
        top_message += f"{i}. @{username} — {player['money']} монет\n"

    top_message += "\n"


    top_message += "💸 Топ-5 по доходу:\n"
    for i, (player_id, player) in enumerate(top_income, 1):
        username = await get_username_from_id(bot, player_id)
        income = calculate_income(player)
        top_message += f"{i}. @{username} — {income} монет/мин.\n"

    top_message += "\n"


    top_message += "🌟 Топ-5 по опыту:\n"
    for i, (player_id, player) in enumerate(top_xp, 1):
        username = await get_username_from_id(bot, player_id)
        top_message += f"{i}. @{username} — {player['xp']} XP\n"

    await update.message.reply_text(top_message, parse_mode='Markdown')


async def get_username_from_id(bot: Bot, player_id: int) -> str: # айди в юзер
    try:
        chat = await bot.get_chat(player_id)
        username = chat.username
        if username is None:
            return str(player_id)
        return username
    except Exception as e:
        print(f"Error fetching username for player_id {player_id}: {e}")
        return str(player_id)



def main():
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("price", set_price))
    application.add_handler(CommandHandler("shop", shop))
    application.add_handler(CommandHandler("feed", feed))
    application.add_handler(CommandHandler("hire", hire))
    application.add_handler(CommandHandler("fire", fire))
    application.add_handler(CommandHandler("ask_elephant", help_command))
    application.add_handler(CommandHandler("top", top_players))

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

    # периодическая зп сотрудникам
    application.job_queue.run_repeating(
        process_salaries,
        interval=SALARY_INTERVAL,
        first=0
    )

    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_input
    ))

    application.run_polling()


if __name__ == '__main__':
    main()
