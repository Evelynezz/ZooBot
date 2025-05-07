animals = {
    'кот': {
        'price': 200,
        'visitor_multiplier': 0.1,
        'feed_cost': 5,
        'emoji': '🐈',
        'initial_count': 1,
        'min_rep': 10
    },
    'кролик': {
        'price': 400,
        'visitor_multiplier': 0.2,
        'feed_cost': 10,
        'emoji': '🐇',
        'min_rep': 15
    },
    'ёж': {
        'price': 600,
        'visitor_multiplier': 0.25,
        'feed_cost': 15,
        'emoji': '🦔',
        'min_rep': 20
    },
    'попугай': {
        'price': 800,
        'visitor_multiplier': 0.4,
        'feed_cost': 20,
        'emoji': '🦜',
        'min_rep': 25
    },
    'черепаха': {
        'price': 1000,
        'visitor_multiplier': 0.5,
        'feed_cost': 25,
        'emoji': '🐢',
        'min_rep': 30
    },
    'змея': {
        'price': 1300,
        'visitor_multiplier': 0.65,
        'feed_cost': 30,
        'emoji': '🐍',
        'min_rep': 35
    },
    'лиса': {
        'price': 1750,
        'visitor_multiplier': 0.85,
        'feed_cost': 35,
        'emoji': '🦊',
        'min_rep': 40
    },
    'обезьяна': {
        'price': 2000,
        'visitor_multiplier': 1.0,
        'feed_cost': 40,
        'emoji': '🐒',
        'min_rep': 45
    },
    'коала': {
        'price': 2300,
        'visitor_multiplier': 1.15,
        'feed_cost': 45,
        'emoji': '🐨',
        'min_rep': 50
    },
    'ленивец': {
        'price': 2750,
        'visitor_multiplier': 1.4,
        'feed_cost': 50,
        'emoji': '🦥',
        'min_rep': 55
    },
    'лама': {
        'price': 3000,
        'visitor_multiplier': 1.5,
        'feed_cost': 55,
        'emoji': '🦙',
        'min_rep': 60
    },
    'бурый медведь': {
        'price': 3500,
        'visitor_multiplier': 1.75,
        'feed_cost': 65,
        'emoji': '🐻',
        'min_rep': 65
    },
    'белый медведь': {
        'price': 4000,
        'visitor_multiplier': 2.0,
        'feed_cost': 70,
        'emoji': '🐻‍❄️',
        'min_rep': 70
    },
    'панда': {
        'price': 4500,
        'visitor_multiplier': 2.25,
        'feed_cost': 75,
        'emoji': '🐼️',
        'min_rep': 75
    },
    'тигр': {
        'price': 5000,
        'visitor_multiplier': 2.5,
        'feed_cost': 80,
        'emoji': '🐅',
        'min_rep': 80
    },
    'бегемот': {
        'price': 5500,
        'visitor_multiplier': 2.75,
        'feed_cost': 85,
        'emoji': '🦛',
        'min_rep': 85
    },
    'носорог': {
        'price': 6000,
        'visitor_multiplier': 3.0,
        'feed_cost': 90,
        'emoji': '🦏',
        'min_rep': 80
    },
    'крокодил': {
        'price': 7000,
        'visitor_multiplier': 3.5,
        'feed_cost': 95,
        'emoji': '🐊',
        'min_rep': 90
    },
    'жираф': {
        'price': 8000,
        'visitor_multiplier': 4.0,
        'feed_cost': 100,
        'emoji': '🦒',
        'min_rep': 95
    },
    'слон': {
        'price': 10000,
        'visitor_multiplier': 5.0,
        'feed_cost': 120,
        'emoji': '🐘',
        'min_rep': 100
    }


}


food = {
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
        "message": "💰 Сегодня отмечается день щедрости! Ваши посетители оставили вам чаевые - {amount} монет!",
        "min_amount": 50,
        "max_amount": 150,
        "emoji": "🎁"
    },
    "animal_show": {
        "type": "reputation",
        "message": '📰 Журнал "National Zoo" написал положительную статью о вашем зоопарке!\n Репутация возросла на {amount} единиц!',
        "min_amount": 5,
        "max_amount": 10,
        "emoji": "✨"
    },

    # Негативные
    "vandalism": {
        "type": "money",
        "message": "💵 Этой ночью кто-то пробрался в ваш зоопарк и украл {amount} монет!",
        "min_amount": -150,
        "max_amount": -50,
        "emoji": "💢"
    },
    "illness": {
        "type": "money",
        "message": "🤒 Один из ваших питомцев заболел!\nРасходы на лечение: {amount} монет.",
        "min_amount": -300,
        "max_amount": -150,
        "emoji": "💢"
    },
    "food_theft": {
        "type": "feed",
        "message": "🦝 Еноты пробрались на склад!\n У вас украли {amount} единиц корма.",
        "min_amount": -50,
        "max_amount": -20,
        "emoji": "💢"
    }
}


# рандомные фразы инспектора
inspector_phrases = [
    '👮 Инспектор зоопарков на связи! Если ты не начнешь кормить своих животных, они могут начать писать мемуары о своей голодной жизни!',
    '👮 Инспектор зоопарков: "Если вы не покормите своих животных, то они начнут требовать зарплату за свою работу по развлечению посетителей!"',
    '📞 Ало! Это Инспектор зоопарков. Мне поступают многочисленные жалобы от ваших животных! Вам следует немедленно покормить их.',
    '😿 Это служба защиты животных. Вчера в наш главный офис пришёл ваш кот, который был вынужден перейти на веганскую диету. Что происходит в вашем зоопарке?!',
    '😡 Животные из соседнего зоопарка жалуются на громкое осуждающее рычание по ночам и не могут заснуть! Вам нужно что-то немедленно предпринять.']
