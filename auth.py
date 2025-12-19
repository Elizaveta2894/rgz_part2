from functools import wraps
from flask import session, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import re

# Валидационные функции
def validate_username(username):
    """Валидация имени пользователя"""
    if not username:
        return False, 'Имя пользователя обязательно'
    
    if len(username) < 3:
        return False, 'Имя пользователя должно быть не менее 3 символов'
    
    if len(username) > 50:
        return False, 'Имя пользователя должно быть не более 50 символов'
    
    # Проверка на допустимые символы
    pattern = r'^[a-zA-Z0-9_!@#$%^&*()\-+=]+$'
    if not re.match(pattern, username):
        return False, 'Имя пользователя может содержать только латинские буквы, цифры и символы: _!@#$%^&*()-+='
    
    return True, ''

def validate_password(password):
    """Валидация пароля"""
    if not password:
        return False, 'Пароль обязателен'
    
    if len(password) < 6:
        return False, 'Пароль должен быть не менее 6 символов'
    
    if len(password) > 100:
        return False, 'Пароль должен быть не более 100 символов'
    
    # Проверка на допустимые символы
    pattern = r'^[a-zA-Z0-9_!@#$%^&*()\-+=]+$'
    if not re.match(pattern, password):
        return False, 'Пароль может содержать только латинские буквы, цифры и символы: _!@#$%^&*()-+='
    
    return True, ''

def validate_email(email):
    """Валидация email"""
    if not email:
        return True, ''  # email не обязателен
    
    if len(email) > 100:
        return False, 'Email должен быть не более 100 символов'
    
    # Простая проверка формата email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, 'Неверный формат email'
    
    return True, ''

def validate_recipe_title(title):
    """Валидация названия рецепта"""
    if not title:
        return False, 'Название рецепта обязательно'
    
    if len(title) < 3:
        return False, 'Название рецепта должно быть не менее 3 символов'
    
    if len(title) > 200:
        return False, 'Название рецепта должно быть не более 200 символов'
    
    # Проверка на допустимые символы
    pattern = r'^[a-zA-Zа-яА-Я0-9\s\-_.,!?()":;\'&]+$'
    if not re.match(pattern, title):
        return False, 'Название рецепта содержит недопустимые символы'
    
    return True, ''

def validate_recipe_description(description):
    """Валидация описания рецепта"""
    if not description:
        return True, ''  # описание не обязательно
    
    if len(description) > 1000:
        return False, 'Описание рецепта должно быть не более 1000 символов'
    
    return True, ''

def validate_recipe_steps(steps):
    """Валидация шагов приготовления"""
    if not steps:
        return False, 'Шаги приготовления обязательны'
    
    if len(steps) < 10:
        return False, 'Шаги приготовления должны быть не менее 10 символов'
    
    if len(steps) > 5000:
        return False, 'Шаги приготовления должны быть не более 5000 символов'
    
    return True, ''

def validate_cooking_time(cooking_time):
    """Валидация времени приготовления"""
    if not isinstance(cooking_time, (int, float)):
        return False, 'Время приготовления должно быть числом'
    
    if cooking_time <= 0:
        return False, 'Время приготовления должно быть положительным'
    
    if cooking_time > 1440:  # 24 часа в минутах
        return False, 'Время приготовления не может превышать 24 часа'
    
    return True, ''

def validate_ingredients(ingredients):
    """Валидация списка ингредиентов"""
    if not ingredients or len(ingredients) == 0:
        return False, 'Должен быть хотя бы один ингредиент'
    
    if len(ingredients) > 50:
        return False, 'Не более 50 ингредиентов'
    
    for ingredient in ingredients:
        if len(ingredient) > 200:
            return False, f'Ингредиент слишком длинный: {ingredient[:50]}...'
    
    return True, ''

def validate_image_url(image_url):
    """Валидация URL изображения"""
    if not image_url:
        return True, ''  # URL не обязателен
    
    if len(image_url) > 500:
        return False, 'URL изображения слишком длинный'
    
    # Простая проверка URL
    if not (image_url.startswith('http://') or image_url.startswith('https://')):
        return False, 'URL должен начинаться с http:// или https://'
    
    return True, ''

def validate_category(category):
    """Валидация категории"""
    if not category:
        return False, 'Категория обязательна'
    
    valid_categories = ['Завтрак', 'Обед', 'Ужин', 'Десерт', 'Закуска', 'Салат', 'Суп', 'Основное блюдо']
    if category not in valid_categories:
        return False, f'Недопустимая категория. Допустимые значения: {", ".join(valid_categories)}'
    
    return True, ''

def validate_difficulty(difficulty):
    """Валидация сложности"""
    if not difficulty:
        return False, 'Сложность обязательна'
    
    valid_difficulties = ['Легкая', 'Средняя', 'Сложная']
    if difficulty not in valid_difficulties:
        return False, f'Недопустимая сложность. Допустимые значения: {", ".join(valid_difficulties)}'
    
    return True, ''

