from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import AccountForm, CategoryForm, TransactionForm
from .models import Account, Category, Transaction


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class RegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'auth/register.html', {'form': UserCreationForm()})

    def post(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
        return render(request, 'auth/register.html', {'form': form})


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class DashboardView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        now = timezone.localdate()  # текущая дата в Europe/Moscow

        # Суммируем баланс по всем счетам пользователя одним SQL-запросом
        total_balance = (Account.objects
                         .filter(owner=user)
                         .aggregate(total=Sum('balance'))['total'] or 0)

        # Доходы и расходы за текущий месяц
        month_qs = Transaction.objects.filter(
            owner=user,
            date__year=now.year,
            date__month=now.month,
        )
        month_income = (month_qs.filter(type='income')
                        .aggregate(total=Sum('amount'))['total'] or 0)
        month_expense = (month_qs.filter(type='expense')
                         .aggregate(total=Sum('amount'))['total'] or 0)

        last_transactions = (Transaction.objects
                             .filter(owner=user)
                             .select_related('account', 'category')[:8])

        accounts = Account.objects.filter(owner=user)

        ctx = {
            'total_balance': total_balance,
            'month_income': month_income,
            'month_expense': month_expense,
            'month_net': month_income - month_expense,
            'last_transactions': last_transactions,
            'accounts': accounts,
            'current_month': now.strftime('%B %Y'),
        }
        return render(request, 'dashboard.html', ctx)


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------

class AccountListView(LoginRequiredMixin, ListView):
    model = Account
    template_name = 'accounts/list.html'
    context_object_name = 'accounts'

    def get_queryset(self):
        return Account.objects.filter(owner=self.request.user)


class AccountCreateView(LoginRequiredMixin, CreateView):
    model = Account
    form_class = AccountForm
    template_name = 'accounts/form.html'
    success_url = reverse_lazy('account-list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Счёт успешно создан.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Новый счёт'
        return ctx


class AccountUpdateView(LoginRequiredMixin, UpdateView):
    model = Account
    form_class = AccountForm
    template_name = 'accounts/form.html'
    success_url = reverse_lazy('account-list')

    def get_queryset(self):
        return Account.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Счёт обновлён.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Редактировать счёт'
        return ctx


class AccountDeleteView(LoginRequiredMixin, DeleteView):
    model = Account
    template_name = 'accounts/confirm_delete.html'
    success_url = reverse_lazy('account-list')

    def get_queryset(self):
        return Account.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Счёт удалён.')
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'categories/list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.filter(owner=self.request.user)


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'categories/form.html'
    success_url = reverse_lazy('category-list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Категория создана.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Новая категория'
        return ctx


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'categories/form.html'
    success_url = reverse_lazy('category-list')

    def get_queryset(self):
        return Category.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Категория обновлена.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Редактировать категорию'
        return ctx


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = 'categories/confirm_delete.html'
    success_url = reverse_lazy('category-list')

    def get_queryset(self):
        return Category.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Категория удалена.')
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

def _apply_balance(account, t_type, amount, reverse=False):
    """Изменяет баланс счёта. reverse=True — откатывает эффект транзакции."""
    if t_type == 'income':
        account.balance += amount if not reverse else -amount
    else:
        account.balance -= amount if not reverse else -amount
    account.save(update_fields=['balance'])


class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'transactions/list.html'
    context_object_name = 'transactions'
    paginate_by = 20

    def get_queryset(self):
        qs = (Transaction.objects
              .filter(owner=self.request.user)
              # select_related подгружает связанные объекты одним JOIN-запросом
              # вместо N отдельных запросов для каждой строки
              .select_related('account', 'category'))

        p = self.request.GET
        if p.get('date_from'):
            qs = qs.filter(date__gte=p['date_from'])
        if p.get('date_to'):
            qs = qs.filter(date__lte=p['date_to'])
        if p.get('account'):
            qs = qs.filter(account_id=p['account'])
        if p.get('category'):
            qs = qs.filter(category_id=p['category'])
        if p.get('type') in ('income', 'expense'):
            qs = qs.filter(type=p['type'])

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['accounts'] = Account.objects.filter(owner=self.request.user)
        ctx['categories'] = Category.objects.filter(owner=self.request.user)
        ctx['current_filters'] = self.request.GET

        # Строка фильтров без параметра page — для ссылок пагинации
        get_copy = self.request.GET.copy()
        get_copy.pop('page', None)
        ctx['filter_query'] = get_copy.urlencode()
        return ctx


class TransactionCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'transactions/form.html'
    success_url = reverse_lazy('transaction-list')

    def get_form_kwargs(self):
        # Передаём user в форму, чтобы она показывала только «наши» счета и категории
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        _apply_balance(self.object.account, self.object.type, self.object.amount)
        messages.success(self.request, 'Транзакция добавлена.')
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Новая транзакция'
        return ctx


class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'transactions/form.html'
    success_url = reverse_lazy('transaction-list')

    def get_queryset(self):
        return Transaction.objects.filter(owner=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Откатываем старый эффект на баланс, потом применяем новый
        old = Transaction.objects.get(pk=self.object.pk)
        _apply_balance(old.account, old.type, old.amount, reverse=True)
        response = super().form_valid(form)
        _apply_balance(self.object.account, self.object.type, self.object.amount)
        messages.success(self.request, 'Транзакция обновлена.')
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Редактировать транзакцию'
        return ctx


class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction
    template_name = 'transactions/confirm_delete.html'
    success_url = reverse_lazy('transaction-list')

    def get_queryset(self):
        return Transaction.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        _apply_balance(self.object.account, self.object.type, self.object.amount, reverse=True)
        messages.success(self.request, 'Транзакция удалена.')
        return super().form_valid(form)
