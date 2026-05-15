from django.db import models
from django.contrib.auth.models import User


class Account(models.Model):
    CURRENCY_CHOICES = [
        ('RUB', 'Рубль'),
        ('USD', 'Доллар'),
        ('EUR', 'Евро'),
    ]

    name = models.CharField('Название', max_length=100)
    balance = models.DecimalField('Баланс', max_digits=12, decimal_places=2, default=0)
    currency = models.CharField('Валюта', max_length=3, choices=CURRENCY_CHOICES, default='RUB')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts', verbose_name='Владелец')
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        verbose_name = 'Счёт'
        verbose_name_plural = 'Счета'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.currency})'


class Category(models.Model):
    TYPE_CHOICES = [
        ('income', 'Доход'),
        ('expense', 'Расход'),
    ]

    name = models.CharField('Название', max_length=100)
    type = models.CharField('Тип', max_length=7, choices=TYPE_CHOICES)
    color = models.CharField('Цвет', max_length=7, default='#6c757d')  # hex, например #ff5733
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories', verbose_name='Владелец')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['type', 'name']

    def __str__(self):
        return f'{self.name} ({self.get_type_display()})'


class Transaction(models.Model):
    TYPE_CHOICES = [
        ('income', 'Доход'),
        ('expense', 'Расход'),
    ]

    amount = models.DecimalField('Сумма', max_digits=12, decimal_places=2)
    date = models.DateField('Дата')
    type = models.CharField('Тип', max_length=7, choices=TYPE_CHOICES)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions', verbose_name='Счёт')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions', verbose_name='Категория')
    description = models.TextField('Описание', blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions', verbose_name='Владелец')
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'
        ordering = ['-date', '-created_at']

    def __str__(self):
        sign = '+' if self.type == 'income' else '-'
        return f'{sign}{self.amount} — {self.date}'
