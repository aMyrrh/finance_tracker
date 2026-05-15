# Веб-приложение для учёта личных финансов

Курсовая работа, 2 курс. Django + PostgreSQL + Bootstrap 5.

## Стек

| Компонент | Версия |
|---|---|
| Python | 3.10.11 |
| Django | 5.1.9 |
| PostgreSQL | 16 (Docker) |
| psycopg2-binary | 2.9.12 |
| python-decouple | 3.8 |
| Bootstrap | 5.3.3 (CDN) |
| Chart.js | 4.4.4 (CDN) |

## Запуск проекта

```powershell
# 1. Запустить PostgreSQL
docker start finance_postgres

# 2. Запустить сервер (порт 8001 — 8000 занят WSL)
python manage.py runserver 8001
```

Открыть: http://127.0.0.1:8001/

Суперпользователь: `admin` / `admin123` → http://127.0.0.1:8001/admin/

## Модель данных

```
User (встроенная Django)
├── Account  — банковский счёт (name, balance Decimal, currency, owner)
├── Category — категория (name, type income/expense, color hex, owner)
└── Transaction — транзакция (amount Decimal, date, type, account FK,
                               category FK nullable, description, owner)
```

**Важно:** деньги хранятся как `DecimalField(max_digits=12, decimal_places=2)`, никогда `FloatField`.

## Реализованные этапы

### Этап 1 — Инициализация
- Структура Django-проекта: `finance_tracker/` (конфигурация) + `core/` (приложение)
- `settings.py`: подключение через `python-decouple`, PostgreSQL, `TIME_ZONE = 'Europe/Moscow'`, `LANGUAGE_CODE = 'ru'`
- `.env` для секретов, `.gitignore` (`.env` исключён)
- PostgreSQL запускается в Docker: `docker run --name finance_postgres ...`

### Этап 2 — Модели и AdminSite
- Модели `Account`, `Category`, `Transaction` в `core/models.py`
- Регистрация в `core/admin.py` через `@admin.register` с `list_display`, `list_filter`, `search_fields`
- Миграция: `python manage.py makemigrations core && python manage.py migrate`

### Этап 3 — Авторизация
- Вход/выход через встроенные `LoginView` / `LogoutView` Django
- Регистрация — `RegisterView` на основе `UserCreationForm`, после регистрации автологин
- URL: `/auth/login/`, `/auth/logout/`, `/auth/register/`
- Настройки редиректов: `LOGIN_URL`, `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL`

### Этап 4 — CRUD счетов и категорий
- CBV: `ListView`, `CreateView`, `UpdateView`, `DeleteView`
- Безопасность: `LoginRequiredMixin` + `get_queryset()` фильтрует по `owner=request.user`
- В `CreateView.form_valid()` устанавливается `form.instance.owner = request.user`
- HTML-пикер цвета для категорий через `<input type="color">`

### Этап 5 — CRUD транзакций + фильтры + пагинация
- `TransactionForm` принимает `user` в `__init__` → фильтрует `account` и `category` по владельцу
- Фильтры GET-параметрами: по дате, типу, счёту, категории
- Пагинация: `paginate_by = 20`. Ссылки пагинации сохраняют параметры фильтров через `filter_query`
- Обновление баланса счёта при создании/изменении/удалении транзакции (`_apply_balance`)
- `select_related('account', 'category')` — оптимизация: один JOIN вместо N запросов

### Этап 6 — Дашборд
- Общий баланс: `Account.objects.filter(owner=user).aggregate(total=Sum('balance'))`
- Доходы/расходы за текущий месяц: фильтр `date__year`, `date__month` + `Sum`
- `timezone.localdate()` вместо `datetime.date.today()` — учитывает `TIME_ZONE = 'Europe/Moscow'`
- Последние 8 транзакций, список счетов

### Этап 7 — Графики Chart.js
- **Pie-chart** — расходы по категориям за месяц: `values('category__name', 'category__color').annotate(total=Sum('amount'))`
- **Bar-chart** — доходы/расходы за 6 месяцев: `TruncMonth('date')` группирует по месяцу
- Данные передаются в JS через `json.dumps(..., ensure_ascii=False)` и `{{ var|safe }}` в шаблоне

### Этап 8 — Импорт CSV
- Формат: `date,type,amount,category,account,description` (кодировка UTF-8)
- Парсер `_parse_csv`: построчная валидация, счёт и категория ищутся по `owner=user`
- `utf-8-sig` убирает BOM-маркер Excel
- Результат импорта: построчный отчёт (ОК / Ошибка с описанием)
- URL: `/transactions/import/`

### Этап 9 — Оформление Bootstrap 5
- Единый `base.html`: тёмный sidebar для авторизованных, чистый layout для страниц входа
- Активный пункт меню определяется через `request.resolver_match.url_name`
- `{% with url_name=... %}` — избегает повторных обращений к `request.resolver_match`
- `{% now "Y" %}` в footer вместо ошибочного `{{ "now"|date:"Y" }}`

## Структура файлов

```
prac/
├── finance_tracker/
│   ├── settings.py       # конфигурация проекта
│   ├── urls.py           # корневые URL
│   └── wsgi.py
├── core/
│   ├── models.py         # Account, Category, Transaction
│   ├── views.py          # все CBV и вспомогательные функции
│   ├── forms.py          # AccountForm, CategoryForm, TransactionForm, CSVImportForm
│   ├── urls.py           # все маршруты приложения
│   ├── admin.py          # регистрация в Django Admin
│   └── migrations/
├── templates/
│   ├── base.html         # базовый шаблон (sidebar + navbar)
│   ├── dashboard.html    # дашборд с графиками
│   ├── auth/             # login.html, register.html
│   ├── accounts/         # list, form, confirm_delete
│   ├── categories/       # list, form, confirm_delete
│   └── transactions/     # list, form, confirm_delete, import
├── static/               # CSS/JS (пока пустая)
├── .env                  # секреты (не в git)
├── .gitignore
├── requirements.txt
└── PROJECT.md            # этот файл
```

## Известные особенности

- Сервер запускается на порту **8001** (порт 8000 занят WSL2 relay)
- Docker-контейнер PostgreSQL нужно запускать вручную после перезагрузки: `docker start finance_postgres`
- `LANGUAGE_CODE = 'ru'` переводит интерфейс Django Admin на русский
