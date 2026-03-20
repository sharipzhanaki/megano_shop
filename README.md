# Megano Shop

Интернет-магазин с REST API на Django REST Framework и React-фронтендом. Поддерживает каталог товаров, корзину для анонимных и авторизованных пользователей, заказы с доставкой и оплатой.

## Оглавление
- [Технологии](#технологии)
- [Архитектура](#архитектура)
- [Установка и запуск](#установка-и-запуск)
- [Переменные окружения](#переменные-окружения)
- [API документация](#api-документация)
- [Тестирование](#тестирование)
- [Структура проекта](#структура-проекта)
- [Статус проекта](#статус-проекта)

---

## Технологии

- **Python 3.10+**, Django 5.2, Django REST Framework 3.16
- **PostgreSQL** — основная база данных
- **Gunicorn** — WSGI-сервер
- **Nginx** — reverse proxy, раздача статики и медиафайлов
- **drf-spectacular** — генерация OpenAPI 3 / Swagger документации
- **pytest**, pytest-django, factory\_boy — тестирование
- **Pillow** — обработка изображений
- **django-filter** — фильтрация каталога

---

## Архитектура

Монолитное Django-приложение, разбитое на независимые модули (apps). Бизнес-логика вынесена в сервисный слой (`services.py`) отдельно от вьюх.

```
Browser
  │
  ▼
Nginx (порт 80)
  ├── /static/  → staticfiles/   (кэш 30 дней)
  ├── /media/   → uploads/       (кэш 7 дней)
  └── /api/*, / → Gunicorn :8000
                    │
                    ▼
              Django + DRF
          ┌────────────────────┐
          │  catalog           │  товары, категории, отзывы, акции
          │  orders            │  корзина, заказы, оплата
          │  profile_user      │  регистрация, профиль, аватар
          └────────────────────┘
                    │
                    ▼
              PostgreSQL
```

**Ключевые решения:**
- Корзина анонимного пользователя хранится в сессии, при входе автоматически мигрирует в БД
- Цены в заказе фиксируются на момент оформления с учётом активных акций
- Остатки на складе уменьшаются только при оплате, а не при создании заказа

---

## Установка и запуск

### Требования
- Python 3.10+
- PostgreSQL 14+

### Быстрый старт

```bash
# 1. Клонировать репозиторий
git clone <repo-url>
cd megano_shop

# 2. Создать виртуальное окружение
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Настроить переменные окружения
cp .env.example .env
# Открыть .env и заполнить значения (см. раздел ниже)

# 5. Применить миграции
cd diploma_backend
python manage.py migrate

# 6. Загрузить тестовые данные (опционально)
python manage.py loaddata fixtures/*.json

# 7. Собрать статику
python manage.py collectstatic --noinput

# 8. Запустить сервер
python manage.py runserver
```

Приложение доступно на `http://localhost:8000`

---

## Переменные окружения

Скопируйте `.env.template` в `.env` и заполните:

```env
# База данных
POSTGRES_DB=megano_shop
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Django
SECRET_KEY=your-secret-key
DEBUG=True                          # False в продакшне
ALLOWED_HOSTS=localhost,127.0.0.1   # Через запятую без пробелов
```

> Файл `.env` добавлен в `.gitignore` — не коммитьте реальные данные.

---

## API документация

При запущенном сервере документация доступна по адресам:

| URL | Описание |
|-----|---------|
| `/api/schema/swagger/` | Swagger UI |
| `/api/schema/redoc/` | ReDoc |
| `/api/schema/` | OpenAPI YAML/JSON |

### Основные эндпоинты

```
# Каталог
GET  /api/categories/           — дерево категорий
GET  /api/catalog/              — список товаров (фильтры, сортировка, пагинация)
GET  /api/product/<id>/         — карточка товара
POST /api/product/<id>/reviews  — оставить отзыв
GET  /api/products/popular/     — популярные товары
GET  /api/products/limited/     — лимитированные товары
GET  /api/banners/              — баннеры главной страницы
GET  /api/sales/                — активные акции

# Пользователи
POST /api/sign-up               — регистрация
POST /api/sign-in               — вход
POST /api/sign-out              — выход
GET  /api/profile               — профиль пользователя
POST /api/profile               — обновить профиль
POST /api/profile/password      — сменить пароль
POST /api/profile/avatar        — загрузить аватар

# Корзина и заказы
GET    /api/basket              — содержимое корзины
POST   /api/basket              — добавить товар
DELETE /api/basket              — удалить товар
POST   /api/orders              — оформить заказ
GET    /api/order/<id>          — детали заказа
POST   /api/order/<id>          — подтвердить адрес и тип доставки
POST   /api/payment/<id>        — оплатить заказ
```

**Параметры фильтрации каталога:** `name`, `minPrice`, `maxPrice`, `freeDelivery`, `available`, `category`, `tags[]`, `sort`, `sortType`, `currentPage`, `limit`

---

## Тестирование

```bash
cd diploma_backend

# Все тесты
pytest

# С подробным выводом
pytest -v

# Конкретный модуль
pytest profile_user/tests.py -v
```

---

## Структура проекта

```
megano_shop/
├── diploma_backend/
│   ├── catalog/            # Товары, категории, отзывы, акции
│   ├── orders/             # Корзина, заказы, оплата
│   ├── profile_user/       # Пользователи и профили
│   ├── fixtures/           # Тестовые данные
│   ├── logs/               # Логи приложения (ротация 5 МБ × 5 файлов)
│   ├── uploads/            # Загружаемые файлы (аватары, фото товаров)
│   └── diploma_backend/    # Конфигурация Django (settings, urls)
├── diploma-frontend/       # React-фронтенд (read-only пакет)
├── nginx/
│   └── megano.conf         # Конфигурация Nginx
├── .env.example
├── requirements.txt
└── requirements-dev.txt
```

---

## Статус проекта

Pet-проект, разработан в рамках дипломной работы. Реализован полный цикл покупки: от просмотра каталога до оплаты заказа.

**Что можно улучшить в будущем:**
- Настроить HTTPS в Nginx
- Добавить Celery для фоновых задач (письма, уведомления)
- Расширить покрытие тестами
