# run.py
from flask import Flask, request, jsonify
import re
from app import create_app
from flask import session


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
@app.context_processor
def inject_cart_items():
    cart_items = []
    if 'cart' in session:
        # Загрузите данные из сессии, например:
        cart_items = session.get('cart', [])
    return dict(cart_items=cart_items)


# Функция для проверки номера телефона
def is_valid_phone(phone):
    pattern = r"^\+7 \(\d{3}\) \d{3} \d{2} \d{2}$"
    return re.match(pattern, phone) is not None

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    data = request.json

    # Валидация данных
    if not data.get('name') or not data.get('phone') or not data.get('agree'):
        return jsonify({"error": "Необходимо заполнить все обязательные поля"}), 400

    if not is_valid_phone(data['phone']):
        return jsonify({"error": "Неверный формат номера телефона"}), 400

    # Здесь можно добавить логику для сохранения данных в базу данных
    print("Данные формы:", data)

    return jsonify({"message": "Форма успешно отправлена"}), 200

if __name__ == '__main__':
    app.run(debug=True)