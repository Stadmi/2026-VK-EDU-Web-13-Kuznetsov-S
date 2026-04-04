# 2026-VK-EDU-Web-13-Kuznetsov-S

AskPupkin — учебный Django-проект с разделением на приложения, шаблонизацией и пагинацией.

## Локальный запуск

1. Создайте виртуальное окружение:
   ```bash
   python -m venv venv
   ```
2. Активируйте его:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Выполните миграции:
   ```bash
   python manage.py migrate
   ```
5. Запустите сервер:
   ```bash
   python manage.py runserver
   ```

Откройте http://127.0.0.1:8000/ в браузере.

## Запуск через Docker Compose

```bash
docker compose up --build
```

После сборки сайт будет доступен по адресу http://127.0.0.1:8000/.

## Структура проекта

- `application/` — настройки Django проекта
- `core/` — страницы пользователя: вход, регистрация, профиль
- `questions/` — страницы вопросов: список, теги, подробности, создание вопроса
- `templates/` — HTML-шаблоны
- `public/static/` — статические CSS/JS/картинки
- `media/` — загруженные файлы
