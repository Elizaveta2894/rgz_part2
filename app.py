import json
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from datetime import datetime

# Импорты из созданных модулей
from auth import (
    validate_username, validate_password, validate_email,
    validate_recipe_title, validate_recipe_description, validate_recipe_steps,
    validate_cooking_time, validate_ingredients, validate_image_url,
    validate_category, validate_difficulty, validate_rating,
    validate_recipe_data, login_required_html, admin_required_html,
    get_current_user, is_admin, verify_password, authenticate_user,
    login_user, logout_user, register_user
)
from config import Config
from jsonrpc_handler import JSONRPCHandler, JSONRPCError
from data_manager import load_users, load_recipes, save_users, save_recipes

app = Flask(__name__)
app.config.from_object(Config)

# Константы категорий и сложностей
RECIPE_CATEGORIES = ['Завтрак', 'Обед', 'Ужин', 'Десерт', 'Закуска', 'Салат', 'Суп', 'Основное блюдо']
RECIPE_DIFFICULTIES = ['Легкая', 'Средняя', 'Сложная']

STUDENT_INFO = {
    'fio': Config.STUDENT_FIO,
    'group': Config.STUDENT_GROUP
}

# Функция для сохранения всех данных
def save_all_data():
    """Сохраняет все данные в файлы"""
    save_users(users)
    save_recipes(recipes)
    print("✅ Данные сохранены в файлы")

# Загружаем данные из файлов
users = load_users()
recipes = load_recipes()

# Добавляем данные в конфиг для доступа из других модулей
app.config['USERS_LIST'] = users
app.config['RECIPES_LIST'] = recipes

# Инициализация JSON-RPC обработчика
jsonrpc_handler = JSONRPCHandler(recipes, users)

# ========== HTML МАРШРУТЫ ==========

@app.context_processor
def inject_stats():
    """Добавляет статистику во все шаблоны"""
    stats = get_current_stats()
    return {
        'student_info': STUDENT_INFO,
        'recipes_count': stats['recipes_count'],
        'users_count': stats['users_count'],
        'total_cooking_time': stats['total_cooking_time'],
        'categories_count': stats['categories_count']
    }

def get_current_stats():
    """Получение актуальной статистики"""
    total_cooking_time = sum(recipe.get('cooking_time', 0) for recipe in recipes)
    categories = set(recipe['category'] for recipe in recipes)
    
    return {
        'recipes_count': len(recipes),
        'users_count': len(users),
        'total_cooking_time': total_cooking_time,
        'categories_count': len(categories)
    }

@app.route('/')
def index():
    """Главная страница"""
    recent_recipes = recipes[:12]
    popular_recipes = sorted(recipes, key=lambda x: x.get('views', 0), reverse=True)[:6]
    
    stats = get_current_stats()
    
    return render_template(
        'index.html',
        student_info=STUDENT_INFO,
        current_user=get_current_user(users),
        recent_recipes=recent_recipes,
        popular_recipes=popular_recipes,
        recipes_count=stats['recipes_count'],
        users_count=stats['users_count'],
        total_cooking_time=stats['total_cooking_time'],
        categories_count=stats['categories_count']
    )

@app.route('/search')
def search_page():
    """Страница поиска"""
    categories = list(set([r['category'] for r in recipes]))
    difficulties = list(set([r['difficulty'] for r in recipes]))
    
    stats = get_current_stats()
    
    return render_template(
        'search.html',
        student_info=STUDENT_INFO,
        current_user=get_current_user(users),
        categories=categories,
        difficulties=difficulties,
        recipes_count=stats['recipes_count'],
        users_count=stats['users_count'],
        total_cooking_time=stats['total_cooking_time'],
        categories_count=stats['categories_count']
    )

@app.route('/recipes')
def all_recipes():
    """Все рецепты"""
    page = request.args.get('page', 1, type=int)
    per_page = 12
    start = (page - 1) * per_page
    end = start + per_page
    
    paginated_recipes = recipes[start:end]
    
    stats = get_current_stats()
    
    return render_template(
        'all_recipes.html',
        student_info=STUDENT_INFO,
        current_user=get_current_user(users),
        recipes=paginated_recipes,
        page=page,
        total_pages=(stats['recipes_count'] + per_page - 1) // per_page,
        recipes_count=stats['recipes_count'],
        users_count=stats['users_count'],
        total_cooking_time=stats['total_cooking_time'],
        categories_count=stats['categories_count']
    )

