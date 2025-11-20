document.addEventListener("DOMContentLoaded", () => {
    const phoneInput = document.getElementById("phone");
    const nameInput = document.getElementById("name");
    const form = document.getElementById("feedback-form");
    const submitButton = document.getElementById("submit-button");
    const buttonText = document.getElementById("button-text");
    const loadingSpinner = submitButton.querySelector(".loading-spinner");

    // +7 ( появляется сразу при фокусе на поле телефона
    phoneInput.addEventListener("focus", () => {
        if (phoneInput.value === "") {
            phoneInput.value = "+7 (";
        }
    });

    // При потере фокуса, если номер пустой, убираем +7 (
    phoneInput.addEventListener("blur", () => {
        const inputWithoutDigits = phoneInput.value.replace(/\D/g, "").length <= 1;
        if (inputWithoutDigits) {
            phoneInput.value = "";
        }
    });

    // Форматирование номера телефона
    phoneInput.addEventListener("input", () => {
        let currentValue = phoneInput.value.replace(/\D/g, "");
        if (currentValue.length > 0) {
            let formattedValue = "+7 (";
            if (currentValue.length > 1) {
                formattedValue += currentValue.substring(1, 4);
            }
            if (currentValue.length >= 5) {
                formattedValue += ") " + currentValue.substring(4, 7);
            }
            if (currentValue.length >= 8) {
                formattedValue += " " + currentValue.substring(7, 9);
            }
            if (currentValue.length >= 10) {
                formattedValue += " " + currentValue.substring(9, 11);
            }
            phoneInput.value = formattedValue;
        }

        // Скрываем ошибки при вводе в поле телефона
        hideError(phoneInput);
    });

    // Скрываем ошибку имени при вводе текста
    nameInput.addEventListener("input", () => {
        hideError(nameInput);
    });

    // Функция для показа сообщений об ошибке
    function showError(field, errText) {
        const errorDiv = field.nextElementSibling;
        if (errorDiv && errorDiv.classList.contains("error-message")) {
            errorDiv.textContent = errText;
            errorDiv.style.display = "block";
        }
        field.classList.add("field-err");
    }

    // Функция для скрытия сообщений об ошибке
    function hideError(field) {
        const errorDiv = field.nextElementSibling;
        if (errorDiv && errorDiv.classList.contains("error-message")) {
            errorDiv.style.display = "none";
        }
        field.classList.remove("field-err");
    }

    // Заменяем обработчик submit формы
    form.addEventListener("submit", async function(event) {
        event.preventDefault();
        
        // Валидация формы
        let valid = true;
        
        if (nameInput.value.trim() === "") {
            showError(nameInput, "Обязательное поле");
            valid = false;
        } else {
            hideError(nameInput);
        }
    
        const phoneDigits = phoneInput.value.replace(/\D/g, "").length;
        if (phoneDigits <= 1) {
            showError(phoneInput, "Обязательное поле");
            valid = false;
        } else if (phoneDigits < 11) {
            showError(phoneInput, "Введите корректный номер телефона");
            valid = false;
        } else {
            hideError(phoneInput);
        }
    
        if (!valid) return;
    
        // Показываем индикатор загрузки
        submitButton.disabled = true;
        buttonText.textContent = "Отправка...";
        loadingSpinner.style.display = "block";
    
        try {
            // Собираем данные формы
            const formData = new FormData(form);
            
            // Добавляем флаг, что это форма из корзины
            const isCartForm = document.getElementById('cart-modal')?.contains(form);
            if (isCartForm) {
                formData.append('from_cart', 'true');
            }
    
            // Отправляем на сервер
            const response = await fetch("/submit-order", {
                method: "POST",
                body: formData,
                credentials: "same-origin" 
            });
    
            const data = await response.json();
            
            if (data.success) {
                // Успешная отправка
                form.reset();
                
                // Обновляем интерфейс корзины
                if (data.cart_cleared) {
                    document.querySelectorAll('.cart-count').forEach(el => {
                        el.textContent = '0';
                    });
                    
                    // Если это форма из корзины - закрываем модалку
                    if (isCartForm) {
                        document.getElementById('cart-modal').style.display = 'none';
                        
                        // Показываем ваше оригинальное уведомление
                        const notification = document.getElementById('cart-notification');
                        if (notification) {
                            notification.textContent = 'Заказ успешно отправлен';
                            notification.style.backgroundColor = '#4CAF50';
                            notification.style.display = 'block';
                            setTimeout(() => {
                                notification.style.display = 'none';
                            }, 3000);
                        }
                    }
                }
                
                // Ваше оригинальное уведомление для форм вне корзины
                if (!isCartForm) {
                    const notification = document.createElement('div');
                    notification.className = 'form-notification success';
                    notification.textContent = 'Заявка отправлена';
                    form.appendChild(notification);
                    setTimeout(() => notification.remove(), 3000);
                }
                
                // Обновляем состояние кнопки
                submitButton.classList.add("success");
                buttonText.textContent = "Отправлено";
            } else {
                throw new Error(data.error || "Ошибка при отправке");
            }
        } catch (error) {
            // Ваше оригинальное уведомление об ошибке
            const errorElement = document.createElement('div');
            errorElement.className = 'form-notification error';
            errorElement.textContent = error.message;
            form.appendChild(errorElement);
            setTimeout(() => errorElement.remove(), 3000);
            
            console.error("Ошибка:", error);
        } finally {
            submitButton.disabled = false;
            loadingSpinner.style.display = "none";
            setTimeout(() => {
                if (submitButton.classList.contains("success")) {
                    buttonText.textContent = "Оставить заявку";
                    submitButton.classList.remove("success");
                }
            }, 3000);
        }
    });
    
    // Ваши оригинальные функции для ошибок
    function showError(field, errText) {
        const errorDiv = field.nextElementSibling;
        if (errorDiv && errorDiv.classList.contains("error-message")) {
            errorDiv.textContent = errText;
            errorDiv.style.display = "block";
        }
        field.classList.add("field-err");
    }
    
    function hideError(field) {
        const errorDiv = field.nextElementSibling;
        if (errorDiv && errorDiv.classList.contains("error-message")) {
            errorDiv.style.display = "none";
        }
        field.classList.remove("field-err");
    }
    
});



