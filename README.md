# MTU FORUM

MTU FORUM — корпоративная платформа для подачи и обработки заявок на доступ к железнодорожным информационным системам. Проект объединяет Django API и административную часть с новым интерфейсом на React/Next.js.

## Возможности

- подача заявок без авторизации;
- обработка, редактирование, блокировка и удаление заявок;
- разграничение доступа по ролям, платформам, филиалам, организациям и предприятиям;
- управление пользователями и менеджерами организаций;
- справочники платформ, WEB-платформ, филиалов, организаций, предприятий и должностей;
- внутренние сообщения, Telegram-чаты и задачи разработчиков;
- вход по логину и паролю, OneID, E-IMZO и Face ID;
- русский, узбекский на латинице, узбекский на кириллице и английский языки;
- светлая, тёмная, системная и автоматическая тема по времени восхода и заката;
- настройки доступности;
- классический интерфейс Django и новый интерфейс React.

## Структура проекта

```text
core/                 Django-приложение, модели, формы, API и бизнес-логика
enakl_forum/          настройки Django и маршруты
frontend/             исходный код React/Next.js
static/next/          готовая статическая сборка React-приложения
static/               CSS, JavaScript, изображения и другие ресурсы
templates/            шаблоны классического Django-интерфейса
locale/               файлы переводов Django
manage.py              команды управления Django
requirements.txt       зависимости Python
.env.example           пример переменных окружения
```

## Требования

- Python 3.10 или новее;
- Node.js и npm для пересборки React-интерфейса;
- SQLite для локальной разработки или PostgreSQL для рабочего сервера.

## Быстрый запуск в Windows PowerShell

```powershell
git clone https://github.com/2000muhammad/MTU_FORUM.git
cd MTU_FORUM

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

После запуска доступны:

- новый публичный интерфейс: <http://127.0.0.1:8000/app/public/?lang=ru>;
- новый рабочий интерфейс: <http://127.0.0.1:8000/app/>;
- классический публичный интерфейс: <http://127.0.0.1:8000/ru/?legacy=1>;
- административная панель Django: <http://127.0.0.1:8000/admin/>.

## Запуск в Linux/macOS

```bash
git clone https://github.com/2000muhammad/MTU_FORUM.git
cd MTU_FORUM

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

## Переменные окружения

Скопируйте `.env.example` в `.env` и измените значения для своего окружения.

| Переменная | Назначение |
| --- | --- |
| `DJANGO_SECRET_KEY` | Секретный ключ Django |
| `DJANGO_DEBUG` | Режим разработки: `1` или `0` |
| `DJANGO_ALLOWED_HOSTS` | Разрешённые домены через запятую |
| `SITE_BASE_URL` | Доверенные HTTPS-адреса для CSRF |
| `SESSION_COOKIE_AGE` | Время обычной сессии в секундах |
| `REMEMBER_ME_COOKIE_AGE` | Время сессии «Запомнить меня» |
| `TELEGRAM_BOT_TOKEN` | Токен Telegram-бота |
| `TELEGRAM_API_KEY` | Ключ доступа к Telegram API проекта |
| `HRM_*` | Параметры интеграции с HRM |
| `DB_*` | Подключение к PostgreSQL |

Не добавляйте `.env`, токены, пароли и рабочие ключи в Git.

## React/Next.js

Исходный код нового интерфейса находится в каталоге `frontend`. Django обслуживает готовую статическую сборку из `static/next`.

Установка зависимостей и рабочий режим:

```powershell
cd frontend
npm ci
npm run dev
```

Создание рабочей статической сборки:

```powershell
cd frontend
npm ci
npm run build
```

Команда `npm run build` создаёт экспорт Next.js и автоматически копирует его в `static/next`. После любого изменения файлов в `frontend/src` необходимо выполнить эту команду и добавить обновлённый каталог `static/next` в коммит.

## База данных и миграции

После загрузки новых изменений применяйте миграции:

```powershell
python manage.py migrate
```

Проверка отсутствия незаписанных изменений моделей:

```powershell
python manage.py makemigrations --check --dry-run
```

По умолчанию используется SQLite. Для PostgreSQL заполните переменные `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` и `DB_PORT` в `.env`.

## Права доступа

Права назначаются через роли и профиль пользователя. Для обычного сотрудника список заявок ограничивается разрешёнными платформами и предприятиями. Менеджер филиала видит данные своего филиала, менеджер организации — своей организации. Суперадминистратор имеет полный доступ.

Ограничения применяются на сервере к:

- списку и статистике заявок;
- прямому открытию и редактированию заявки;
- уведомлениям;
- доступным вариантам в формах;
- справочникам предприятий и должностей.

## Проверка проекта

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Проверка React-сборки:

```powershell
cd frontend
npm ci
npm run build
```

## Обновление из GitHub

```powershell
git pull --rebase origin main
python manage.py migrate
cd frontend
npm ci
npm run build
cd ..
python manage.py check
```

После обновления перезапустите процесс Django на сервере.

## Подготовка к рабочему серверу

Перед публикацией:

1. Установите `DJANGO_DEBUG=0`.
2. Задайте уникальный `DJANGO_SECRET_KEY`.
3. Заполните `DJANGO_ALLOWED_HOSTS` и `SITE_BASE_URL`.
4. Подключите PostgreSQL.
5. Выполните миграции и `python manage.py collectstatic`.
6. Соберите React-интерфейс командой `npm run build`.
7. Настройте HTTPS, WSGI-сервер и обратный прокси.
8. Не храните секреты и рабочую базу данных в репозитории.

## Основные команды Git

```powershell
git status
git pull --rebase origin main
git add -A
git commit -m "Описание изменений"
git push origin HEAD:main
```