@app.route('/recipe/<int:recipe_id>')
def recipe_detail(recipe_id):
    """Страница рецепта"""
    recipe = next((r for r in recipes if r['id'] == recipe_id), None)
    
    if not recipe:
        flash('Рецепт не найден', 'danger')
        return redirect(url_for('index'))
    
    if recipe.get('cooking_time', 0) <= 0:
        flash('Внимание: время приготовления указано некорректно', 'warning')
    
    recipe['views'] = recipe.get('views', 0) + 1
    save_all_data()
    
    stats = get_current_stats()
    
    return render_template(
        'recipe_detail.html',
        student_info=STUDENT_INFO,
        current_user=get_current_user(users),
        recipe=recipe,
        recipes_count=stats['recipes_count'],
        users_count=stats['users_count'],
        total_cooking_time=stats['total_cooking_time'],
        categories_count=stats['categories_count']
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа"""
    if get_current_user(users):
        return redirect(url_for('index'))
    
    stats = get_current_stats()
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        username_valid, username_error = validate_username(username)
        if not username_valid:
            flash(f'Ошибка валидации логина: {username_error}', 'danger')
            return render_template('login.html',
                                 student_info=STUDENT_INFO,
                                 current_user=get_current_user(users),
                                 recipes_count=stats['recipes_count'])
        
        password_valid, password_error = validate_password(password)
        if not password_valid:
            flash(f'Ошибка валидации пароля: {password_error}', 'danger')
            return render_template('login.html',
                                 student_info=STUDENT_INFO,
                                 current_user=get_current_user(users),
                                 recipes_count=stats['recipes_count'])

        user = authenticate_user(username, password, users)
        if user:
            login_user(user['id'], user['username'], user.get('is_admin', False))
            flash('Вы успешно вошли в систему!', 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        
        flash('Неверное имя пользователя или пароль', 'danger')
    
    return render_template(
        'login.html',
        student_info=STUDENT_INFO,
        current_user=get_current_user(users),
        recipes_count=stats['recipes_count'],
        users_count=stats['users_count'],
        total_cooking_time=stats['total_cooking_time'],
        categories_count=stats['categories_count']
    )

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Страница регистрации"""
    if get_current_user(users):
        return redirect(url_for('index'))
    
    stats = get_current_stats()
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        email = request.form.get('email', '').strip()

        username_valid, username_error = validate_username(username)
        if not username_valid:
            flash(f'Ошибка валидации логина: {username_error}', 'danger')
            return render_template('register.html',
                                 student_info=STUDENT_INFO,
                                 current_user=get_current_user(users),
                                 recipes_count=stats['recipes_count'])
        
        password_valid, password_error = validate_password(password)
        if not password_valid:
            flash(f'Ошибка валидации пароля: {password_error}', 'danger')
            return render_template('register.html',
                                 student_info=STUDENT_INFO,
                                 current_user=get_current_user(users),
                                 recipes_count=stats['recipes_count'])
        
        if password != confirm_password:
            flash('Пароли не совпадают', 'danger')
            return render_template('register.html',
                                 student_info=STUDENT_INFO,
                                 current_user=get_current_user(users),
                                 recipes_count=stats['recipes_count'])
        
        email_valid, email_error = validate_email(email)
        if not email_valid:
            flash(f'Ошибка валидации email: {email_error}', 'danger')
            return render_template('register.html',
                                 student_info=STUDENT_INFO,
                                 current_user=get_current_user(users),
                                 recipes_count=stats['recipes_count'])
        
        new_user, error = register_user(username, password, email, users)
        if error:
            flash(error, 'danger')
            return render_template('register.html',
                                 student_info=STUDENT_INFO,
                                 current_user=get_current_user(users),
                                 recipes_count=stats['recipes_count'])
        
        # Хешируем пароль
        new_user['password_hash'] = generate_password_hash(password)
        new_user['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        users.append(new_user)
        save_all_data()
        
        login_user(new_user['id'], new_user['username'], new_user['is_admin'])
        
        flash('Регистрация успешна! Добро пожаловать!', 'success')
        return redirect(url_for('index'))
    
    return render_template('register.html',
                         student_info=STUDENT_INFO,
                         current_user=get_current_user(users),
                         recipes_count=stats['recipes_count'],
                         users_count=stats['users_count'],
                         total_cooking_time=stats['total_cooking_time'],
                         categories_count=stats['categories_count'])

@app.route('/logout')
def logout():
    """Выход"""
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

@app.route('/admin')
@admin_required_html
def admin_panel():
    """Админ-панель"""
    stats = get_current_stats()
    
    invalid_recipes = []
    for recipe in recipes:
        if recipe.get('cooking_time', 0) <= 0:
            invalid_recipes.append(recipe)
    
    safe_users = []
    for user in users:
        safe_user = user.copy()
        if 'password_hash' in safe_user:
            safe_user.pop('password_hash')
        safe_users.append(safe_user)
    
    # ИЗМЕНЕНО: показываем все рецепты, а не только первые 20
    return render_template(
        'admin.html',
        student_info=STUDENT_INFO,
        current_user=get_current_user(users),
        recipes=recipes,  # ← Вместо recipes[:20]
        users=safe_users,
        recipes_count=stats['recipes_count'],
        users_count=stats['users_count'],
        total_cooking_time=stats['total_cooking_time'],
        categories_count=stats['categories_count'],
        invalid_recipes=invalid_recipes[:10]  # Можно оставить только 10 проблемных
    )
    
@app.route('/test-api')
def test_api_page():
    """Тестирование API"""
    stats = get_current_stats()
    
    return render_template(
        'test_api.html',
        student_info=STUDENT_INFO,
        current_user=get_current_user(users),
        recipes_count=stats['recipes_count'],
        users_count=stats['users_count'],
        total_cooking_time=stats['total_cooking_time'],
        categories_count=stats['categories_count']
    )

@app.route('/author')
def author_page():
    """Страница об авторе"""
    stats = get_current_stats()
    
    return render_template(
        'author.html',
        student_info=STUDENT_INFO,
        current_user=get_current_user(users),
        recipes_count=stats['recipes_count'],
        users_count=stats['users_count'],
        total_cooking_time=stats['total_cooking_time'],
        categories_count=stats['categories_count']
    )

@app.route('/delete-account', methods=['POST'])
@login_required_html
def delete_account():
    """Удаление аккаунта пользователя"""
    user = get_current_user(users)
    
    if user['is_admin'] and user['username'] == 'admin':
        flash('Нельзя удалить администратора системы', 'danger')
        return redirect(url_for('index'))
    
    # Используем JSON-RPC метод для удаления
    response = jsonrpc_handler.delete_account()
    
    if response and isinstance(response, dict) and response.get('success'):
        save_all_data()
        flash('Ваш аккаунт был успешно удален', 'info')
        return redirect(url_for('index'))
    else:
        flash('Ошибка при удалении аккаунта', 'danger')
        return redirect(url_for('index'))

@app.route('/validation-info')
def validation_info():
    """Страница с информацией о валидации"""
    validation_rules = {
        'username': {
            'min_length': 3,
            'max_length': 50,
            'allowed_chars': 'латинские буквы, цифры и символы: _!@#$%^&*()-+='
        },
        'password': {
            'min_length': 6,
            'max_length': 100,
            'allowed_chars': 'латинские буквы, цифры и символы: _!@#$%^&*()-+=',
            'security_info': 'Пароли хранятся в захешированном виде с солью'
        },
        'email': {
            'max_length': 100,
            'format': 'example@domain.com',
            'required': False
        },
        'recipe_title': {
            'min_length': 3,
            'max_length': 200,
            'allowed_chars': 'буквы, цифры, пробелы и символы: -_.,!?()":;\'&'
        },
        'recipe_description': {
            'max_length': 1000,
            'required': False
        },
        'recipe_steps': {
            'min_length': 10,
            'max_length': 5000
        },
        'cooking_time': {
            'min_value': 1,
            'max_value': 1440,
            'unit': 'минуты'
        },
        'ingredients': {
            'min_count': 1,
            'max_count': 50,
            'max_length_per_ingredient': 200
        }
    }
    
    stats = get_current_stats()
    
    return render_template(
        'validation_info.html',
        student_info=STUDENT_INFO,
        current_user=get_current_user(users),
        validation_rules=validation_rules,
        recipes_count=stats['recipes_count'],
        users_count=stats['users_count'],
        total_cooking_time=stats['total_cooking_time'],
        categories_count=stats['categories_count']
    )

@app.route('/security-info')
def security_info():
    """Страница с информацией о безопасности"""
    security_features = {
        'password_hashing': {
            'enabled': True,
            'algorithm': 'pbkdf2:sha256',
            'salt': True,
            'description': 'Пароли хранятся в виде криптографических хешей с уникальной солью для каждого пользователя'
        },
        'session_management': {
            'secure_cookies': True,
            'httponly': True,
            'session_timeout': 'при закрытии браузера'
        },
        'data_validation': {
            'input_validation': True,
            'output_encoding': True,
            'sql_injection_protection': 'N/A (in-memory storage)'
        },
        'authentication': {
            'password_min_length': 6,
            'password_complexity': 'латинские буквы, цифры и специальные символы',
            'login_attempts': 'не ограничено (в демо-версии)'
        }
    }
    
    stats = get_current_stats()
    
    return render_template(
        'security_info.html',
        student_info=STUDENT_INFO,
        current_user=get_current_user(users),
        security_features=security_features,
        recipes_count=stats['recipes_count'],
        users_count=stats['users_count'],
        total_cooking_time=stats['total_cooking_time'],
        categories_count=stats['categories_count']
    )

@app.route('/admin/edit-recipe/<int:recipe_id>', methods=['GET', 'POST'])
@admin_required_html
def edit_recipe(recipe_id):
    """Редактирование рецепта администратором"""
    recipe = next((r for r in recipes if r['id'] == recipe_id), None)
    
    if not recipe:
        flash('Рецепт не найден', 'danger')
        return redirect(url_for('admin_panel'))
    
    stats = get_current_stats()
    
    if request.method == 'POST':
        # Получаем данные из формы
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        ingredients = request.form.get('ingredients', '').strip()
        steps = request.form.get('steps', '').strip()
        image_url = request.form.get('image_url', '').strip()
        cooking_time = request.form.get('cooking_time', '').strip()
        category = request.form.get('category', '').strip()
        difficulty = request.form.get('difficulty', '').strip()
        rating = request.form.get('rating', '').strip()
        
        # Валидация данных
        errors = {}
        
        title_valid, title_error = validate_recipe_title(title)
        if not title_valid:
            errors['title'] = title_error
        
        desc_valid, desc_error = validate_recipe_description(description)
        if not desc_valid:
            errors['description'] = desc_error
        
        ingredients_list = [i.strip() for i in ingredients.split('\n') if i.strip()]
        ing_valid, ing_error = validate_ingredients(ingredients_list)
        if not ing_valid:
            errors['ingredients'] = ing_error
        
        steps_valid, steps_error = validate_recipe_steps(steps)
        if not steps_valid:
            errors['steps'] = steps_error
        
        if cooking_time:
            try:
                cooking_time_int = int(cooking_time)
                time_valid, time_error = validate_cooking_time(cooking_time_int)
                if not time_valid:
                    errors['cooking_time'] = time_error
            except ValueError:
                errors['cooking_time'] = 'Время приготовления должно быть числом'
        
        if image_url:
            img_valid, img_error = validate_image_url(image_url)
            if not img_valid:
                errors['image_url'] = img_error
        
        cat_valid, cat_error = validate_category(category)
        if not cat_valid:
            errors['category'] = cat_error
        
        diff_valid, diff_error = validate_difficulty(difficulty)
        if not diff_valid:
            errors['difficulty'] = diff_error
        
        if rating:
            try:
                rating_float = float(rating)
                rating_valid, rating_error = validate_rating(rating_float)
                if not rating_valid:
                    errors['rating'] = rating_error
            except ValueError:
                errors['rating'] = 'Рейтинг должен быть числом'
        
        if errors:
            for field, error in errors.items():
                flash(f'{field}: {error}', 'danger')
            return render_template('edit_recipe.html',
                                 student_info=STUDENT_INFO,
                                 current_user=get_current_user(users),
                                 recipe=recipe,
                                 recipes_count=stats['recipes_count'],
                                 categories=RECIPE_CATEGORIES,
                                 difficulties=RECIPE_DIFFICULTIES)
        
        # Обновляем рецепт
        recipe['title'] = title
        recipe['description'] = description
        recipe['ingredients'] = ingredients_list
        recipe['steps'] = steps
        if image_url:
            recipe['image_url'] = image_url
        if cooking_time:
            recipe['cooking_time'] = int(cooking_time)
        recipe['category'] = category
        recipe['difficulty'] = difficulty
        if rating:
            recipe['rating'] = float(rating)
        
        save_all_data()
        
        flash('Рецепт успешно обновлен!', 'success')
        return redirect(url_for('admin_panel'))
    
    return render_template('edit_recipe.html',
                         student_info=STUDENT_INFO,
                         current_user=get_current_user(users),
                         recipe=recipe,
                         recipes_count=stats['recipes_count'],
                         categories=RECIPE_CATEGORIES,
                         difficulties=RECIPE_DIFFICULTIES)

@app.route('/admin/delete-recipe/<int:recipe_id>', methods=['POST'])
@admin_required_html
def delete_recipe_route(recipe_id):
    """Быстрое удаление рецепта из админ-панели"""
    global recipes
    initial_count = len(recipes)
    
    recipes = [r for r in recipes if r['id'] != recipe_id]
    
    if len(recipes) < initial_count:
        save_all_data()
        flash(f'Рецепт с ID {recipe_id} успешно удален', 'success')
    else:
        flash(f'Рецепт с ID {recipe_id} не найден', 'danger')
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/create-recipe', methods=['GET', 'POST'])
@admin_required_html
def create_recipe():
    """Создание нового рецепта администратором"""
    stats = get_current_stats()
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        ingredients = request.form.get('ingredients', '').strip()
        steps = request.form.get('steps', '').strip()
        image_url = request.form.get('image_url', '').strip()
        cooking_time = request.form.get('cooking_time', '').strip()
        category = request.form.get('category', '').strip()
        difficulty = request.form.get('difficulty', '').strip()
        
        errors = {}
        
        title_valid, title_error = validate_recipe_title(title)
        if not title_valid:
            errors['title'] = title_error
        
        desc_valid, desc_error = validate_recipe_description(description)
        if not desc_valid:
            errors['description'] = desc_error
        
        ingredients_list = [i.strip() for i in ingredients.split('\n') if i.strip()]
        ing_valid, ing_error = validate_ingredients(ingredients_list)
        if not ing_valid:
            errors['ingredients'] = ing_error
        
        steps_valid, steps_error = validate_recipe_steps(steps)
        if not steps_valid:
            errors['steps'] = steps_error
        
        if cooking_time:
            try:
                cooking_time_int = int(cooking_time)
                time_valid, time_error = validate_cooking_time(cooking_time_int)
                if not time_valid:
                    errors['cooking_time'] = time_error
            except ValueError:
                errors['cooking_time'] = 'Время приготовления должно быть числом'
        else:
            errors['cooking_time'] = 'Время приготовления обязательно'
        
        if image_url:
            img_valid, img_error = validate_image_url(image_url)
            if not img_valid:
                errors['image_url'] = img_error
        
        cat_valid, cat_error = validate_category(category)
        if not cat_valid:
            errors['category'] = cat_error
        
        diff_valid, diff_error = validate_difficulty(difficulty)
        if not diff_valid:
            errors['difficulty'] = diff_error
        
        if errors:
            for field, error in errors.items():
                flash(f'{field}: {error}', 'danger')
            
            return render_template('create_recipe.html',
                                 student_info=STUDENT_INFO,
                                 current_user=get_current_user(users),
                                 recipes_count=stats['recipes_count'],
                                 categories=RECIPE_CATEGORIES,
                                 difficulties=RECIPE_DIFFICULTIES,
                                 form_data=request.form)
        
        new_id = max([r['id'] for r in recipes], default=0) + 1
        current_user = get_current_user(users)
        
        new_recipe = {
            'id': new_id,
            'title': title,
            'description': description,
            'ingredients': ingredients_list,
            'steps': steps,
            'image_url': image_url if image_url else f'https://source.unsplash.com/300x200/?food,recipe&sig={new_id}',
            'cooking_time': int(cooking_time),
            'category': category,
            'difficulty': difficulty,
            'author': current_user['username'] if current_user else 'admin',
            'rating': 4.0,
            'views': 0,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        recipes.append(new_recipe)
        save_all_data()
        
        flash(f'Рецепт "{title}" успешно создан!', 'success')
        return redirect(url_for('admin_panel'))
    
    return render_template('create_recipe.html',
                         student_info=STUDENT_INFO,
                         current_user=get_current_user(users),
                         recipes_count=stats['recipes_count'],
                         categories=RECIPE_CATEGORIES,
                         difficulties=RECIPE_DIFFICULTIES)

@app.route('/admin/fix-recipe/<int:recipe_id>', methods=['POST'])
@admin_required_html
def fix_recipe(recipe_id):
    """Исправление проблемного рецепта"""
    recipe = next((r for r in recipes if r['id'] == recipe_id), None)
    
    if not recipe:
        flash('Рецепт не найден', 'danger')
        return redirect(url_for('admin_panel'))
    
    if recipe['cooking_time'] <= 0:
        recipe['cooking_time'] = 30
        save_all_data()
        flash(f'Время приготовления рецепта "{recipe["title"]}" исправлено на 30 минут', 'success')
    else:
        flash('Рецепт не требует исправлений', 'info')
    
    return redirect(url_for('admin_panel'))

@app.route('/init')
def init_database():
    """Инициализация тестовых данных"""
    try:
        global users
        
        # Добавляем тестовых пользователей
        test_users = [
            ('alice', 'password123', 'alice@example.com'),
            ('bob', 'password123', 'bob@example.com'),
            ('charlie', 'password123', 'charlie@example.com'),
            ('diana', 'password123', 'diana@example.com'),
            ('eve', 'password123', 'eve@example.com')
        ]
        
        existing_usernames = [user['username'] for user in users]
        new_users_created = 0
        
        for username, password, email in test_users:
            if username not in existing_usernames:
                new_user = {
                    'id': max([u['id'] for u in users], default=0) + 1,
                    'username': username,
                    'password_hash': generate_password_hash(password),
                    'is_admin': False,
                    'email': email,
                    'created_at': datetime.now().strftime('%Y-%m-%d')
                }
                users.append(new_user)
                existing_usernames.append(username)
                new_users_created += 1
        
        # Обновляем данные в конфиге
        app.config['USERS_LIST'] = users
        app.config['RECIPES_LIST'] = recipes
        
        save_all_data()
        
        return f'''
            <!DOCTYPE html>
            <html lang="ru">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Инициализация данных</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        max-width: 800px;
                        margin: 50px auto;
                        padding: 20px;
                        background-color: #f5f5f5;
                    }}
                    .container {{
                        background-color: white;
                        padding: 30px;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    .success {{
                        color: #2e7d32;
                        font-weight: bold;
                    }}
                    .user-list {{
                        background-color: #f8f9fa;
                        padding: 15px;
                        border-radius: 5px;
                        margin: 20px 0;
                    }}
                    ul {{
                        list-style-type: none;
                        padding: 0;
                    }}
                    li {{
                        padding: 5px 0;
                    }}
                    .stats {{
                        background-color: #e8f5e9;
                        padding: 15px;
                        border-radius: 5px;
                        margin: 20px 0;
                    }}
                    .btn {{
                        display: inline-block;
                        background-color: #4CAF50;
                        color: white;
                        padding: 10px 20px;
                        text-decoration: none;
                        border-radius: 5px;
                        margin-top: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1 class="success">✅ Данные успешно инициализированы!</h1>
                    
                    <div class="stats">
                        <h2>Статистика системы:</h2>
                        <p><strong>Пользователей:</strong> {len(users)}</p>
                        <p><strong>Рецептов:</strong> {len(recipes)}</p>
                        <p><strong>Категорий:</strong> {len(set([r['category'] for r in recipes]))}</p>
                    </div>
                    
                    <div class="user-list">
                        <h2>Тестовые аккаунты:</h2>
                        <ul>
                            <li><strong>Администратор:</strong> admin / admin123</li>
                            <li><strong>Пользователь:</strong> alice / password123</li>
                            <li><strong>Пользователь:</strong> bob / password123</li>
                            <li><strong>Пользователь:</strong> charlie / password123</li>
                            <li><strong>Пользователь:</strong> diana / password123</li>
                            <li><strong>Пользователь:</strong> eve / password123</li>
                        </ul>
                    </div>
                    
                    <h3>Доступные действия:</h3>
                    <a href="/" class="btn">Перейти на главную страницу</a>
                    <a href="/login" class="btn">Войти в систему</a>
                    <a href="/admin" class="btn">Админ-панель</a>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                        <p><strong>Студент:</strong> {STUDENT_INFO['fio']}</p>
                        <p><strong>Группа:</strong> {STUDENT_INFO['group']}</p>
                    </div>
                </div>
            </body>
            </html>
        '''
        
    except Exception as e:
        return f'''
            <!DOCTYPE html>
            <html lang="ru">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Ошибка инициализации</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        max-width: 800px;
                        margin: 50px auto;
                        padding: 20px;
                        background-color: #f5f5f5;
                    }}
                    .container {{
                        background-color: white;
                        padding: 30px;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    .error {{
                        color: #d32f2f;
                        font-weight: bold;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1 class="error">❌ Ошибка при инициализации данных</h1>
                    <p><strong>Сообщение об ошибке:</strong> {str(e)}</p>
                    <p><a href="/">Вернуться на главную</a></p>
                </div>
            </body>
            </html>
        '''

# ========== JSON-RPC API ==========

@app.route('/api', methods=['POST'])
def api():
    """JSON-RPC endpoint"""
    try:
        return jsonrpc_handler.handle_request()
    except JSONRPCError as e:
        return jsonify({
            'jsonrpc': '2.0',
            'error': {
                'code': e.code,
                'message': e.message,
                'data': e.data
            },
            'id': request.json.get('id') if request.is_json else None
        }), 500
    except Exception as e:
        return jsonify({
            'jsonrpc': '2.0',
            'error': {
                'code': -32603,
                'message': f'Internal server error: {str(e)}'
            },
            'id': request.json.get('id') if request.is_json else None
        }), 500

# ========== ВСПОМОГАТЕЛЬНЫЕ МАРШРУТЫ ==========

@app.route('/api/test', methods=['GET'])
def api_test():
    """Тестовый endpoint для проверки работы API"""
    return jsonify({
        'status': 'OK',
        'message': 'API работает корректно',
        'endpoints': {
            '/api': 'JSON-RPC endpoint (POST)',
            '/api/test': 'Тестовый endpoint (GET)'
        },
        'app_info': {
            'name': 'Кулинарные рецепты',
            'author': STUDENT_INFO['fio'],
            'group': STUDENT_INFO['group'],
            'version': '1.0.0'
        }
    })

@app.route('/api/current_stats', methods=['GET'])
def current_stats():
    """Текущая статистика для обновления иконок"""
    stats = get_current_stats()
    
    return jsonify({
        'success': True,
        'stats': {
            'recipes': stats['recipes_count'],
            'users': stats['users_count'],
            'cooking_time': stats['total_cooking_time'],
            'categories': stats['categories_count']
        },
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/ping')
def ping():
    """Проверка работы API"""
    return jsonify({'status': 'ok', 'message': 'API работает'})

# ========== ЗАПУСК ==========

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🍳 КУЛИНАРНЫЙ САЙТ")
    print("="*50)
    print(f"👤 Пользователей в системе: {len(users)}")
    print(f"📝 Рецептов в системе: {len(recipes)}")
    print(f"🏷️ Категорий рецептов: {len(set([r['category'] for r in recipes]))}")
    
    # Проверяем наличие администратора
    admin_exists = any(user['username'] == 'admin' for user in users)
    if not admin_exists:
        print("\n⚠️  Администратор не найден!")
        print("📌 Перейдите по ссылке: http://localhost:5000/init")
    else:
        print("\n✅ Система готова к работе")
    
    print("💾 Данные загружены из файлов: data/users.json и data/recipes.json")
    print("\n🚀 Запуск приложения на http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)