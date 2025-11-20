# app/routes.py
from flask import Blueprint, render_template, request, redirect, url_for
from app import create_app
import pymysql
from flask import jsonify
from app.models import Automation
from flask import session
from decimal import Decimal
import traceback
from flask import current_app
main_routes = Blueprint('main', __name__)

# Главная страница
@main_routes.route('/')
def index():
    return render_template('index.html')

@main_routes.route('/services')
def services():
    app = create_app()
    connection = app.mysql_connection
    

    try:
        with connection.cursor() as cursor:
            # Обновленный запрос с JOIN и основной ценой
            cursor.execute("""
                SELECT s.id AS service_id, s.name AS service_name, s.description AS service_description, 
                       s.image AS service_image, s.price AS service_price,
                       v.id AS variant_id, v.name AS variant_name, v.price AS variant_price
                FROM services s
                LEFT JOIN service_variants v ON s.id = v.service_id
            """)
            services_data = cursor.fetchall()
            
        
        # Обрабатываем данные для удобного отображения в шаблоне
        services = {}
        for row in services_data:
            service_id = row['service_id']
            if service_id not in services:
                services[service_id] = {
                    'id': service_id,
                    'name': row['service_name'],
                    'description': row['service_description'],
                    'image': row['service_image'],
                    'price': row['service_price'],  # Основная цена из таблицы services
                    'variants': []
                }
            if row['variant_id']:  # Добавляем вариант, если он есть
                services[service_id]['variants'].append({
                    'id': row['variant_id'],
                    'name': row['variant_name'],
                    'price': row['variant_price']
                })
        
        return render_template('services.html', services=services.values())
    finally:
        connection.close()


