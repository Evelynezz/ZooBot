

ANIMALS = {
    'кот': {
        'required_level': 1,
        'price': 200,
        'visitor_multiplier': 0.1,
        'feed_cost': 5,
        'emoji': '🐈',
        'initial_count': 1,
        'min_rep': 10
    },
    'кролик': {
        'required_level': 1,
        'price': 600,
        'visitor_multiplier': 0.15,
        'feed_cost': 10,
        'emoji': '🐇',
        'min_rep': 15
    },
    'ёж': {
        'required_level': 1,
        'price': 1000,
        'visitor_multiplier': 0.2,
        'feed_cost': 15,
        'emoji': '🦔',
        'min_rep': 20
    },
    'попугай': {
        'required_level': 1,
        'price': 2000,
        'visitor_multiplier': 0.25,
        'feed_cost': 20,
        'emoji': '🦜',
        'min_rep': 25
    },
    'черепаха': {
        'required_level': 2,
        'price': 3500,
        'visitor_multiplier': 0.3,
        'feed_cost': 25,
        'emoji': '🐢',
        'min_rep': 30
    },
    'змея': {
        'required_level': 2,
        'price': 7000,
        'visitor_multiplier': 0.35,
        'feed_cost': 30,
        'emoji': '🐍',
        'min_rep': 35
    },
    'лиса': {
        'required_level': 2,
        'price': 15000,
        'visitor_multiplier': 0.4,
        'feed_cost': 35,
        'emoji': '🦊',
        'min_rep': 40
    },
    'обезьяна': {
        'required_level': 2,
        'price': 35000,
        'visitor_multiplier': 0.5,
        'feed_cost': 40,
        'emoji': '🐒',
        'min_rep': 45
    },
    'коала': {
        'required_level': 3,
        'price': 75000,
        'visitor_multiplier': 0.6,
        'feed_cost': 45,
        'emoji': '🐨',
        'min_rep': 50
    },
    'ленивец': {
        'required_level': 3,
        'price': 100000,
        'visitor_multiplier': 0.7,
        'feed_cost': 50,
        'emoji': '🦥',
        'min_rep': 55
    },
    'лама': {
        'required_level': 3,
        'price': 120000,
        'visitor_multiplier': 0.8,
        'feed_cost': 55,
        'emoji': '🦙',
        'min_rep': 60
    },
    'бурый медведь': {
        'required_level': 3,
        'price': 150000,
        'visitor_multiplier': 0.9,
        'feed_cost': 65,
        'emoji': '🐻',
        'min_rep': 65
    },
    'белый медведь': {
        'required_level': 4,
        'price': 200000,
        'visitor_multiplier': 1.0,
        'feed_cost': 70,
        'emoji': '🐻‍❄️',
        'min_rep': 70
    },
    'панда': {
        'required_level': 4,
        'price': 250000,
        'visitor_multiplier': 1.15,
        'feed_cost': 75,
        'emoji': '🐼️',
        'min_rep': 75
    },
    'тигр': {
        'required_level': 4,
        'price': 300000,
        'visitor_multiplier': 1.3,
        'feed_cost': 80,
        'emoji': '🐅',
        'min_rep': 80
    },
    'бегемот': {
        'required_level': 4,
        'price': 500000,
        'visitor_multiplier': 1.45,
        'feed_cost': 85,
        'emoji': '🦛',
        'min_rep': 85
    },
    'носорог': {
        'required_level': 5,
        'price': 700000,
        'visitor_multiplier': 1.6,
        'feed_cost': 90,
        'emoji': '🦏',
        'min_rep': 80
    },
    'крокодил': {
        'required_level': 5,
        'price': 1000000,
        'visitor_multiplier': 1.8,
        'feed_cost': 95,
        'emoji': '🐊',
        'min_rep': 90
    },
    'жираф': {
        'required_level': 5,
        'price': 1500000,
        'visitor_multiplier': 2.0,
        'feed_cost': 100,
        'emoji': '🦒',
        'min_rep': 95
    },
    'слон': {
        'required_level': 5,
        'price': 3000000,
        'visitor_multiplier': 2.5,
        'feed_cost': 120,
        'emoji': '🐘',
        'min_rep': 100
    }


}


FOOD = {
    'корм': {
        'price': 5,
        'quantity': 1,
        'emoji': '🌾',
        'description': 'единица корма'}}


