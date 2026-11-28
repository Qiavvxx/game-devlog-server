# Дневники разработки игр

Небольшой серверный API для игровых проектов и записей о ходе их разработки.

## Запуск

Нужен Python 3.12 или новее.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Создай секретный ключ командой `python3 -c 'import secrets; print(secrets.token_urlsafe(32))'` и вставь результат вместо значения `SECRET_KEY` в `.env`.

Запусти сервер:

```bash
uvicorn app.main:app --reload
```

Интерактивная документация API будет доступна по адресу `http://127.0.0.1:8000/docs`.

## Возможности API

- регистрация и вход;
- игровые проекты с жанром, движком и этапом разработки;
- задачи проекта со сроком, приоритетом и состоянием;
- записи дневника с видом работы, затраченным временем, результатом, трудностями и следующим шагом;
- отбор записей по виду работы и периоду;
- сводка по проекту: число записей, затраченное время и состояние задач;
- отдельный доступ каждого пользователя к своим проектам и записям.

Для проекта доступны этапы `idea`, `in_development`, `testing`, `released` и `paused`. В дневнике можно указать `game_design`, `programming`, `graphics`, `audio`, `testing` или `other`. Состояния задач: `planned`, `in_progress` и `done`; приоритеты: `low`, `medium` и `high`.

## Структура кода

- `app/main.py` — маршруты API;
- `app/models.py` — операции с данными;
- `app/database.py` — подключение и таблицы SQLite;
- `app/schemas.py` — проверка запросов и формат ответов;
- `app/security.py` — проверка паролей и токенов.

## Проверка

```bash
pip install -r requirements-dev.txt
pytest
```
