# MTU FORUM

MTU FORUM — корпоративная платформа для подачи и обработки заявок на доступ к железнодорожным информационным системам.

Проект содержит два совместимых интерфейса:

- классический интерфейс Django;
- новый интерфейс React/Next.js.

Пользователь может переключаться между версиями через переключатель **«Старая версия / Новая версия»**. Обе версии используют одну базу данных, одну систему авторизации и одинаковые серверные права доступа.

## Возможности

- публичная подача заявок без авторизации;
- обработка, редактирование, блокировка и удаление заявок;
- ограничение заявок по платформам и предприятиям пользователя;
- отдельная область данных для менеджера филиала и менеджера организации;
- управление пользователями, менеджерами и ролями;
- случайные пароли при создании аккаунта без заданного пароля и при сбросе пароля;
- справочники платформ, филиалов, организаций, предприятий и должностей;
- внутренние сообщения, Telegram-чаты и задания разработчиков;
- вход по логину и паролю, OneID, E-IMZO и Face ID;
- русский, O‘zbekcha, ўзбекча и английский языки;
- светлая, тёмная, системная и автоматическая тема по восходу и закату;
- настройки доступности;
- API для Telegram-бота и внешних интеграций.

## Технологии

- Python 3.10+;
- Django 5;
- React 19;
- Next.js 16;
- SQLite для разработки или PostgreSQL для рабочего сервера;
- `python-telegram-bot`, Requests и Pillow.

## Структура проекта

```text
core/                 модели, формы, API, права и бизнес-логика Django
core/tests/           автоматические backend-тесты
enakl_forum/          настройки и маршруты Django
frontend/             исходный код React/Next.js
static/next/          готовая React-сборка, которую обслуживает Django
static/               стили, JavaScript, изображения и иконки
templates/            шаблоны классического Django-интерфейса
locale/               переводы Django
telegram_bot/         Telegram-часть проекта
manage.py             управление Django
requirements.txt      Python-зависимости
.env.example          пример настроек окружения
```

## Быстрый запуск в Windows

```powershell
git clone https://github.com/2000muhammad/MTU_FORUM.git
cd MTU_FORUM

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser

cd frontend
npm ci
npm run build
cd ..

python manage.py runserver 127.0.0.1:8000
```

Откройте <http://127.0.0.1:8000/>.

## Быстрый запуск в Linux или macOS

```bash
git clone https://github.com/2000muhammad/MTU_FORUM.git
cd MTU_FORUM

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
python manage.py migrate
python manage.py createsuperuser

cd frontend
npm ci
npm run build
cd ..

python manage.py runserver 127.0.0.1:8000
```

## Адреса

| Раздел | Адрес |
| --- | --- |
| Новая публичная версия | <http://127.0.0.1:8000/app/public/?lang=ru> |
| Новая рабочая версия | <http://127.0.0.1:8000/app/> |
| Старая публичная версия | <http://127.0.0.1:8000/ru/?legacy=1> |
| Старая страница входа | <http://127.0.0.1:8000/ru/login/?legacy=1> |
| Django Admin | <http://127.0.0.1:8000/admin/> |
| Backend API | <http://127.0.0.1:8000/api/> |

Коды языков: `ru`, `uz`, `uz-cyrl`, `en`.

## React/Next.js

Исходный код нового интерфейса находится в `frontend`. Рабочая сборка создаётся командой:

```powershell
cd frontend
npm ci
npm run build
```

Команда выполняет `next build`, создаёт статический экспорт и копирует его в `static/next`. Django обслуживает эту сборку по адресу `/app/`. После изменения React-кода необходимо повторить сборку и добавить обновлённый `static/next` в Git.

Для разработки компонентов можно использовать:

```powershell
cd frontend
npm run dev
```

Основной интегрированный режим проекта запускается через Django на порту `8000`.

## Переменные окружения

Скопируйте `.env.example` в `.env`. Файл `.env` не должен попадать в Git.

| Переменная | Назначение |
| --- | --- |
| `DJANGO_SECRET_KEY` | секретный ключ Django |
| `DJANGO_DEBUG` | режим разработки: `1` или `0` |
| `DJANGO_ALLOWED_HOSTS` | разрешённые домены через запятую |
| `SITE_BASE_URL` | доверенный адрес сайта для CSRF |
| `SESSION_COOKIE_AGE` | срок обычной сессии в секундах |
| `REMEMBER_ME_COOKIE_AGE` | срок сессии «Запомнить меня» |
| `TELEGRAM_BOT_TOKEN` | токен Telegram-бота |
| `TELEGRAM_API_KEY` | ключ серверного Telegram API |
| `HRM_*` | настройки интеграции с HRM |
| `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | подключение PostgreSQL |

## Права доступа

Права рассчитываются на сервере и не зависят от выбранной версии интерфейса.

- Суперадминистратор видит все данные.
- Менеджер филиала видит предприятия, должности и заявки своего филиала.
- Менеджер организации видит данные своей организации.
- Сотрудник видит заявки только разрешённых ему платформ и предприятий.

Эти ограничения применяются к спискам, статистике, прямому открытию заявки, редактированию, уведомлениям и справочникам.

## Пароли пользователей

Если при создании пользователя или менеджера пароль не указан, система создаёт случайный пароль из 12 символов и показывает его администратору. При сбросе пароля также создаётся новый случайный пароль. Постоянный пароль `1234567` не используется.

## Миграции и проверки

```powershell
python manage.py migrate
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Проверка React:

```powershell
cd frontend
npm ci
npm run build
```

## Обновление проекта

```powershell
git pull --rebase origin master
.\.venv\Scripts\python.exe manage.py migrate

cd frontend
npm ci
npm run build
cd ..

.\.venv\Scripts\python.exe manage.py check
```

После обновления перезапустите процесс Django.

## Рабочий сервер

1. Установите `DJANGO_DEBUG=0`.
2. Укажите уникальный `DJANGO_SECRET_KEY`.
3. Настройте `DJANGO_ALLOWED_HOSTS` и `SITE_BASE_URL`.
4. Подключите PostgreSQL.
5. Выполните миграции и `python manage.py collectstatic`.
6. Соберите React командой `npm run build`.
7. Запустите Django через WSGI/ASGI-сервер.
8. Настройте HTTPS и обратный прокси.
9. Не храните секреты, рабочую базу и пользовательские медиафайлы в репозитории.

## Git

Основная ветка проекта — `master`.

```powershell
git status
git pull --rebase origin master
git add -A
git commit -m "Описание изменений"
git push origin master
```
