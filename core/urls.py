from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='dashboard', permanent=False), name='home'),

    # Auth
    path('auth/login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('auth/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('auth/register/', views.RegisterView.as_view(), name='register'),

    # Dashboard (заглушка)
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    # Accounts
    path('accounts/', views.AccountListView.as_view(), name='account-list'),
    path('accounts/create/', views.AccountCreateView.as_view(), name='account-create'),
    path('accounts/<int:pk>/edit/', views.AccountUpdateView.as_view(), name='account-edit'),
    path('accounts/<int:pk>/delete/', views.AccountDeleteView.as_view(), name='account-delete'),

    # Categories
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category-create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category-edit'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category-delete'),

    # Transactions
    path('transactions/', views.TransactionListView.as_view(), name='transaction-list'),
    path('transactions/create/', views.TransactionCreateView.as_view(), name='transaction-create'),
    path('transactions/<int:pk>/edit/', views.TransactionUpdateView.as_view(), name='transaction-edit'),
    path('transactions/<int:pk>/delete/', views.TransactionDeleteView.as_view(), name='transaction-delete'),
]
