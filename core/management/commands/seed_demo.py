from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from core.models import Account, Category, Transaction


def _apply_balance(account, t_type, amount):
    if t_type == 'income':
        account.balance += amount
    else:
        account.balance -= amount
    account.save(update_fields=['balance'])


class Command(BaseCommand):
    help = 'Создаёт тестового пользователя demo со счетами, категориями и транзакциями за 6 месяцев'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Удалить пользователя demo перед созданием (если уже существует)',
        )

    def handle(self, *args, **options):
        if options['reset']:
            deleted, _ = User.objects.filter(username='demo').delete()
            if deleted:
                self.stdout.write(self.style.WARNING('Старый пользователь demo удалён.'))

        if User.objects.filter(username='demo').exists():
            self.stdout.write(self.style.ERROR(
                'Пользователь demo уже существует. Используйте --reset для пересоздания.'
            ))
            return

        # --- Пользователь ---
        user = User.objects.create_user(
            username='demo',
            password='demo12345',
            first_name='Демо',
            last_name='Пользователь',
            email='demo@example.com',
        )
        self.stdout.write(f'Создан пользователь: demo / demo12345')

        # --- Счета ---
        card = Account.objects.create(name='Основная карта', balance=Decimal('0'), currency='RUB', owner=user)
        wallet = Account.objects.create(name='Кошелёк', balance=Decimal('60000'), currency='RUB', owner=user)
        usd = Account.objects.create(name='Долларовый счёт', balance=Decimal('500.00'), currency='USD', owner=user)
        self.stdout.write(f'Создано счетов: 3')

        # --- Категории доходов ---
        cat_salary = Category.objects.create(name='Зарплата', type='income', color='#28a745', owner=user)
        cat_freelance = Category.objects.create(name='Фриланс', type='income', color='#17a2b8', owner=user)
        cat_gifts = Category.objects.create(name='Подарки', type='income', color='#fd7e14', owner=user)

        # --- Категории расходов ---
        cat_groceries = Category.objects.create(name='Продукты', type='expense', color='#dc3545', owner=user)
        cat_transport = Category.objects.create(name='Транспорт', type='expense', color='#6610f2', owner=user)
        cat_cafe = Category.objects.create(name='Кафе и рестораны', type='expense', color='#e83e8c', owner=user)
        cat_fun = Category.objects.create(name='Развлечения', type='expense', color='#ffc107', owner=user)
        cat_utility = Category.objects.create(name='Коммунальные услуги', type='expense', color='#20c997', owner=user)
        cat_clothes = Category.objects.create(name='Одежда', type='expense', color='#6f42c1', owner=user)
        self.stdout.write(f'Создано категорий: 9 (3 дохода + 6 расходов)')

        # --- Транзакции ---
        # Формат: (date, type, amount, category, account, description)
        # 6 месяцев: Dec 2025 – May 2026 (~38 записей, проверяет пагинацию и оба графика)
        transactions_raw = [
            # Декабрь 2025
            ('2025-12-01', 'income',  75000, cat_salary,   card,   'Зарплата за ноябрь'),
            ('2025-12-05', 'expense',  8500, cat_groceries, wallet, 'Продукты на неделю'),
            ('2025-12-10', 'expense',  1800, cat_transport, card,   'Проездной'),
            ('2025-12-15', 'expense',  3200, cat_cafe,      card,   'Корпоратив'),
            ('2025-12-20', 'expense',  5000, cat_clothes,   card,   'Куртка'),
            ('2025-12-25', 'expense',  4500, cat_groceries, wallet, 'Продукты к праздникам'),
            ('2025-12-28', 'income',  15000, cat_freelance,  card,   'Разработка сайта'),

            # Январь 2026
            ('2026-01-01', 'income',  75000, cat_salary,   card,   'Зарплата за декабрь'),
            ('2026-01-05', 'expense',  6500, cat_utility,  card,   'ЖКХ январь'),
            ('2026-01-08', 'expense',  7200, cat_groceries, wallet, 'Продукты'),
            ('2026-01-12', 'expense',  2500, cat_fun,      card,   'Кино и игры'),
            ('2026-01-20', 'expense',  1500, cat_transport, card,   'Такси'),
            ('2026-01-25', 'income',   8000, cat_gifts,    wallet, 'На день рождения'),

            # Февраль 2026
            ('2026-02-01', 'income',  75000, cat_salary,   card,   'Зарплата за январь'),
            ('2026-02-05', 'expense',  6500, cat_utility,  card,   'ЖКХ февраль'),
            ('2026-02-10', 'expense',  9000, cat_groceries, wallet, 'Продукты'),
            ('2026-02-14', 'expense',  4500, cat_cafe,     card,   'День Валентина'),
            ('2026-02-20', 'expense',  3500, cat_fun,      card,   'Концерт'),
            ('2026-02-25', 'income',  20000, cat_freelance, card,   'Разработка приложения'),

            # Март 2026
            ('2026-03-01', 'income',  75000, cat_salary,   card,   'Зарплата за февраль'),
            ('2026-03-05', 'expense',  6500, cat_utility,  card,   'ЖКХ март'),
            ('2026-03-08', 'expense',  8000, cat_groceries, wallet, '8 марта — продукты'),
            ('2026-03-08', 'expense',  6000, cat_cafe,     card,   '8 марта — ресторан'),
            ('2026-03-15', 'expense',  2000, cat_transport, card,   'Транспорт за месяц'),
            ('2026-03-25', 'expense', 12000, cat_clothes,  card,   'Весенний гардероб'),

            # Апрель 2026
            ('2026-04-01', 'income',  75000, cat_salary,   card,   'Зарплата за март'),
            ('2026-04-05', 'expense',  6500, cat_utility,  card,   'ЖКХ апрель'),
            ('2026-04-10', 'expense',  7500, cat_groceries, wallet, 'Продукты'),
            ('2026-04-15', 'expense',  3000, cat_cafe,     card,   'Обеды на работе'),
            ('2026-04-18', 'expense',  5000, cat_fun,      card,   'Выставка и кино'),
            ('2026-04-28', 'income',  25000, cat_freelance, card,   'Апрельский проект'),

            # Май 2026 (текущий месяц — данные для pie-графика и месячной статистики)
            ('2026-05-01', 'income',  75000, cat_salary,   card,   'Зарплата за апрель'),
            ('2026-05-05', 'expense',  6500, cat_utility,  card,   'ЖКХ май'),
            ('2026-05-08', 'expense',  8500, cat_groceries, wallet, 'Продукты'),
            ('2026-05-10', 'expense',  2500, cat_transport, card,   'Проездной май'),
            ('2026-05-12', 'expense',  4000, cat_cafe,     card,   'Кафе с друзьями'),
            ('2026-05-14', 'expense',  3500, cat_fun,      wallet, 'Боулинг и кино'),
            ('2026-05-15', 'expense',  9000, cat_clothes,  card,   'Летняя одежда'),
        ]

        for raw_date, t_type, amount, category, account, description in transactions_raw:
            tx_date = date.fromisoformat(raw_date)
            dec_amount = Decimal(str(amount))
            Transaction.objects.create(
                date=tx_date,
                type=t_type,
                amount=dec_amount,
                account=account,
                category=category,
                description=description,
                owner=user,
            )
            _apply_balance(account, t_type, dec_amount)

        self.stdout.write(f'Создано транзакций: {len(transactions_raw)}')

        # Итоговые балансы
        card.refresh_from_db()
        wallet.refresh_from_db()
        self.stdout.write(
            self.style.SUCCESS(
                f'\nГотово! Данные для входа:\n'
                f'  Логин:    demo\n'
                f'  Пароль:   demo12345\n\n'
                f'Итоговые балансы:\n'
                f'  {card.name}: {card.balance} RUB\n'
                f'  {wallet.name}: {wallet.balance} RUB\n'
                f'  {usd.name}: {usd.balance} USD\n'
            )
        )
