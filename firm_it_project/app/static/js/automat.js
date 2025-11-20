class CartManager {
    constructor() {
        this.initEventListeners();
        this.updateCartHeader();
        this.setupModalCloseHandlers();
        this.setupClearCartButton();
    }

    initEventListeners() {
        // Обработчики для разных типов кнопок
        document.addEventListener('click', (e) => {
            // Для страницы automation (третья страница)
            if (e.target.closest('.product-card')) {
                const card = e.target.closest('.product-card');
                if (!e.target.classList.contains('add-to-cart-label')) return;
                e.preventDefault();
                this.addAutomationProduct(card);
            }
            // Для страницы services
            else if (e.target.closest('.add-to-cart-service')) {
                e.preventDefault();
                this.addService(e.target.closest('.add-to-cart-service'));
            }
            // Для страницы products
            else if (e.target.closest('.store-product-add-btn')) {
                e.preventDefault();
                this.addRegularProduct(e.target.closest('.store-product-add-btn'));
            }
        });

        // Остальные обработчики без изменений
        document.querySelector('.cart')?.addEventListener('click', () => this.openCartModal());
        document.addEventListener('cartContentLoaded', () => {
            this.initCartItemHandlers();
            this.updateCartTotals();
            this.setupClearCartButton();
        });
    }

    // Метод для automation (третья страница)
    async addAutomationProduct(card) {
        try {
            const productId = card.getAttribute('data-product-id');
            const response = await fetch(`/add_to_cart/${productId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            this.handleAddResponse(data, card.querySelector('.add-to-cart-label'), 'Товар добавлен');
        } catch (error) {
            this.showError(error);
        }
    }

    // Метод для services
    async addService(button) {
        try {
            const serviceId = button.getAttribute('data-service-id');
            let variantId = null;
            
            if (!button.hasAttribute('data-no-variants')) {
                const variantSelect = document.querySelector(`select.variant-select[data-service-id="${serviceId}"]`);
                variantId = variantSelect ? variantSelect.value : button.getAttribute('data-variant-id');
                
                if (!variantId) {
                    this.showNotification('Выберите вариант услуги', true);
                    return;
                }
            }

            const response = await fetch(`/add_service_to_cart/${serviceId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ variant_id: variantId })
            });
            
            const data = await response.json();
            this.handleAddResponse(data, button, 'Услуга добавлена');
        } catch (error) {
            this.showError(error);
        }
    }

    // Метод для products
    async addRegularProduct(button) {
        try {
            const form = button.closest('form');
            const productId = form.querySelector('input[name="product_id"]').value;
            const variantSelect = form.querySelector('select[name="variant_id"]');
            const variantId = variantSelect ? variantSelect.value : null;

            const response = await fetch(`/add_product_to_cart/${productId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ variant_id: variantId })
            });
            
            const data = await response.json();
            this.handleAddResponse(data, button, 'Товар добавлен');
        } catch (error) {
            this.showError(error);
        }
    }

    // Общая обработка успешного добавления
    handleAddResponse(data, element, successMessage) {
        if (data.success) {
            element.classList.add('added');
            setTimeout(() => element.classList.remove('added'), 500);
            this.showNotification(successMessage);
            this.updateCartHeader();
            
            // Для кнопок на странице products
            if (element.classList.contains('store-product-add-btn')) {
                element.textContent = 'Добавлено';
                setTimeout(() => {
                    element.textContent = 'Добавить в корзину';
                }, 2000);
            }
        } else {
            this.showNotification(data.error || 'Ошибка при добавлении', true);
        }
    }

    // Обработка ошибок
    showError(error) {
        console.error('Ошибка:', error);
        this.showNotification('Ошибка при добавлении', true);
    }
    
    setupModalCloseHandlers() {
        const modal = document.getElementById('cart-modal');
    
        modal.addEventListener('click', (e) => {
            // Проверяем, был ли клик на самом модальном окне (не на его содержимом)
            if (e.target === modal) {
                this.closeCartModal();
            }
        });
        // Закрытие при клике на оверлей
        document.querySelector('.modal-overlay').addEventListener('click', () => {
            this.closeCartModal();
        });
    
        // Закрытие при клике на кнопку закрытия
        document.querySelector('.modal .close').addEventListener('click', () => {
            this.closeCartModal();
        });
    
        // Закрытие при нажатии Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && document.getElementById('cart-modal').style.display === 'flex') {
                this.closeCartModal();
            }
        });
    
    
        // Закрытие при нажатии Escape (оставляем как было, раз оно работает)
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const cartModal = document.getElementById('cart-modal');
                if (cartModal && window.getComputedStyle(cartModal).display !== 'none') {
                    this.closeCartModal();
                }
            }
        });
    }

    async openCartModal() {
        try {
            const response = await fetch('/cart');
            const html = await response.text();
            
            const container = document.getElementById('cart-items-container');
            container.innerHTML = html;
            
            const event = new Event('cartContentLoaded');
            document.dispatchEvent(event);
            
            document.getElementById('cart-modal').style.display = 'flex';
            document.body.style.overflow = 'hidden'; // Блокируем скролл страницы
        } catch (error) {
            console.error('Ошибка при загрузке корзины:', error);
        }
    }


    closeCartModal() {
        document.getElementById('cart-modal').style.display = 'none';
        document.body.style.overflow = ''; // Восстанавливаем скролл страницы
    }

    async updateQuantity(event, change) {
        const itemElement = event.target.closest('.cart-item');
        if (!itemElement) return;

        try {
            const itemId = itemElement.getAttribute('data-item-id');
            const itemType = itemElement.getAttribute('data-type');
            const variantId = itemElement.getAttribute('data-variant-id');
            const counter = itemElement.querySelector('.counter');
            const newQty = parseInt(counter.textContent) + change;

            if (newQty < 1) {
                this.removeItem(itemElement);
                return;
            }

            const response = await fetch(`/update_${itemType}_cart_item/${itemId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ change, variant_id: variantId })
            });

            if (response.ok) {
                counter.textContent = newQty;
                this.updateItemPrice(itemElement, newQty);
                this.updateCartTotals();
            }
            if (response.ok) {
                counter.textContent = newQty;
                this.updateItemPrice(itemElement, newQty);
                this.updateCartTotals();
                this.updateCartHeader(); // ✅ добавляем вот это
            }
            
        } catch (error) {
            console.error('Ошибка при обновлении количества:', error);
        }
    }

    async removeItem(itemElement) {
        if (!itemElement) return;
    
        try {
            const itemId = itemElement.getAttribute('data-item-id');
            const itemType = itemElement.getAttribute('data-type');
            const variantId = itemElement.getAttribute('data-variant-id');
    
            const response = await fetch(`/remove_${itemType}_from_cart/${itemId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ variant_id: variantId })
            });
    
            if (response.ok) {
                itemElement.remove();
                this.checkEmptyCart();
                this.updateCartTotals();
                this.updateCartHeader();
                this.showNotification('Товар удалён из корзины');
            }
        } catch (error) {
            console.error('Ошибка при удалении товара:', error);
            this.showNotification('Ошибка при удалении', true);
        }
    }
    initCartItemHandlers(container = document) {
        container.querySelectorAll('.plus').forEach(btn => {
            btn.addEventListener('click', (e) => this.updateQuantity(e, 1));
        });
    
        container.querySelectorAll('.minus').forEach(btn => {
            btn.addEventListener('click', (e) => this.updateQuantity(e, -1));
        });
    
        container.querySelectorAll('.remove-from-cart').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.removeItem(e.target.closest('.cart-item'));
            });
        });
    }

    updateItemPrice(itemElement, quantity) {
        const unitPrice = parseFloat(itemElement.getAttribute('data-unit-price'));
        const priceElement = itemElement.querySelector('.cart-item-price');
        
        if (unitPrice > 0 && priceElement) {
            priceElement.textContent = (unitPrice * quantity).toFixed(2) + ' руб.';
        }
    }

    async updateCartTotals() {
        try {
            const response = await fetch('/get_cart_total');
            const data = await response.json();

            const totalItemsElement = document.getElementById('total-items-count');
            const totalSumElement = document.getElementById('total-sum');

            if (totalItemsElement) totalItemsElement.textContent = data.items_count;
            if (totalSumElement) totalSumElement.textContent = data.total_sum.toFixed(2);
        } catch (error) {
            console.error('Ошибка при обновлении итогов:', error);
        }
    }

    async updateCartHeader() {
        try {
            const response = await fetch('/get_cart_total');
            const data = await response.json();
            
            const cartCount = document.querySelector('.cart-count');
            if (cartCount) {
                cartCount.textContent = data.items_count;
                if (data.items_count > 0) {
                    cartCount.classList.add('pulse');
                    setTimeout(() => cartCount.classList.remove('pulse'), 300);
                }
            }
        } catch (error) {
            console.error('Ошибка при обновлении шапки:', error);
        }
    }

    checkEmptyCart() {
        const container = document.getElementById('cart-items-container');
        if (container && container.querySelectorAll('.cart-item').length === 0) {
            container.innerHTML = '<div class="empty-cart"><p>Корзина пуста</p></div>';
        }
    }

    showNotification(message, isError = false) {
        const notification = document.getElementById('cart-notification');
        if (!notification) return;
        
        notification.textContent = message;
        notification.style.backgroundColor = isError ? '#ff4d4d' : '#4CAF50';
        notification.style.display = 'block';
        
        setTimeout(() => {
            notification.style.display = 'none';
        }, 3000);
    }

    setupClearCartButton() {
        const clearBtn = document.getElementById('clear-cart-button');
        const confirmBlock = document.getElementById('clear-cart-confirm');
        const yesBtn = document.getElementById('confirm-clear-yes');
        const noBtn = document.getElementById('confirm-clear-no');
    
        if (!clearBtn || !confirmBlock) return;
    
        clearBtn.addEventListener('click', () => {
            clearBtn.style.display = 'none';
            confirmBlock.classList.remove('hidden');
        });
    
        noBtn.addEventListener('click', () => {
            confirmBlock.classList.add('hidden');
            clearBtn.style.display = 'inline-block';
        });
    
        yesBtn.addEventListener('click', async () => {
            confirmBlock.classList.add('hidden');
            clearBtn.style.display = 'inline-block';
    
            try {
                const response = await fetch('/clear_cart');
                const data = await response.json();
                if (data.success) {
                    this.showNotification('Корзина очищена');
                    this.updateCartHeader();
                    this.openCartModal(); // обновить содержимое
                }
            } catch (err) {
                console.error('Ошибка очистки корзины:', err);
            }
        });
    }
    

}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    new CartManager();
});