def validate_rating(rating):
    """Валидация рейтинга"""
    if not isinstance(rating, (int, float)):
        return False, 'Рейтинг должен быть числом'
    
    if rating < 0 or rating > 5:
        return False, 'Рейтинг должен быть от 0 до 5'
    
    return True, ''

def validate_recipe_data(data, is_update=False):
    """Валидация всех данных рецепта"""
    errors = {}
    
    if 'title' in data:
        valid, error = validate_recipe_title(data['title'])
        if not valid:
            errors['title'] = error
    
    if 'description' in data and data['description']:
        valid, error = validate_recipe_description(data['description'])
        if not valid:
            errors['description'] = error
    
    if 'ingredients' in data:
        ingredients_list = data['ingredients']
        if isinstance(ingredients_list, str):
            ingredients_list = [i.strip() for i in ingredients_list.split('\n') if i.strip()]
        valid, error = validate_ingredients(ingredients_list)
        if not valid:
            errors['ingredients'] = error
    
    if 'steps' in data:
        valid, error = validate_recipe_steps(data['steps'])
        if not valid:
            errors['steps'] = error
    
    if 'cooking_time' in data and data['cooking_time'] is not None:
        try:
            cooking_time = int(data['cooking_time'])
            valid, error = validate_cooking_time(cooking_time)
            if not valid:
                errors['cooking_time'] = error
        except (ValueError, TypeError):
            errors['cooking_time'] = 'Время приготовления должно быть числом'
    
    if 'image_url' in data and data['image_url']:
        valid, error = validate_image_url(data['image_url'])
        if not valid:
            errors['image_url'] = error
    
    if 'category' in data and data['category']:
        valid, error = validate_category(data['category'])
        if not valid:
            errors['category'] = error
    
    if 'difficulty' in data and data['difficulty']:
        valid, error = validate_difficulty(data['difficulty'])
        if not valid:
            errors['difficulty'] = error
    
    if 'rating' in data and data['rating'] is not None:
        try:
            rating = float(data['rating'])
            valid, error = validate_rating(rating)
            if not valid:
                errors['rating'] = error
        except (ValueError, TypeError):
            errors['rating'] = 'Рейтинг должен быть числом'
    
    return errors

# Функции аутентификации
def get_current_user(users_list):
    """Получение текущего пользователя"""
    user_id = session.get('user_id')
    username = session.get('username')
    
    if user_id and username:
        for user in users_list:
            if user['id'] == user_id and user['username'] == username:
                return user
    return None

def is_admin(users_list):
    """Проверка прав администратора"""
    user = get_current_user(users_list)
    return user and user.get('is_admin', False)

def verify_password(password_hash, password):
    """Проверка пароля"""
    return check_password_hash(password_hash, password)

def authenticate_user(username, password, users_list):
    """Аутентификация пользователя"""
    for user in users_list:
        if user['username'] == username:
            if verify_password(user['password_hash'], password):
                return user
    return None

def login_user(user_id, username, is_admin_flag=False):
    """Вход пользователя"""
    session['user_id'] = user_id
    session['username'] = username
    session['is_admin'] = is_admin_flag

def logout_user():
    """Выход пользователя"""
    session.clear()

def register_user(username, password, email, users_list):
    """Регистрация нового пользователя"""
    # Проверяем, существует ли пользователь с таким именем
    for user in users_list:
        if user['username'] == username:
            return None, 'Пользователь с таким именем уже существует'
    
    # Генерируем новый ID
    new_id = max([user['id'] for user in users_list], default=0) + 1
    
    # Создаем нового пользователя
    new_user = {
        'id': new_id,
        'username': username,
        'password_hash': generate_password_hash(password),
        'is_admin': False,
        'email': email,
        'created_at': None  # Будет установлено позже
    }
    
    return new_user, None

# Декораторы для проверки аутентификации
def login_required_html(f):
    """Декоратор для HTML маршрутов"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or 'username' not in session:
            flash('Требуется авторизация', 'danger')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required_html(f):
    """Декоратор для HTML маршрутов (только админ)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or 'username' not in session:
            flash('Требуется авторизация', 'danger')
            return redirect(url_for('login', next=request.url))
        if not session.get('is_admin'):
            flash('Требуются права администратора', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def login_required_jsonrpc(method):
    """Декоратор для JSON-RPC методов"""
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.get_current_user():
            raise JSONRPCError(-32001, 'Требуется авторизация')
        return method(self, *args, **kwargs)
    return wrapper

def admin_required_jsonrpc(method):
    """Декоратор для JSON-RPC методов (только админ)"""
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.get_current_user():
            raise JSONRPCError(-32001, 'Требуется авторизация')
        if not self.is_admin():
            raise JSONRPCError(-32002, 'Требуются права администратора')
        return method(self, *args, **kwargs)
    return wrapper

# Исключение для JSON-RPC ошибок
class JSONRPCError(Exception):
    def __init__(self, code, message, data=None):
        self.code = code
        self.message = message
        self.data = data