# MTU FORUM

MTU FORUM состоит из двух отдельных приложений:

- **Django** — только backend: API, авторизация, права доступа, база данных, медиафайлы и служебная административная панель;
- **React/Next.js** — единственный пользовательский frontend.

Django не создаёт и не обслуживает пользовательские HTML-страницы. Старые адреса автоматически перенаправляются в React.

## Структура

```text
core/                 модели, формы, API и бизнес-логика Django
enakl_forum/          настройки и backend-маршруты
frontend/             React/Next.js frontend
static/               общие изображения и статические ресурсы backend
locale/               переводы
manage.py             команды Django
requirements.txt      зависимости Python
```

## Локальный запуск

Откройте два окна PowerShell.

Backend:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Frontend:

```powershell
cd frontend
npm ci
npm run dev
```

Открывайте интерфейс по адресу <http://127.0.0.1:3000/app/public/?lang=ru>. Backend API доступен на <http://127.0.0.1:8000/api/>, служебная панель Django — на <http://127.0.0.1:8000/admin/>.

## Переменные окружения

| Переменная | Назначение | Значение для разработки |
| --- | --- | --- |
| `FRONTEND_URL` | адрес React-приложения | `http://127.0.0.1:3000` |
| `DJANGO_BACKEND_URL` | backend для прокси Next.js | `http://127.0.0.1:8000` |
| `DJANGO_SECRET_KEY` | секретный ключ Django | замените в рабочей среде |
| `DJANGO_DEBUG` | режим разработки | `1` |
| `DJANGO_ALLOWED_HOSTS` | разрешённые backend-хосты | `127.0.0.1,localhost` |
| `SITE_BASE_URL` | дополнительные доверенные CSRF origins | адреса через запятую |
| `DB_*` | подключение к PostgreSQL | необязательно для SQLite |
| `TELEGRAM_*`, `HRM_*` | внешние интеграции | по настройкам сервера |

`DJANGO_BACKEND_URL` задаётся для процесса Next.js. При локальном запуске можно не указывать: используется `http://127.0.0.1:8000`.

## Проверка

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
cd frontend
npm run build
```

## Рабочий сервер

1. Запустите Django через WSGI/ASGI на внутреннем порту.
2. Соберите и запустите Next.js: `npm ci`, `npm run build`, `npm start`.
3. Направьте пользовательский домен на Next.js.
4. Проксируйте `/api/`, `/media/` и `/static/` в Django либо используйте встроенные rewrites Next.js.
5. Укажите `FRONTEND_URL`, `DJANGO_BACKEND_URL`, `DJANGO_DEBUG=0`, разрешённые хосты и HTTPS origins.
6. Выполните `python manage.py migrate` и `python manage.py collectstatic`.

## Обновление

```powershell
git pull --rebase origin main
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py check
cd frontend
npm ci
npm run build
```

После обновления перезапустите оба процесса: Django и Next.js.
