import os
from datetime import datetime

class Config:
    """Конфигурация приложения"""
    # Основные настройки
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Данные студента
    STUDENT_FIO = "Стабровская Елизавета"
    STUDENT_GROUP = "ФБИ-33"
    
    # Настройки сессии
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 час
    
    # Настройки валидации
    MIN_USERNAME_LENGTH = 3
    MAX_USERNAME_LENGTH = 50
    MIN_PASSWORD_LENGTH = 6
    MAX_PASSWORD_LENGTH = 100
    
    # Константы для рецептов
    RECIPE_CATEGORIES = ['Завтрак', 'Обед', 'Ужин', 'Десерт', 'Закуска', 'Салат', 'Суп', 'Основное блюдо']
    RECIPE_DIFFICULTIES = ['Легкая', 'Средняя', 'Сложная']
    
    # Пути к файлам данных
    DATA_DIR = 'data'
    USERS_FILE = os.path.join(DATA_DIR, 'users.json')
    RECIPES_FILE = os.path.join(DATA_DIR, 'recipes.json')