# СЛУЧАЙНЫЕ СОБЫТИЯ
EVENTS = {
    # Положительные
    "generous_visitor": {
        "type": "money",
        "positive": True,
        "message": "💰 Сегодня отмечается день щедрости! Ваши посетители оставили вам чаевые: {amount} монет!",
        "min_amount": 50,
        "max_amount": 150,
        "emoji": "🎁"
    },
    "animal_show": {
        "type": "reputation",
        "positive": True,
        "message": '📰 Журнал "National Zoo" написал положительную статью о вашем зоопарке!\n Репутация возросла на {amount} единиц!',
        "min_amount": 5,
        "max_amount": 10,
        "emoji": "✨"
    },

    # Негативные
    "thief": {
        "type": "money",
        "positive": False,
        "message": "💵 Этой ночью кто-то пробрался в ваш зоопарк и украл {amount} монет!",
        "min_amount": -150,
        "max_amount": -50,
        "emoji": "💢"
    },
    "illness": {
        "type": "money",
        "positive": False,
        "message": "🤒 Один из ваших питомцев заболел!\nРасходы на лечение: {amount} монет.",
        "min_amount": -300,
        "max_amount": -150,
        "emoji": "💢"
    },
    "food_theft": {
        "type": "feed",
        "positive": False,
        "message": "🦝 Еноты пробрались на склад!\n У вас украли {amount} единиц корма.",
        "min_amount": -50,
        "max_amount": -20,
        "emoji": "💢"
    },

    "vandalism": {
        "type": "reputation",
        "positive": False,
        "message": "🎨 Этой ночью кто-то пробрался в ваш зоопарк и превратил стену в сомнительный арт-объект.",
        "min_amount": -15,
        "max_amount": -5,
        "emoji": "💢"
    },

    "animal_birth": {
        "type": "birth",
        "message": "🎉 Сегодня в вашем зоопарке пополнение!\n🥺 {animal} уже радует посетителей своей милотой!\n\nТеперь у вас {new_count} {animal_emoji}.",
        "emoji": "🐣",
    },
    "animal_escape": {
        "type": "escape",
        "message": "😵 Кажется кто-то забыл закрыть вольер...\n🌙 Этой ночью {animal} совершил(-а) грандиозный побег!\n\nТеперь у вас {new_count} {animal_emoji}.",
        "emoji": "🚶‍♂️",
    }
}


# рандомные фразы инспектора
inspector_phrases = [
    '👮 Инспектор зоопарков на связи! Если ты не начнешь кормить своих животных, они могут начать писать мемуары о своей голодной жизни!',
    '👮 Инспектор зоопарков: "Если вы не покормите своих животных, то они начнут требовать зарплату за свою работу по развлечению посетителей!"',
    '📞 Ало! Это Инспектор зоопарков. Мне поступают многочисленные жалобы от ваших животных! Вам следует немедленно покормить их.',
    '😿 Это служба защиты животных. Вчера в наш главный офис пришёл ваш кот, который был вынужден перейти на веганскую диету. Что происходит в вашем зоопарке?!',
    '😡 Животные из соседнего зоопарка жалуются на громкое осуждающее рычание по ночам и не могут заснуть! Вам нужно что-то немедленно предпринять.']


# система уровней
LEVELS = {
    1: {
        "message": "",
        "xp": 0,
        "max_animals": 3,
        "base_visitors": 30,
        "optimal_price": 35,
        "features": "basic_gameplay",
        "shop_page": 1
    },
    2: {
        "message": "Теперь вам доступны:\n◆ Новая страница в магазине животных\n◆ Новый персонал\n◆ Случайные события\n\n",
        "xp": 150,
        "max_animals": 5,
        "base_visitors": 60,
        "optimal_price": 50,
        "features": "random_events",
        "shop_page": 2
    },
    3: {
        "message": "Теперь вам доступны:\n◆ Новая страница в магазине животных\n◆ Новый персонал",
        "xp": 1000,
        "max_animals": 8,
        "base_visitors": 100,
        "optimal_price": 70,
        "features": "level3",
        "shop_page": 3
    },
    4: {
        "message": "Теперь вам доступны:\n◆ Новая страница в магазине животных\n◆ Новый персонал",
        "xp": 5000,
        "max_animals": 12,
        "base_visitors": 150,
        "optimal_price": 100,
        "features": "level4",
        "shop_page": 4
    },
    5: {
        "message": "Теперь вам доступны:\n◆ Новая страница в магазине животных\n◆ Новый персонал",
        "xp": 25000,
        "max_animals": 15,
        "base_visitors": 200,
        "optimal_price": 150,
        "features": "level5",
        "shop_page": 5
    }
}


STAFF = {
    "cleaner": {
        "name": "Уборщик",
        "emoji": "🧹",
        "salary": 2500,
        "income_percent": 10,
        "level": 1,
        "description": "Повышает чистоту и увеличивает количество посетителей на 10%.",
        "bonus": "visitor_multiplier"  # +10% к посещаемости

    },
    "cashier": {
        "name": "Кассир",
        "emoji": "🏪",
        "salary": 10000,
        "income_percent": 10,
        "level": 2,
        "description": "Увеличивает доход от билетов на 10%.",
        "bonus": "income_multiplier" # +10% к доходу

    },
    "vet": {
        "name": "Ветеринар",
        "emoji": "🩺",
        "salary": 50000,
        "income_percent": 15,
        "level": 3,
        "description": "Следит за здоровьем животных и увеличивает шанс на появление потомства.",
        "bonus": "multiplier"

    },
    "guard": {
        "name": "Сторож",
        "emoji": "🛡️",
        "salary": 100000,
        "income_percent": 15,
        "level": 3,
        "description": "Снижает вероятность побега животных и предотвращает кражи.",
        "bonus": "guardion"

    },
    "feeder": {
        "name": "Смотритель",
        "emoji": "🥕",
        "salary": 250000,
        "income_percent": 20,
        "level": 4,
        "description": "Автоматически кормит животных (если хватает корма) и снижает расходы корма.",
        "bonus": "auto_feed"

    }
}


STAFF_NAME_TO_ID = {
    "уборщик": "cleaner",
    "кассир": "cashier",
    "ветеринар": "vet",
    "смотритель": "feeder",
    "сторож": "guard"
}
