# Task Manager (FastAPI)

Помимо базовых операций CRUD (Create, Read, Update, Delete - все по 1,25 балла) есть:

- Сортировка задач по различным критериям, таким как заголовок, статус или дата создания (1,25 балла)
- Добавление приоритетов к задачам и возможность выводить топ-N самых приоритетных задач (1,25 балла)
- Реализация функционала поиска по тексту задач (применение - хочешь найти строку в описании задачи или заголовке, но не помнишь в какой), достаточно проверять на вхождение подстроки полным перебором строк (2.5 балла)
- Реализация аутентификации пользователей с использованием JWT-токенов: доступны только его задачи для всех запросов, в т.ч. отображаться и изменяться могут только собственные задачи этого пользователя (2.8 бонусных баллов)
- Кэширование для запросов, которые по моему мнению, стоит кэшировать, объясняю выбор (0.2 бонусных балла):
  - Кэшируются: GET /tasks (с sort_by/order) и GET /tasks/top (с n), потому что это частые запросы с небольшим числом вариантов параметров, кэш уменьшает обращения к БД; TTL задаётся в настройках; после создания/изменения/удаления задачи для пользователя версия ключа кэша увеличивается, чтобы не отдавать устаревшие списки

## Пуск

```bash
cd homework_fastapi
python -m pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Документация API: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) 

Проверка, что сервер поднят: GET [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

Таблицы в SQLite (`tasks.db`) создаются при старте приложения (`lifespan` в `app/main.py`)

## Аутентификация

1. `POST /auth/register` - JSON: `username` (от 3 символов), `password` (от 6)
2. `POST /auth/login` - форма OAuth2 (`username`, `password`); ответ: `access_token`, `token_type: bearer`
3. Для `/tasks/*`: заголовок `Authorization: Bearer <token>`

В Swagger: выполните login, затем **Authorize** и вставьте токен

## Задачи


| Метод  | Путь               | Описание                                                                                            |
| ------ | ------------------ | --------------------------------------------------------------------------------------------------- |
| GET    | `/tasks`           | Список; query: `sort_by` = `title` | `status` | `created_at` | `priority`, `order` = `asc` | `desc` |
| POST   | `/tasks`           | Создание                                                                                            |
| GET    | `/tasks/search?q=` | Подстрока в заголовке или описании (без учёта регистра, полный перебор в памяти)                    |
| GET    | `/tasks/top?n=`    | До `n` задач с наибольшим `priority` (1-500, по умолчанию 5)                                        |
| GET    | `/tasks/{id}`      | Одна задача                                                                                         |
| PUT    | `/tasks/{id}`      | Полная замена полей                                                                                 |
| PATCH  | `/tasks/{id}`      | Частичное обновление                                                                                |
| DELETE | `/tasks/{id}`      | Удаление                                                                                            |


**Приоритет:** большее число = выше (для `/tasks/top`)

**Статусы в API:** `pending`, `in_progress`, `completed` - в ответе также `status_label` на русском ("в ожидании", "в работе", "завершено")

## Тесты

Каталог `tests/`, для БД в тестах используется SQLite in-memory (см. `tests/conftest.py`), таблицы перед тестами обнуляются

```bash
python -m pip install -r requirements.txt
python -m pytest tests
```

Покрытие:

```bash
python -m coverage run -m pytest tests
python -m coverage report -m
python -m coverage html -d htmlcov
```

Цифры последнего прогона: `tests/COVERAGE_TOTAL.txt`, кратко - `tests/COVERAGE_REPORT.txt`, отчёт в браузере - `htmlcov/index.html`

## Нагрузка (Locust)

Сначала `uvicorn app.main:app --host 127.0.0.1 --port 8000`, затем Locust

```bash
locust -f locustfile.py --host=http://127.0.0.1:8000
```

Без UI, например: `locust -f locustfile.py --host=http://127.0.0.1:8000 --headless -u 20 -r 5 -t 30s`

Скрин лога одного прогона: `tests/LOAD_TEST_SAMPLE_OUTPUT.txt`

## Docker

То же приложение, но для ДЗ по контейнерам - через compose. Два сервиса: `web` (FastAPI) и `db` (mysql 8). Файлы: `Dockerfile`, `docker-compose.yml`. Данные базы в volume `mysql_data`.

```bash
docker compose up --build
```

mysql обычно поднимается не сразу, секунд 10-15. web ждёт healthcheck в compose, плюс retry на создание таблиц в `app/main.py`.

- http://127.0.0.1:8000/ - страница с задачами
- http://127.0.0.1:8000/docs - swagger

Без docker всё как раньше - sqlite из `.env`. В compose в `DATABASE_URL` прописан mysql.

Остановить: `docker compose down` (volume не трогает). `docker compose down -v` - удалит данные в volume.

Проверка volume: создать задачу, потом `docker compose rm -sf db && docker compose up -d`, подождать и снова GET `/tasks` - задача должна остаться.

asciinema: https://asciinema.org/a/NeU9CXaQxTFIGP9e