# Программы 1С
@main_routes.route('/products')
def products():
    app = create_app()
    connection = app.mysql_connection

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT p.id AS product_id, p.name AS product_name, p.description AS product_description, 
                       p.image AS product_image, p.price AS product_price,
                       v.id AS variant_id, v.name AS variant_name, v.price AS variant_price
                FROM products p
                LEFT JOIN product_variants v ON p.id = v.product_id
            """)
            products_data = cursor.fetchall()

        products = {}
        for row in products_data:
            product_id = row['product_id']
            if product_id not in products:
                products[product_id] = {
                    'id': product_id,
                    'name': row['product_name'],
                    'description': row['product_description'],
                    'image': row['product_image'],
                    'price': row['product_price'],
                    'variants': []
                }
            if row['variant_id']:
                products[product_id]['variants'].append({
                    'id': row['variant_id'],
                    'name': row['variant_name'],
                    'price': row['variant_price']
                })

        return render_template('products.html', products=products.values())
    
    finally:
        connection.close()


# Автоматизация
@main_routes.route('/automation')
def automation():
    automation_model = Automation()  # Создаем экземпляр модели Automation
    products = automation_model.get_all_products()  # Получаем все товары из таблицы automation
    return render_template('automation.html', products=products)

# Контакты
@main_routes.route('/contact')
def contact():
    return render_template('contact.html')

@main_routes.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    try:
        # Получаем данные из формы
        inn = request.form.get('inn', '')  # Необязательное поле
        name = request.form['name']        # Обязательное поле
        phone = request.form['phone']      # Обязательное поле
        email = request.form.get('email', '')  # Необязательное поле

        print(f"Данные: {name}, {phone}, {email}, {inn}")  # Логирование

        # Подключение к базе данных
        app = create_app()
        connection = app.mysql_connection
        try:
            with connection.cursor() as cursor:
                # SQL-запрос для вставки данных
                sql = """
                INSERT INTO clients (full_name, phone_number, email, description, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                """
                cursor.execute(sql, (name, phone, email, inn))
            connection.commit()
            return jsonify(success=True)  # Успешный ответ
        except Exception as e:
            print(f"Ошибка SQL: {e}")  # Логирование
            connection.rollback()
            return jsonify(success=False, message="Ошибка базы данных"), 500
        finally:
            connection.close()
    except KeyError as e:
        print(f"Ошибка: отсутствует поле {e}")  # Логирование
        return jsonify(success=False, message="Отсутствуют обязательные поля"), 400
    except Exception as e:
        print(f"Неизвестная ошибка: {e}")  # Логирование
        return jsonify(success=False, message="Внутренняя ошибка сервера"), 500




@main_routes.route('/cart')
def cart():
    if 'cart' not in session:
        session['cart'] = {}
    elif isinstance(session['cart'], list):
        session['cart'] = {str(product_id): 1 for product_id in session['cart']}
        session.modified = True

    cart_items = []
    cart_total = Decimal('0.0')  # Используем Decimal для денежных расчетов
    
    app = create_app()
    connection = app.mysql_connection

    try:
        with connection.cursor() as cursor:
            for cart_key, quantity in session['cart'].items():
                quantity = int(quantity)
                
                # Обработка товаров автоматизации
                if cart_key.isdigit():
                    cursor.execute("SELECT id, name FROM automation WHERE id = %s", (int(cart_key),))
                    product = cursor.fetchone()
                    if product:
                        cart_items.append({
                            'id': product['id'],
                            'name': product['name'],
                            'quantity': quantity,
                            'type': 'product',
                            'price': None,
                            'variant': None
                        })

                # Обработка товаров products
                elif cart_key.startswith('prd_'):
                    parts = cart_key.split('_')
                    product_id = parts[1]
                    variant_id = parts[2] if len(parts) > 2 else None
                    print(f"Parsing cart key: {cart_key} => product_id: {product_id}, variant_id: {variant_id}")

                    cursor.execute("SELECT id, name, price FROM products WHERE id = %s", (product_id,))
                    product = cursor.fetchone()

                    if product:
                        item_data = {
                            'id': product['id'],
                            'name': product['name'],
                            'quantity': quantity,
                            'type': 'product',
                            'price': Decimal(str(product['price'])) if product['price'] else None,
                            'variant': None
                        }

                        if variant_id:
                            cursor.execute("SELECT id, name, price FROM product_variants WHERE id = %s", (variant_id,))
                            variant = cursor.fetchone()
                            if variant:
                                item_data['variant'] = {
                                    'id': variant['id'],
                                    'name': variant['name'],
                                    'price': Decimal(str(variant['price']))
                                }
                                item_data['price'] = item_data['variant']['price']

                        if item_data['price']:
                            print(f"[DEBUG] Цена товара: {item_data['price']}, количество: {quantity}")
                            cart_total += item_data['price'] * Decimal(quantity)
                        
                        cart_items.append(item_data)


                # Обработка услуг
                elif cart_key.startswith('service_'):
                    parts = cart_key.split('_')
                    service_id = parts[1]
                    variant_id = parts[2] if len(parts) > 2 else None

                    cursor.execute("""
                        SELECT s.id, s.name, s.price, 
                            v.id as variant_id, v.name as variant_name, v.price as variant_price
                        FROM services s
                        LEFT JOIN service_variants v ON v.id = %s AND v.service_id = s.id
                        WHERE s.id = %s
                    """, (variant_id, service_id))

                    item = cursor.fetchone()
                    if item:
                        price = item['variant_price'] if variant_id else item['price']
                        name = item['variant_name'] if variant_id else item['name']

                        item_data = {
                            'id': item['id'],
                            'name': name,
                            'quantity': quantity,
                            'type': 'service',
                            'price': Decimal(str(price)) if price else None,
                            'variant': {
                                'id': item['variant_id'],
                                'name': item['variant_name']
                            } if variant_id else None
                        }

                        if item_data['price']:
                            cart_total += item_data['price'] * Decimal(quantity)

                        cart_items.append(item_data)

    
        # Конвертируем Decimal в float для шаблона (если нужно)
        cart_total_float = float(cart_total)
        
        return render_template('cart.html', 
                            cart_items=cart_items,
                            cart_total=cart_total_float)
        
    except Exception as e:
        
        print(f"Ошибка при загрузке корзины: {str(e)}")
        return render_template('cart.html',
                        cart_items=cart_items,
                        cart_total=float(cart_total),
                        items_count=sum(session['cart'].values()))
    
    finally:
        connection.close()

@main_routes.route('/add_product_to_cart/<string:product_key>', methods=['POST'])
def add_product_to_cart(product_key):
    data = request.get_json() or {}
    variant_id = data.get('variant_id')
    
    # Удаляем префикс
    product_id = product_key.replace('prd_', '')
    
    if 'cart' not in session:
        session['cart'] = {}

    # Формируем ключ
    cart_key = f"prd_{product_id}"
    if variant_id:
        cart_key += f"_{variant_id}"

    session['cart'][cart_key] = session['cart'].get(cart_key, 0) + 1
    session.modified = True
    
    return jsonify(
        success=True,
        cart_total=sum(session['cart'].values())
    )

@main_routes.route('/debug_cart')
def debug_cart():
    return jsonify({
        'session_cart': session.get('cart', {}),
        'cart_total': sum(session.get('cart', {}).values())
    })

@main_routes.route('/add_service_to_cart/<int:service_id>', methods=['POST'])
def add_service_to_cart(service_id):
    data = request.get_json() or {}  # ✅ защита от None
    variant_id = data.get('variant_id')

    if 'cart' not in session:
        session['cart'] = {}

    cart_key = f"service_{service_id}_{variant_id}" if variant_id else f"service_{service_id}"

    if cart_key not in session['cart']:
        session['cart'][cart_key] = 1
    else:
        session['cart'][cart_key] += 1

    session.modified = True

    cart_total = sum(int(value) for value in session['cart'].values())
    return jsonify(success=True, cart_total=cart_total)

@main_routes.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'cart' not in session:
        session['cart'] = {}
    
    # Убедимся, что ключи являются строками
    product_key = str(product_id)
    
    if product_key not in session['cart']:
        session['cart'][product_key] = 1
    else:
        session['cart'][product_key] += 1
    
    session.modified = True
    
    # Возвращаем общее количество товаров в корзине
    cart_total = sum(int(value) for value in session['cart'].values())
    return jsonify(success=True, cart_total=cart_total)

@main_routes.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    if 'cart' in session and str(product_id) in session['cart']:
        del session['cart'][str(product_id)]
        session.modified = True
    
    cart_total = sum(int(value) for value in session.get('cart', {}).values())
    return jsonify(success=True, cart_total=cart_total)

@main_routes.route('/update_cart_item/<int:product_id>', methods=['POST'])
def update_cart_item(product_id):
    data = request.get_json()
    change = data.get('change', 1)

    if 'cart' in session:
        cart = session['cart']
        product_key = str(product_id)
        
        if product_key in cart:
            # Увеличиваем или уменьшаем количество товара
            cart[product_key] += change
            
            # Если количество меньше 1, удаляем товар из корзины
            if cart[product_key] < 1:
                del cart[product_key]
            
            session.modified = True

    # Возвращаем общее количество товаров в корзине
    cart_total = sum(int(value) for value in session.get('cart', {}).values())
    return jsonify(success=True, cart_total=cart_total)

@main_routes.route('/get_cart_total')
def get_cart_total():
    items_count = sum(session.get('cart', {}).values())
    total_sum = Decimal('0.0')
    cart_items = []  # Для хранения данных о товарах/услугах (важно для уведомлений!)
    
    if 'cart' in session:
        app = create_app()
        connection = app.mysql_connection
        try:
            with connection.cursor() as cursor:
                for cart_key, quantity in session['cart'].items():
                    quantity = int(quantity)
                    
                    # Обработка услуг (оставляем как было)
                    if cart_key.startswith('service_'):
                        parts = cart_key.split('_')
                        service_id = parts[1]
                        variant_id = parts[2] if len(parts) > 2 else None
                        
                        cursor.execute("SELECT id, name, price FROM services WHERE id = %s", (service_id,))
                        service = cursor.fetchone()
                        if service:
                            item_data = {
                                'id': service['id'],
                                'name': service['name'],
                                'quantity': quantity,
                                'type': 'service',
                                'price': Decimal(str(service['price'])) if service['price'] else None,
                                'variant': None
                            }
                            
                            if variant_id:
                                cursor.execute("SELECT id, name, price FROM service_variants WHERE id = %s", (variant_id,))
                                variant = cursor.fetchone()
                                if variant:
                                    item_data['variant'] = {
                                        'id': variant['id'],
                                        'name': variant['name'],
                                        'price': Decimal(str(variant['price']))
                                    }
                                    item_data['price'] = item_data['variant']['price']
                            
                            if item_data['price']:
                                total_sum += item_data['price'] * quantity
                            
                            cart_items.append(item_data)
                    


                    # Обработка товаров (исправляем ошибку, но сохраняем структуру)
                    elif cart_key.startswith('product_'):
                        parts = cart_key.split('_')
                        product_id = parts[1]
                        variant_id = parts[2] if len(parts) > 2 else None

                        cursor.execute("SELECT id, name, price FROM products WHERE id = %s", (product_id,))
                        product = cursor.fetchone()

                        if product:
                            item_data = {
                                'id': product['id'],
                                'name': product['name'],
                                'quantity': quantity,
                                'type': 'product',
                                'price': Decimal(str(product['price'])) if product['price'] else None,
                                'variant': None
                            }

                            if variant_id:
                                cursor.execute("SELECT id, name, price FROM product_variants WHERE id = %s", (variant_id,))
                                variant = cursor.fetchone()
                                if variant:
                                    item_data['variant'] = {
                                        'id': variant['id'],
                                        'name': variant['name'],
                                        'price': Decimal(str(variant['price']))
                                    }
                                    item_data['price'] = item_data['variant']['price']
                            
                            if item_data['price']:
                                    cart_total += Decimal(str(item_data['price'])) * Decimal(quantity)

                            
                            cart_items.append(item_data)

                    elif cart_key.startswith('prd_'):
                        parts = cart_key.split('_')
                        product_id = parts[1]
                        variant_id = parts[2] if len(parts) > 2 else None

                        cursor.execute("SELECT id, name, price FROM products WHERE id = %s", (product_id,))
                        product = cursor.fetchone()

                        if product:
                            item_data = {
                                'id': product['id'],
                                'name': product['name'],
                                'quantity': quantity,
                                'type': 'product',
                                'price': Decimal(str(product['price'])) if product['price'] else None,
                                'variant': None
                            }

                            if variant_id:
                                cursor.execute("SELECT id, name, price FROM product_variants WHERE id = %s", (variant_id,))
                                variant = cursor.fetchone()
                                if variant:
                                    item_data['variant'] = {
                                        'id': variant['id'],
                                        'name': variant['name'],
                                        'price': Decimal(str(variant['price']))
                                    }
                                    item_data['price'] = item_data['variant']['price']

                            if item_data['price']:
                                total_sum += item_data['price'] * Decimal(quantity)

                            cart_items.append(item_data)

        finally:
            connection.close()
    
    return jsonify({
        'items_count': items_count,
        'total_sum': float(total_sum),
        'cart_items': cart_items,  # Важно! Для уведомлений и счетчиков
        'cart': session.get('cart', {})
    })

@main_routes.route('/clear_cart')
def clear_cart():
    session['cart'] = {}
    session.modified = True
    return jsonify(success=True)

@main_routes.route('/update_service_cart_item/<int:service_id>', methods=['POST'])
def update_service_cart_item(service_id):
    data = request.get_json()
    change = data.get('change', 1)
    variant_id = data.get('variant_id')
    
    if 'cart' not in session:
        session['cart'] = {}
    
    cart_key = f"service_{service_id}_{variant_id}" if variant_id else f"service_{service_id}"
    session['cart'][cart_key] = session['cart'].get(cart_key, 0) + change
    
    if session['cart'][cart_key] < 1:
        del session['cart'][cart_key]
    
    session.modified = True
    return jsonify(success=True)

@main_routes.route('/remove_service_from_cart/<int:service_id>', methods=['POST'])
def remove_service_from_cart(service_id):
    data = request.get_json()
    variant_id = data.get('variant_id')
    
    if 'cart' in session:
        cart_key = f"service_{service_id}_{variant_id}" if variant_id else f"service_{service_id}"
        if cart_key in session['cart']:
            del session['cart'][cart_key]
            session.modified = True
    
    return jsonify(success=True)


@main_routes.route('/remove_product_from_cart/<int:product_id>', methods=['POST'])
def remove_product_from_cart(product_id):
    data = request.get_json()
    variant_id = data.get('variant_id')

    cart_key = f"prd_{product_id}_{variant_id}" if variant_id else f"prd_{product_id}"

    if 'cart' in session and cart_key in session['cart']:
        del session['cart'][cart_key]
        session.modified = True

    return jsonify(success=True)




@main_routes.route('/update_product_cart_item/<int:product_id>', methods=['POST'])
def update_product_cart_item(product_id):
    data = request.get_json()
    change = data.get('change', 1)
    variant_id = data.get('variant_id')  # ключевое

    if 'cart' not in session:
        session['cart'] = {}

    # Ключ должен быть в формате prd_1_1
    cart_key = f"prd_{product_id}_{variant_id}" if variant_id else f"prd_{product_id}"

    if cart_key in session['cart']:
        session['cart'][cart_key] += change
        if session['cart'][cart_key] < 1:
            del session['cart'][cart_key]
        session.modified = True

    return jsonify(success=True)


from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash, generate_password_hash

auth = HTTPBasicAuth()

# Можно хранить пароль в хэшированном виде:
users = {
    "admin": generate_password_hash("2121") 
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username

@main_routes.route('/admin/orders')
@auth.login_required
def view_orders():
    try:
        app = create_app()
        connection = app.mysql_connection

        with connection.cursor() as cursor:
            # Получаем заказы + данные клиентов
            cursor.execute("""
                SELECT 
                    o.id, 
                    o.created_at, 
                    o.status,
                    c.full_name, 
                    c.phone_number, 
                    c.email
                FROM orders o
                JOIN clients c ON o.client_id = c.id
                ORDER BY o.created_at DESC
            """)
            orders = []
            for row in cursor.fetchall():
                orders.append({
                    'id': row['id'],
                    'created_at': row['created_at'],
                    'status': row['status'],
                    'client_name': row['full_name'],
                    'client_phone': row['phone_number'],
                    'client_email': row['email'],
                    'items': [],
                    'items_count': 0,
                    'total_sum': 0
                })

            # Для каждого заказа — получить его товары
            for order in orders:
                cursor.execute("""
                    SELECT 
                        product_id, 
                        product_name,
                        variant_id,
                        variant_name,
                        quantity,
                        price
                    FROM order_items
                    WHERE order_id = %s
                """, (order['id'],))

                for item in cursor.fetchall():
                    price = float(item['price']) if item['price'] is not None else 0.0
                    quantity = item['quantity']

                    order['items'].append({
                        'product_id': item['product_id'],
                        'product_name': item['product_name'],
                        'variant_id': item['variant_id'],
                        'variant_name': item['variant_name'],
                        'quantity': quantity,
                        'price': price
                    })

                order['items_count'] = len(order['items'])
                order['total_sum'] = sum(item['price'] * item['quantity'] for item in order['items'])

            return render_template('admin/orders.html', orders=orders)

    except Exception as e:
        import traceback
        print(f"Full error: {traceback.format_exc()}")
        return render_template('admin/orders.html', orders=[], error=str(e))

    finally:
        if connection:
            connection.close()



@main_routes.route('/admin/orders/delete/<int:order_id>', methods=['DELETE'])
def delete_order_ajax(order_id):
    try:
        connection = current_app.mysql_connection

        # Проверка соединения, если оно "заснуло" — перезапускаем
        try:
            connection.ping(reconnect=True)
        except:
            print("Соединение устарело, пересоздаём его...")
            from config import DB_CONFIG
            connection = pymysql.connect(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                db=DB_CONFIG['database'],
                cursorclass=pymysql.cursors.DictCursor
            )
            current_app.mysql_connection = connection  # обновляем в app

        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM order_items WHERE order_id = %s", (order_id,))
            cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))
            connection.commit()
        
        return jsonify({'success': True})

    except Exception as e:
        print(f"Ошибка при удалении заказа: {e}")
        try:
            connection.rollback()
        except Exception as rollback_error:
            print(f"Ошибка при откате транзакции: {rollback_error}")
        return jsonify({'success': False, 'error': str(e)}), 500


@main_routes.route('/submit-order', methods=['POST'])
def submit_order():
    try:
        form_data = request.form
        name = form_data['name']
        phone = form_data['phone']
        email = form_data.get('email', '')
        inn = form_data.get('inn', '')

        cart_items = session.get('cart', {})
        if not cart_items:
            return jsonify(success=False, message="Корзина пуста"), 400

        app = create_app()
        connection = app.mysql_connection

        try:
            with connection.cursor() as cursor:
                # 1. Сохраняем клиента
                cursor.execute("""
                    INSERT INTO clients (full_name, phone_number, email, description, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (name, phone, email, inn))
                client_id = cursor.lastrowid

                # 2. Создаем заказ
                cursor.execute("""
                    INSERT INTO orders (client_id, created_at, status)
                    VALUES (%s, NOW(), 'new')
                """, (client_id,))
                order_id = cursor.lastrowid

                # 3. Обрабатываем корзину
                for cart_key, quantity in cart_items.items():
                    quantity = int(quantity)
                    parts = cart_key.split('_')

                    if cart_key.startswith(('product_', 'prd_')):
                        product_id = parts[1]
                        variant_id = parts[2] if len(parts) > 2 else None

                        cursor.execute("""
                            SELECT p.name AS product_name, 
                                   v.name AS variant_name, 
                                   COALESCE(v.price, p.price) AS price
                            FROM products p
                            LEFT JOIN product_variants v ON v.id = %s AND v.product_id = p.id
                            WHERE p.id = %s
                        """, (variant_id, product_id))
                        product = cursor.fetchone()

                        if product:
                            cursor.execute("""
                                INSERT INTO order_items 
                                (order_id, product_id, product_name, variant_id, variant_name, quantity, price)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, (
                                order_id,
                                product_id,
                                product['product_name'],
                                variant_id,
                                product['variant_name'],
                                quantity,
                                product['price']
                            ))

                    elif cart_key.startswith('service_'):
                        service_id = parts[1]
                        variant_id = parts[2] if len(parts) > 2 else None

                        cursor.execute("""
                            SELECT s.name AS service_name, 
                                   v.name AS variant_name, 
                                   COALESCE(v.price, s.price) AS price
                            FROM services s
                            LEFT JOIN service_variants v ON v.id = %s AND v.service_id = s.id
                            WHERE s.id = %s
                        """, (variant_id, service_id))
                        service = cursor.fetchone()

                        if service:
                            cursor.execute("""
                                INSERT INTO order_items 
                                (order_id, product_id, product_name, variant_id, variant_name, quantity, price)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, (
                                order_id,
                                service_id,
                                service['service_name'],
                                variant_id,
                                service['variant_name'],
                                quantity,
                                service['price']
                            ))

                    elif cart_key.isdigit():
                        # Automation товары: просто ID, без вариантов и цены
                        cursor.execute("SELECT id, name FROM automation WHERE id = %s", (cart_key,))
                        automation = cursor.fetchone()

                        if automation:
                            cursor.execute("""
                                INSERT INTO order_items 
                                (order_id, product_id, product_name, quantity, price)
                                VALUES (%s, %s, %s, %s, NULL)
                            """, (
                                order_id,
                                automation['id'],
                                automation['name'],
                                quantity
                            ))

                connection.commit()

                # Очищаем корзину
                session.pop('cart', None)
                session.modified = True

                return jsonify(
                    success=True,
                    message='Заказ успешно сохранен',
                    cart_cleared=True
                )

        except Exception as e:
            connection.rollback()
            print(f"[DB ERROR] {str(e)}")
            return jsonify(success=False, error="Ошибка сохранения заказа"), 500

        finally:
            connection.close()

    except KeyError as e:
        return jsonify(success=False, message=f"Отсутствует обязательное поле: {e}"), 400
    except Exception as e:
        print(f"[SERVER ERROR] {str(e)}")
        return jsonify(success=False, message="Внутренняя ошибка сервера"), 500


@main_routes.route('/admin/clear-clients')
@auth.login_required
def clear_clients():
    try:
        app = create_app()
        connection = app.mysql_connection

        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM clients")
            connection.commit()

        return jsonify({'success': True, 'message': 'Таблица clients очищена'})

    except Exception as e:
        import traceback
        print(f"Ошибка при очистке таблицы clients: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

    finally:
        if connection:
            connection.close()
