from django import forms
from .models import Account, Category, Transaction


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'balance', 'currency']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'name': 'Название',
            'balance': 'Начальный баланс',
            'currency': 'Валюта',
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'type', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            # type="color" — встроенный HTML-пикер цвета, без сторонних библиотек
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
        }
        labels = {
            'name': 'Название',
            'type': 'Тип',
            'color': 'Цвет',
        }


class CSVImportForm(forms.Form):
    csv_file = forms.FileField(
        label='CSV-файл',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.csv'}),
        help_text='Кодировка UTF-8. Столбцы: date, type, amount, category, account, description',
    )


class TransactionForm(forms.ModelForm):
    # Принимаем user, чтобы показывать только счета и категории этого пользователя
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['account'].queryset = Account.objects.filter(owner=user)
            self.fields['category'].queryset = Category.objects.filter(owner=user)

    class Meta:
        model = Transaction
        fields = ['date', 'type', 'amount', 'account', 'category', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'account': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'date': 'Дата',
            'type': 'Тип',
            'amount': 'Сумма',
            'account': 'Счёт',
            'category': 'Категория',
            'description': 'Описание',
        }
