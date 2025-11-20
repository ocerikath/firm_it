// Плавная прокрутка к секциям
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

// Анимация появления элементов при прокрутке
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('animate');
        }
    });
}, { threshold: 0.2 });

document.querySelectorAll('.hero-content h1, .hero-content p, .cta-button, .about-container, .advantage-item, .faq-item').forEach(element => {
    observer.observe(element);
});

// Открытие и закрытие бургер-меню
const burgerMenu = document.querySelector('.burger-menu');
const navLinks = document.querySelector('.nav-links');

burgerMenu.addEventListener('click', () => {
    burgerMenu.classList.toggle('active');
    navLinks.classList.toggle('active');
});

// Закрытие меню при клике вне его области
document.addEventListener('click', (event) => {
    const isClickInsideMenu = burgerMenu.contains(event.target) || navLinks.contains(event.target);
    if (!isClickInsideMenu) {
        burgerMenu.classList.remove('active');
        navLinks.classList.remove('active');
    }
});


const images = document.querySelectorAll('.background-animation img');

if (images.length > 0) {
    let currentIndex = 0;

    function changeBackground() {
        const nextIndex = (currentIndex + 1) % images.length;
        images[nextIndex].classList.add('active');

        setTimeout(() => {
            images[currentIndex].classList.remove('active');
            currentIndex = nextIndex;
        }, 1000);
    }

    setTimeout(() => {
        images[currentIndex].classList.add('active');
    }, 100);

    setInterval(changeBackground, 5000);
}



document.addEventListener('DOMContentLoaded', () => {
    // Получаем все карточки
    const cards = document.querySelectorAll('.advantage-item');

    // Функция для переворота карточки
    function flipCard(card) {
        const front = card.querySelector('.front');
        const back = card.querySelector('.back');

        front.style.transform = 'rotateY(180deg)';
        back.style.transform = 'rotateY(360deg)';
    }

    // Функция для возврата карточки в исходное состояние
    function unflipCard(card) {
        const front = card.querySelector('.front');
        const back = card.querySelector('.back');

        front.style.transform = 'rotateY(0deg)';
        back.style.transform = 'rotateY(180deg)';
    }

    // Добавляем обработчики событий для каждой карточки
    cards.forEach((card) => {
        let flipTimeout;

        // При наведении мыши
        card.addEventListener('mouseenter', () => {
            flipTimeout = setTimeout(() => {
                flipCard(card);
            }, 100); // Задержка 1 секунда
        });

        // Когда курсор уходит
        card.addEventListener('mouseleave', () => {
            clearTimeout(flipTimeout); // Отменяем таймер, если курсор ушел раньше времени
            unflipCard(card);
        });
    });
});


document.addEventListener('DOMContentLoaded', () => {
    const cards = document.querySelectorAll('.advantage-item');

    // Добавляем логику только для десктопной версии
    if (window.innerWidth > 768) {
        cards.forEach((card) => {
            const moreInfoButton = card.querySelector('.more-info');
            const detailedInfo = card.querySelector('.detailed-info');

            // При клике на "Подробнее"
            if (moreInfoButton && detailedInfo) {
                moreInfoButton.addEventListener('click', (e) => {
                    e.stopPropagation();
                    detailedInfo.classList.toggle('visible');
                    moreInfoButton.style.display = 'none';
                });
            }

            // При наведении на карточку
            card.addEventListener('mouseenter', () => {
                card.classList.add('active');
            });

            // Когда курсор уходит
            card.addEventListener('mouseleave', () => {
                card.classList.remove('active');
                if (detailedInfo) detailedInfo.classList.remove('visible');
                if (moreInfoButton) moreInfoButton.style.display = 'block';
            });
        });
    }
});


document.addEventListener('DOMContentLoaded', () => {
    const fadeElements = document.querySelectorAll('.fade-in');

    const checkVisibility = () => {
        fadeElements.forEach((element) => {
            const elementTop = element.getBoundingClientRect().top;
            const elementBottom = element.getBoundingClientRect().bottom;

            // Если элемент в зоне видимости
            if (elementTop < window.innerHeight && elementBottom > 0) {
                element.classList.add('active');
            }
        });
    };

    // Проверяем при загрузке страницы и при скролле
    window.addEventListener('scroll', checkVisibility);
    checkVisibility(); // Проверяем сразу при загрузке
});


document.addEventListener('DOMContentLoaded', () => {
    const faqQuestions = document.querySelectorAll('.faq-question');

    faqQuestions.forEach((question) => {
        question.addEventListener('click', () => {
            const faqItem = question.parentElement;
            const faqAnswer = faqItem.querySelector('.faq-answer');

            // Закрываем все открытые вопросы
            document.querySelectorAll('.faq-item').forEach((item) => {
                if (item !== faqItem) {
                    item.classList.remove('active');
                    item.querySelector('.faq-answer').style.maxHeight = null;
                }
            });

            // Открываем/закрываем текущий вопрос
            faqItem.classList.toggle('active');

            if (faqItem.classList.contains('active')) {
                faqAnswer.style.maxHeight = faqAnswer.scrollHeight + 'px'; // Открываем
            } else {
                faqAnswer.style.maxHeight = null; // Закрываем
            }
        });
    });
});

// Кнопка "Наверх"
const scrollToTopBtn = document.getElementById('scrollToTopBtn');



// Прокрутка наверх при клике
scrollToTopBtn.addEventListener('click', () => {
    window.scrollTo({
        top: 0,
        behavior: 'smooth' // Плавная прокрутка
    });
});

