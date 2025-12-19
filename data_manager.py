import json
import os
from datetime import datetime
from werkzeug.security import generate_password_hash

DATA_DIR = 'data'
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
RECIPES_FILE = os.path.join(DATA_DIR, 'recipes.json')

def ensure_data_dir():
    """Создает директорию для данных если ее нет"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def get_initial_users():
    """Возвращает начальных пользователей"""
    return [
        {
            'id': 1,
            'username': 'admin',
            'password_hash': generate_password_hash('admin123'),
            'is_admin': True,
            'email': 'admin@example.com',
            'created_at': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'id': 2,
            'username': 'user',
            'password_hash': generate_password_hash('user123'),
            'is_admin': False,
            'email': 'user@example.com',
            'created_at': datetime.now().strftime('%Y-%m-%d')
        }
    ]

def get_initial_recipes():
    """Возвращает все 100 рецептов (10 начальных + 90 сгенерированных)"""
    recipes = [
        {
            'id': 1,
            'title': 'Омлет с сыром и зеленью',
            'description': 'Простой и вкусный завтрак за 10 минут',
            'ingredients': ['Яйца - 3 шт', 'Молоко - 50 мл', 'Сыр твердый - 50 г', 'Зелень - по вкусу', 'Соль, перец - по вкусу', 'Масло растительное - 1 ст.л.'],
            'steps': '1. Взбить яйца с молоком\n2. Добавить соль и перец\n3. Натереть сыр на терке\n4. Разогреть сковороду с маслом\n5. Вылить яичную смесь\n6. Добавить сыр и зелень\n7. Жарить на среднем огне 5-7 минут',
            'image_url': 'https://source.unsplash.com/300x200/?omelet,breakfast',
            'cooking_time': 10,
            'category': 'Завтрак',
            'difficulty': 'Легкая',
            'author': 'admin',
            'rating': 4.5,
            'views': 150,
            'created_at': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'id': 2,
            'title': 'Салат Цезарь с курицей',
            'description': 'Классический салат с хрустящими сухариками',
            'ingredients': ['Куриное филе - 300 г', 'Салат романо - 1 кочан', 'Сухарики белые - 100 г', 'Сыр пармезан - 50 г', 'Соус цезарь - 3 ст.л.', 'Чеснок - 2 зубчика', 'Оливковое масло - 2 ст.л.'],
            'steps': '1. Обжарить куриное филе до готовности\n2. Порвать салат руками\n3. Натереть сыр на терке\n4. Приготовить соус\n5. Смешать все ингредиенты\n6. Добавить сухарики перед подачей',
            'image_url': 'https://source.unsplash.com/300x200/?caesar,salad',
            'cooking_time': 25,
            'category': 'Салат',
            'difficulty': 'Средняя',
            'author': 'admin',
            'rating': 4.8,
            'views': 230,
            'created_at': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'id': 3,
            'title': 'Борщ украинский',
            'description': 'Наваристый борщ со сметаной',
            'ingredients': ['Говядина на кости - 500 г', 'Свекла - 2 шт', 'Капуста белокочанная - 300 г', 'Картофель - 3 шт', 'Морковь - 1 шт', 'Лук репчатый - 1 шт', 'Томатная паста - 2 ст.л.', 'Сметана - для подачи'],
            'steps': '1. Сварить бульон из мяса (1.5 часа)\n2. Нарезать овощи\n3. Пассеровать лук, морковь и свеклу\n4. Добавить овоцы в бульон\n5. Варить еще 30 минут\n6. Добавить капусту\n7. Варить до готовности',
            'image_url': 'https://source.unsplash.com/300x200/?borscht,soup',
            'cooking_time': 90,
            'category': 'Суп',
            'difficulty': 'Сложная',
            'author': 'admin',
            'rating': 4.9,
            'views': 180,
            'created_at': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'id': 4,
            'title': 'Паста Карбонара',
            'description': 'Итальянская паста с беконом и сыром',
            'ingredients': ['Спагетти - 400 г', 'Бекон - 200 г', 'Яйца - 4 шт', 'Сыр пармезан - 100 г', 'Сливки 20% - 100 мл', 'Чеснок - 2 зубчика', 'Соль, черный перец - по вкусу'],
            'steps': '1. Отварить пасту аль денте\n2. Обжарить бекон с чесноком\n3. Взбить яйца со сливками и сыром\n4. Смешать пасту с беконом\n5. Добавить яичную смесь\n6. Быстро перемешать на выключенном огне',
            'image_url': 'https://source.unsplash.com/300x200/?pasta,carbonara',
            'cooking_time': 20,
            'category': 'Основное блюдо',
            'difficulty': 'Средняя',
            'author': 'admin',
            'rating': 4.7,
            'views': 210,
            'created_at': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'id': 5,
            'title': 'Шоколадный торт',
            'description': 'Нежный шоколадный торт без выпечки',
            'ingredients': ['Печенье песочное - 300 г', 'Шоколад темный - 200 г', 'Сливочное масло - 100 г', 'Сливки 33% - 200 мл', 'Сахарная пудра - 50 г', 'Желатин - 20 г', 'Какао - для украшения'],
            'steps': '1. Измельчить печенье в крошку\n2. Растопить шоколад и масло\n3. Смешать с печеньем\n4. Выложить в форму\n5. Приготовить крем из сливок\n6. Залить кремом основу\n7. Охлаждать 4 часа в холодильнике',
            'image_url': 'https://source.unsplash.com/300x200/?chocolate,cake',
            'cooking_time': 30,
            'category': 'Десерт',
            'difficulty': 'Средняя',
            'author': 'admin',
            'rating': 4.9,
            'views': 190,
            'created_at': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'id': 6,
            'title': 'Греческий салат',
            'description': 'Свежий овощной салат с сыром фета',
            'ingredients': ['Помидоры - 3 шт', 'Огурцы - 2 шт', 'Перец болгарский - 1 шт', 'Лук красный - 1 шт', 'Сыр фета - 200 г', 'Маслины - 100 г', 'Оливковое масло - 3 ст.л.', 'Орегано - 1 ч.л.'],
            'steps': '1. Нарезать овочи крупными кубиками\n2. Добавить маслины\n3. Поломать сыр фета руками\n4. Заправить маслом и специями\n5. Аккуратно перемешать',
            'image_url': 'https://source.unsplash.com/300x200/?greek,salad',
            'cooking_time': 15,
            'category': 'Салат',
            'difficulty': 'Легкая',
            'author': 'admin',
            'rating': 4.6,
            'views': 175,
            'created_at': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'id': 7,
            'title': 'Куриные крылышки в медовом соусе',
            'description': 'Хрустящие крылышки с сладко-острым соусом',
            'ingredients': ['Куриные крылышки - 1 кг', 'Мед - 3 ст.л.', 'Соевый соус - 4 ст.л.', 'Чеснок - 4 зубчика', 'Имбирь тертый - 1 ст.л.', 'Кунжут - для подачи', 'Зеленый лук - для украшения'],
            'steps': '1. Замариновать крылышки на 1 час\n2. Запечь в духовке 25 минут\n3. Приготовить соус\n4. Обмазать крылышки соусом\n5. Запечь еще 10 минут\n6. Посыпать кунжутом и луком',
            'image_url': 'https://source.unsplash.com/300x200/?chicken,wings',
            'cooking_time': 45,
            'category': 'Закуска',
            'difficulty': 'Средняя',
            'author': 'admin',
            'rating': 4.8,
            'views': 220,
            'created_at': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'id': 8,
            'title': 'Сырники с ягодами',
            'description': 'Нежные сырники на завтрак',
            'ingredients': ['Творог - 500 г', 'Яйца - 2 шт', 'Мука - 4 ст.л.', 'Сахар - 3 ст.л.', 'Ванилин - 1 ч.л.', 'Соль - щепотка', 'Ягоды свежие - для подачи', 'Сметана - для подачи'],
            'steps': '1. Протереть творог через сито\n2. Смешать с яйцами и сахаром\n3. Добавить муку\n4. Сформировать сырники\n5. Обжарить на среднем огне с двух сторон\n6. Подавать с ягодами и сметаной',
            'image_url': 'https://source.unsplash.com/300x200/?cheesecakes,breakfast',
            'cooking_time': 25,
            'category': 'Завтрак',
            'difficulty': 'Легкая',
            'author': 'admin',
            'rating': 4.7,
            'views': 165,
            'created_at': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'id': 9,
            'title': 'Томатный суп-пюре',
            'description': 'Густой крем-суп из томатов',
            'ingredients': ['Помидоры - 1 кг', 'Лук - 1 шт', 'Морковь - 1 шт', 'Чеснок - 3 зубчика', 'Сливки 20% - 200 мл', 'Базилик свежий - пучок', 'Оливковое масло - 2 ст.л.', 'Соль, перец - по вкусу'],
            'steps': '1. Обжарить лук и морковь\n2. Добавить помидоры\n3. Тушить 20 минут\n4. Измельчить блендером\n5. Добавить сливки\n6. Прогреть 5 минут\n7. Украсить базиликом',
            'image_url': 'https://source.unsplash.com/300x200/?tomato,soup',
            'cooking_time': 35,
            'category': 'Суп',
            'difficulty': 'Легкая',
            'author': 'admin',
            'rating': 4.5,
            'views': 140,
            'created_at': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'id': 10,
            'title': 'Пицца Маргарита',
            'description': 'Классическая итальянская пицца',
            'ingredients': ['Тесто для пиццы - 500 г', 'Помидоры - 3 шт', 'Сыр моцарелла - 250 г', 'Соус томатный - 5 ст.л.', 'Базилик свежий - пучок', 'Оливковое масло - 2 ст.л.', 'Соль, орегано - по вкусу'],
            'steps': '1. Раскатать тесто\n2. Смазать томатным соусом\n3. Выложить помидоры и сыр\n4. Посыпать специями\n5. Выпекать 15-20 минут\n6. Украсить базиликом',
            'image_url': 'https://source.unsplash.com/300x200/?pizza,margarita',
            'cooking_time': 30,
            'category': 'Основное блюдо',
            'difficulty': 'Средняя',
            'author': 'admin',
            'rating': 4.9,
            'views': 280,
            'created_at': datetime.now().strftime('%Y-%m-%d')
        }
    ]
    
    # Добавляем рецепты с 11 до 100
    RECIPE_CATEGORIES = ['Завтрак', 'Обед', 'Ужин', 'Десерт', 'Закуска', 'Салат', 'Суп', 'Основное блюдо']
    RECIPE_DIFFICULTIES = ['Легкая', 'Средняя', 'Сложная']
    
    for i in range(11, 101):
        categories = RECIPE_CATEGORIES
        difficulties = RECIPE_DIFFICULTIES
        recipe_titles = [
            f'Вкусный {categories[i % len(categories)]} номер {i}',
            f'Домашний рецепт {categories[i % len(categories)]}а',
            f'Авторский {categories[i % len(categories)]} от шеф-повара',
            f'Быстрый {categories[i % len(categories)]} на скорую руку',
            f'Праздничный {categories[i % len(categories)]}'
        ]
        
        recipes.append({
            'id': i,
            'title': recipe_titles[i % len(recipe_titles)],
            'description': f'Замечательный рецепт {categories[i % len(categories)]}а, который понравится всей семье. Идеально подходит для {["завтрака", "обеда", "ужина", "десерта", "перекуса"][i % 5]}.',
            'ingredients': [
                f'{ing} - {amount}' for ing, amount in [
                    ('Мука', f'{i % 5 + 1} ст.л.'),
                    ('Яйца', f'{i % 3 + 1} шт'),
                    ('Молоко', f'{(i % 4 + 1) * 50} мл'),
                    ('Сахар', f'{i % 3 + 1} ст.л.'),
                    ('Соль', 'по вкусу'),
                    ('Масло', f'{i % 2 + 1} ст.л.'),
                    ('Специи', 'по вкусу')
                ]
            ],
            'steps': '\n'.join([
                f'Шаг {j+1}: {step}' for j, step in enumerate([
                    'Подготовьте все ингредиенты',
                    'Тщательно перемешайте основные компоненты',
                    'Добавьте специи по вкусу',
                    f'Готовьте в течение {i % 20 + 10} минут',
                    'Подавайте блюдо горячим',
                    'Украсьте свежей зеленью'
                ][:i % 4 + 3])
            ]),
            'image_url': f'https://source.unsplash.com/300x200/?food,{categories[i % len(categories)].lower()}&sig={i}',
            'cooking_time': i % 60 + 15,
            'category': categories[i % len(categories)],
            'difficulty': difficulties[i % len(difficulties)],
            'author': 'admin',
            'rating': 4.0 + (i % 10) / 10,
            'views': i * 10,
            'created_at': datetime.now().strftime('%Y-%m-%d')
        })
    
    return recipes

def load_users():
    """Загружает пользователей из файла"""
    ensure_data_dir()
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                users = json.load(f)
                # Проверяем, что есть хотя бы админ
                if not any(user.get('username') == 'admin' for user in users):
                    users = get_initial_users()
                    save_users(users)
                return users
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    # Если файла нет или он поврежден
    users = get_initial_users()
    save_users(users)
    return users

def save_users(users):
    """Сохраняет пользователей в файл"""
    ensure_data_dir()
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def load_recipes():
    """Загружает рецепты из файла"""
    ensure_data_dir()
    if os.path.exists(RECIPES_FILE):
        try:
            with open(RECIPES_FILE, 'r', encoding='utf-8') as f:
                recipes = json.load(f)
                if not recipes:  # Если файл пустой
                    recipes = get_initial_recipes()
                    save_recipes(recipes)
                return recipes
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    # Если файла нет или он поврежден
    recipes = get_initial_recipes()
    save_recipes(recipes)
    return recipes

def save_recipes(recipes):
    """Сохраняет рецепты в файл"""
    ensure_data_dir()
    with open(RECIPES_FILE, 'w', encoding='utf-8') as f:
        json.dump(recipes, f, ensure_ascii=False, indent=2)