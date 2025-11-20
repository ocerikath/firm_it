document.addEventListener('DOMContentLoaded', () => {
    const deleteButtons = document.querySelectorAll('.btn-delete');

    deleteButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const orderId = button.dataset.orderId;

            if (!confirm(`Удалить заказ #${orderId}?`)) return;

            try {
                const response = await fetch(`/admin/orders/delete/${orderId}`, {
                    method: 'DELETE',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                    }
                });

                const result = await response.json();

                if (result.success) {
                    // Удалим карточку заказа из DOM
                    const orderCard = button.closest('.order-card');
                    if (orderCard) {
                        orderCard.remove();
                    }
                } else {
                    alert('Ошибка при удалении: ' + (result.error || 'Неизвестная ошибка'));
                }
            } catch (err) {
                alert('Произошла ошибка при удалении заказа.');
                console.error(err);
            }
        });
    });
});
