from flask import request, jsonify, session
from auth import login_required_jsonrpc, admin_required_jsonrpc, validate_recipe_data, JSONRPCError
import json
from datetime import datetime

class JSONRPCHandler:
    """Обработчик JSON-RPC запросов для кулинарного сайта"""
    
    def __init__(self, recipes_list, users_list):
        self.recipes = recipes_list
        self.users = users_list
        self.methods = {
            'search_recipes': self.search_recipes,
            'get_recipe': self.get_recipe,
            'add_recipe': self.add_recipe,
            'update_recipe': self.update_recipe,
            'delete_recipe': self.delete_recipe,
            'get_categories': self.get_categories,
            'get_recipes_count': self.get_recipes_count,
            'get_user_info': self.get_user_info,
            'validate_login': self.validate_login,
            'get_popular_recipes': self.get_popular_recipes,
            'admin_get_all_users': self.admin_get_all_users,
            'admin_delete_user': self.admin_delete_user,
            'admin_update_user': self.admin_update_user,
            'delete_account': self.delete_account,
        }
    
    def get_current_user(self):
        """Получение текущего пользователя"""
        from auth import get_current_user
        return get_current_user(self.users)
    
    def is_admin(self):
        """Проверка прав администратора"""
        from auth import is_admin
        return is_admin(self.users)
    
    def handle_request(self):
        """Основной обработчик запроса"""
        if not request.is_json:
            raise JSONRPCError(-32700, 'Invalid JSON')
        
        data = request.get_json()
        
        # Проверка формата JSON-RPC 2.0
        if not isinstance(data, dict):
            raise JSONRPCError(-32600, 'Invalid Request')
        
        jsonrpc = data.get('jsonrpc')
        method_name = data.get('method')
        params = data.get('params', {})
        request_id = data.get('id')
        
        if jsonrpc != '2.0':
            raise JSONRPCError(-32600, 'Invalid Request: jsonrpc must be "2.0"')
        
        if not method_name or not isinstance(method_name, str):
            raise JSONRPCError(-32600, 'Invalid Request: method is required')
        
        if not isinstance(params, dict):
            raise JSONRPCError(-32602, 'Invalid params')
        
        # Выполнение метода
        if method_name not in self.methods:
            raise JSONRPCError(-32601, f'Method not found: {method_name}')
        
        try:
            result = self.methods[method_name](**params)
            response = {
                'jsonrpc': '2.0',
                'result': result,
                'id': request_id
            }
            return jsonify(response)
            
        except JSONRPCError as e:
            return self._error_response(e.code, e.message, e.data, request_id)
        except Exception as e:
            return self._error_response(-32603, f'Internal error: {str(e)}', None, request_id)
    
    def _error_response(self, code, message, data, request_id):
        return jsonify({
            'jsonrpc': '2.0',
            'error': {
                'code': code,
                'message': message,
                'data': data
            },
            'id': request_id
        })
    
    # ========== Методы JSON-RPC ==========
    
    def search_recipes(self, title='', ingredients=None, mode='any', 
                      category='', difficulty='', max_time=None):
        """Поиск рецептов по различным критериям"""
        title_filter = title.lower().strip()
        
        if isinstance(ingredients, str):
            ingredients_filter = [i.strip() for i in ingredients.split(',') if i.strip()]
        elif isinstance(ingredients, list):
            ingredients_filter = ingredients
        else:
            ingredients_filter = []
        
        if max_time is not None:
            try:
                max_time = int(max_time)
                if max_time <= 0:
                    return {'error': 'Максимальное время приготовления должно быть положительным числом'}
            except (ValueError, TypeError):
                return {'error': 'Максимальное время приготовления должно быть числом'}
        
        filtered_recipes = []
        
        for recipe in self.recipes:
            if title_filter and title_filter not in recipe['title'].lower():
                continue

            if category and recipe['category'].lower() != category.lower():
                continue

            if difficulty and recipe['difficulty'].lower() != difficulty.lower():
                continue

            if max_time and recipe['cooking_time'] > max_time:
                continue
                
            if ingredients_filter:
                recipe_ingredients = ' '.join([
                    ing.lower() for ing in recipe['ingredients']
                ])
                
                if mode == 'all':
                    all_found = True
                    for ingredient in ingredients_filter:
                        if ingredient.lower() not in recipe_ingredients:
                            all_found = False
                            break
                    if not all_found:
                        continue
                else:
                    found = False
                    for ingredient in ingredients_filter:
                        if ingredient.lower() in recipe_ingredients:
                            found = True
                            break
                    if not found:
                        continue
            
            filtered_recipes.append(recipe)
        
        filtered_recipes.sort(key=lambda x: x.get('views', 0), reverse=True)
        
        return {
            'recipes': filtered_recipes[:100],
            'count': len(filtered_recipes),
            'filters_applied': {
                'title': title_filter,
                'ingredients_count': len(ingredients_filter),
                'mode': mode,
                'category': category,
                'difficulty': difficulty,
                'max_time': max_time
            }
        }
    
    def get_recipe(self, recipe_id):
        """Получение информации о конкретном рецепте"""
        if not recipe_id:
            return {'error': 'Не указан ID рецепта'}
        
        try:
            recipe_id = int(recipe_id)
        except ValueError:
            return {'error': 'ID рецепта должен быть числом'}
        
        for recipe in self.recipes:
            if recipe['id'] == recipe_id:
                recipe['views'] = recipe.get('views', 0) + 1
                # Сохраняем увеличение просмотров
                from data_manager import save_recipes
                save_recipes(self.recipes)
                return {'recipe': recipe}
        
        return {'error': f'Рецепт с ID {recipe_id} не найден'}
    
    @login_required_jsonrpc
    def add_recipe(self, title, description='', ingredients=None, steps='', 
                  image_url='', cooking_time=30, category='Основное блюдо', 
                  difficulty='Средняя'):
        """Добавление нового рецепта"""
        if not self.is_admin():
            return {'error': 'Требуются права администратора'}
        
        params = {
            'title': title,
            'description': description,
            'ingredients': ingredients,
            'steps': steps,
            'image_url': image_url,
            'cooking_time': cooking_time,
            'category': category,
            'difficulty': difficulty
        }
        
        validation_errors = validate_recipe_data(params, is_update=False)
        if validation_errors:
            return {'error': 'Ошибки валидации', 'validation_errors': validation_errors}
        
        if isinstance(ingredients, str):
            ingredients = [i.strip() for i in ingredients.split('\n') if i.strip()]
        
        # Генерируем новый ID
        new_id = max([r['id'] for r in self.recipes], default=0) + 1
        current_user = self.get_current_user()
        
        new_recipe = {
            'id': new_id,
            'title': title,
            'description': description,
            'ingredients': ingredients,
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
        
        self.recipes.append(new_recipe)
        from data_manager import save_recipes
        save_recipes(self.recipes)
        
        return {
            'success': True,
            'message': 'Рецепт успешно добавлен',
            'recipe_id': new_id,
            'recipe': new_recipe
        }
    
    @login_required_jsonrpc
    def update_recipe(self, recipe_id, title=None, description=None, 
                     ingredients=None, steps=None, image_url=None, 
                     cooking_time=None, category=None, difficulty=None, rating=None):
        """Обновление существующего рецепта"""
        if not self.is_admin():
            return {'error': 'Требуются права администратора'}
        
        if not recipe_id:
            return {'error': 'Не указан ID рецепта'}
        
        try:
            recipe_id = int(recipe_id)
        except ValueError:
            return {'error': 'ID рецепта должен быть числом'}
        
        params = {}
        if title is not None:
            params['title'] = title
        if description is not None:
            params['description'] = description
        if ingredients is not None:
            params['ingredients'] = ingredients
        if steps is not None:
            params['steps'] = steps
        if image_url is not None:
            params['image_url'] = image_url
        if cooking_time is not None:
            params['cooking_time'] = cooking_time
        if category is not None:
            params['category'] = category
        if difficulty is not None:
            params['difficulty'] = difficulty
        if rating is not None:
            params['rating'] = rating
        
        validation_errors = validate_recipe_data(params, is_update=True)
        if validation_errors:
            return {'error': 'Ошибки валидации', 'validation_errors': validation_errors}
        
        for i, recipe in enumerate(self.recipes):
            if recipe['id'] == recipe_id:
                update_fields = ['title', 'description', 'ingredients', 'steps', 
                               'image_url', 'cooking_time', 'category', 'difficulty', 'rating']
                
                for field in update_fields:
                    if field in params and params[field] is not None:
                        if field == 'ingredients' and isinstance(params[field], str):
                            self.recipes[i][field] = [
                                ing.strip() for ing in params[field].split('\n') 
                                if ing.strip()
                            ]
                        elif field == 'cooking_time':
                            try:
                                time_val = int(params[field])
                                if time_val <= 0:
                                    return {'error': 'Время приготовления должно быть положительным числом'}
                                self.recipes[i][field] = time_val
                            except (ValueError, TypeError):
                                return {'error': 'Время приготовления должно быть числом'}
                        elif field == 'rating':
                            try:
                                rating_val = float(params[field])
                                if rating_val < 0 or rating_val > 5:
                                    return {'error': 'Рейтинг должен быть в диапазоне от 0 до 5'}
                                self.recipes[i][field] = rating_val
                            except (ValueError, TypeError):
                                return {'error': 'Рейтинг должен быть числом'}
                        else:
                            self.recipes[i][field] = params[field]
                
                from data_manager import save_recipes
                save_recipes(self.recipes)
                
                return {
                    'success': True,
                    'message': 'Рецепт успешно обновлен',
                    'recipe': self.recipes[i]
                }
        
        return {'error': f'Рецепт с ID {recipe_id} не найден'}
    
    @login_required_jsonrpc
    def delete_recipe(self, recipe_id):
        """Удаление рецепта"""
        if not self.is_admin():
            return {'error': 'Требуются права администратора'}
        
        if not recipe_id:
            return {'error': 'Не указан ID рецепта'}
        
        try:
            recipe_id = int(recipe_id)
        except ValueError:
            return {'error': 'ID рецепта должен быть числом'}
        
        initial_count = len(self.recipes)
        
        # Удаляем рецепт
        self.recipes = [r for r in self.recipes if r['id'] != recipe_id]
        
        if len(self.recipes) < initial_count:
            from data_manager import save_recipes
            save_recipes(self.recipes)
            return {
                'success': True,
                'message': f'Рецепт с ID {recipe_id} успешно удален',
                'remaining_recipes': len(self.recipes)
            }
        else:
            return {'error': f'Рецепт с ID {recipe_id} не найден'}
    
    def get_categories(self):
        """Получение списка всех категорий рецептов"""
        categories = {}
        for recipe in self.recipes:
            cat = recipe['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        # Сортируем по популярности
        sorted_categories = sorted(
            categories.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            'categories': [cat for cat, count in sorted_categories],
            'counts': {cat: count for cat, count in sorted_categories},
            'total_categories': len(categories)
        }
    
    def get_recipes_count(self):
        """Получение статистики по рецептам"""
        categories_count = {}
        difficulties_count = {}
        negative_time_count = 0
        total_cooking_time = 0
        
        for recipe in self.recipes:
            cat = recipe['category']
            diff = recipe['difficulty']
            
            categories_count[cat] = categories_count.get(cat, 0) + 1
            difficulties_count[diff] = difficulties_count.get(diff, 0) + 1
            total_cooking_time += recipe.get('cooking_time', 0)
            
            if recipe['cooking_time'] <= 0:
                negative_time_count += 1
        
        return {
            'total': len(self.recipes),
            'categories': categories_count,
            'difficulties': difficulties_count,
            'total_cooking_time': total_cooking_time,
            'avg_cooking_time': round(total_cooking_time / len(self.recipes), 1) if self.recipes else 0,
            'total_views': sum(r.get('views', 0) for r in self.recipes),
            'avg_rating': round(sum(r.get('rating', 0) for r in self.recipes) / len(self.recipes), 2) if self.recipes else 0,
            'validation_stats': {
                'recipes_with_negative_time': negative_time_count,
                'total_valid_recipes': len(self.recipes) - negative_time_count
            }
        }
    
    def get_user_info(self):
        """Получение информации о текущем пользователе"""
        user = self.get_current_user()
        if not user:
            return {'authenticated': False}
        
        user_info = user.copy()
        if 'password_hash' in user_info:
            user_info.pop('password_hash', None)
        
        return {
            'authenticated': True,
            'user': user_info,
            'is_admin': user.get('is_admin', False)
        }
    
    def validate_login(self, username, password):
        """Валидация логина и пароля через API"""
        from auth import validate_username, validate_password
        
        username_valid, username_error = validate_username(username)
        if not username_valid:
            return {'valid': False, 'error': username_error}
        
        password_valid, password_error = validate_password(password)
        if not password_valid:
            return {'valid': False, 'error': password_error}
        
        return {'valid': True}
    
    def get_popular_recipes(self, count=10):
        """Получение популярных рецептов"""
        try:
            count = int(count)
            if count <= 0:
                return {'error': 'Количество должно быть положительным числом'}
            if count > 50:
                count = 50
        except (ValueError, TypeError):
            return {'error': 'Количество должно быть числом'}
        
        # Сортируем по просмотрам и рейтингу
        popular = sorted(
            self.recipes,
            key=lambda x: (x.get('views', 0), x.get('rating', 0)),
            reverse=True
        )[:count]
        
        return {
            'recipes': popular,
            'count': len(popular),
            'total_views': sum(r.get('views', 0) for r in popular)
        }
    
    @admin_required_jsonrpc
    def admin_get_all_users(self, limit=100, offset=0, search=None, role_filter=None):
        """Админ: получение всех пользователей с фильтрацией"""
        try:
            print(f"DEBUG: Вызов admin_get_all_users, поиск: '{search}', фильтр: '{role_filter}'")
            
            # Применяем фильтры
            filtered_users = self.users
            
            if search:
                search_lower = search.lower()
                filtered_users = [u for u in filtered_users if search_lower in u['username'].lower()]
            
            if role_filter:
                if role_filter == 'admin':
                    filtered_users = [u for u in filtered_users if u.get('is_admin', False)]
                elif role_filter == 'user':
                    filtered_users = [u for u in filtered_users if not u.get('is_admin', False)]
            
            total_count = len(filtered_users)
            
            # Применяем пагинацию
            paginated_users = filtered_users[offset:offset + limit]
            
            print(f"DEBUG: Найдено {len(paginated_users)} пользователей (всего: {total_count})")
            
            result = []
            for user in paginated_users:
                # Считаем количество рецептов пользователя
                recipes_count = len([r for r in self.recipes if r.get('author') == user['username']])
                
                user_info = user.copy()
                if 'password_hash' in user_info:
                    user_info.pop('password_hash', None)
                
                result.append({
                    'id': user['id'],
                    'username': user['username'],
                    'email': user.get('email', ''),
                    'is_admin': bool(user.get('is_admin', False)),
                    'created_at': user.get('created_at', ''),
                    'recipes_count': recipes_count
                })
            
            return {
                'users': result,
                'total': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            print(f"ERROR в admin_get_all_users: {str(e)}")
            raise JSONRPCError(-32603, f'Internal server error: {str(e)}')
    
    @admin_required_jsonrpc
    def admin_delete_user(self, user_id):
        """Админ: удаление пользователя"""
        current_user = self.get_current_user()
        if user_id == current_user['id']:
            raise JSONRPCError(-32602, 'Нельзя удалить самого себя')
        
        try:
            user_id = int(user_id)
        except ValueError:
            raise JSONRPCError(-32602, 'ID пользователя должен быть числом')
        
        # Проверяем существование пользователя
        user_exists = any(user['id'] == user_id for user in self.users)
        if not user_exists:
            raise JSONRPCError(-32602, 'Пользователь не найден')
        
        # Удаляем пользователя
        self.users = [u for u in self.users if u['id'] != user_id]
        
        # Удаляем рецепты пользователя
        user_to_delete = None
        for user in self.users:
            if user['id'] == user_id:
                user_to_delete = user
                break
        
        if user_to_delete:
            self.recipes = [r for r in self.recipes if r.get('author') != user_to_delete['username']]
        
        # Сохраняем изменения в файлы
        from data_manager import save_users, save_recipes
        save_users(self.users)
        save_recipes(self.recipes)
        
        return {'success': True, 'deleted_user_id': user_id}
    
    @admin_required_jsonrpc
    def admin_update_user(self, user_id, is_admin=None, new_password=None):
        """Админ: обновление пользователя"""
        try:
            user_id = int(user_id)
        except ValueError:
            raise JSONRPCError(-32602, 'ID пользователя должен быть числом')
        
        user_found = False
        for i, user in enumerate(self.users):
            if user['id'] == user_id:
                user_found = True
                
                if is_admin is not None:
                    self.users[i]['is_admin'] = bool(is_admin)
                
                if new_password:
                    from werkzeug.security import generate_password_hash
                    self.users[i]['password_hash'] = generate_password_hash(new_password)
                
                break
        
        if not user_found:
            raise JSONRPCError(-32602, 'Пользователь не найден')
        
        from data_manager import save_users
        save_users(self.users)
        
        return {'success': True, 'updated_user_id': user_id}
    
    @login_required_jsonrpc
    def delete_account(self):
        """Удаление своего аккаунта"""
        current_user = self.get_current_user()
        
        if current_user['is_admin'] and current_user['username'] == 'admin':
            raise JSONRPCError(-32602, 'Нельзя удалить администратора системы')
        
        # Удаляем пользователя
        self.users = [u for u in self.users if u['id'] != current_user['id']]
        
        # Удаляем рецепты пользователя (кроме административных)
        self.recipes = [r for r in self.recipes if r.get('author') != current_user['username']]
        
        # Сохраняем изменения в файлы
        from data_manager import save_users, save_recipes
        save_users(self.users)
        save_recipes(self.recipes)
        
        # Выходим из системы
        from auth import logout_user
        logout_user()
        
        return {'success': True, 'message': 'Аккаунт удален'}