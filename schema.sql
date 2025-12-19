-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица рецептов
CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    ingredients TEXT NOT NULL,  -- Храним как JSON строку
    steps TEXT NOT NULL,
    image_url TEXT,
    cooking_time INTEGER NOT NULL,
    category TEXT NOT NULL,
    difficulty TEXT NOT NULL CHECK (difficulty IN ('Легкая', 'Средняя', 'Сложная')),
    author_id INTEGER NOT NULL,
    rating REAL DEFAULT 4.0 CHECK (rating >= 0 AND rating <= 5),
    views INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES users(id)
);

-- Таблица избранных рецептов (если добавите функционал "избранное")
CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    recipe_id INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (recipe_id) REFERENCES recipes(id),
    UNIQUE(user_id, recipe_id)
);

-- Таблица отзывов (если добавите функционал отзывов)
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    recipe_id INTEGER NOT NULL,
    rating REAL NOT NULL CHECK (rating >= 0 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (recipe_id) REFERENCES recipes(id),
    UNIQUE(user_id, recipe_id)
);

-- Индексы для быстрого поиска рецептов
CREATE INDEX IF NOT EXISTS idx_recipes_category ON recipes(category);
CREATE INDEX IF NOT EXISTS idx_recipes_difficulty ON recipes(difficulty);
CREATE INDEX IF NOT EXISTS idx_recipes_cooking_time ON recipes(cooking_time);
CREATE INDEX IF NOT EXISTS idx_recipes_author ON recipes(author_id);
CREATE INDEX IF NOT EXISTS idx_recipes_created ON recipes(created_at DESC);

-- Индекс для поиска по названию рецепта
CREATE INDEX IF NOT EXISTS idx_recipes_title ON recipes(title);

-- Индекс для популярных рецептов (по просмотрам и рейтингу)
CREATE INDEX IF NOT EXISTS idx_recipes_popularity ON recipes(views DESC, rating DESC);

-- Индексы для пользователей
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_created ON users(created_at DESC);

-- Индексы для избранного
CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_favorites_recipe ON favorites(recipe_id);

-- Индексы для отзывов
CREATE INDEX IF NOT EXISTS idx_reviews_recipe ON reviews(recipe_id);
CREATE INDEX IF NOT EXISTS idx_reviews_user ON reviews(user_id);

-- Представление для статистики рецептов (если понадобится)
CREATE VIEW IF NOT EXISTS recipe_stats AS
SELECT 
    category,
    COUNT(*) as count,
    AVG(cooking_time) as avg_cooking_time,
    AVG(rating) as avg_rating,
    SUM(views) as total_views
FROM recipes
GROUP BY category;

-- Представление для статистики пользователей
CREATE VIEW IF NOT EXISTS user_stats AS
SELECT 
    u.username,
    u.is_admin,
    u.created_at,
    COUNT(r.id) as recipes_count,
    COALESCE(AVG(r.rating), 0) as avg_rating,
    COALESCE(SUM(r.views), 0) as total_views
FROM users u
LEFT JOIN recipes r ON u.id = r.author_id
GROUP BY u.id;

-- Триггер для автоматического обновления среднего рейтинга рецепта (если будете использовать отзывы)
CREATE TRIGGER IF NOT EXISTS update_recipe_rating
AFTER INSERT OR UPDATE OR DELETE ON reviews
FOR EACH ROW
BEGIN
    UPDATE recipes
    SET rating = (
        SELECT AVG(rating) 
        FROM reviews 
        WHERE recipe_id = COALESCE(NEW.recipe_id, OLD.recipe_id)
    )
    WHERE id = COALESCE(NEW.recipe_id, OLD.recipe_id);
END;