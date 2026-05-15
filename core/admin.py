from django.contrib import admin
from .models import Account, Category, Transaction


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'balance', 'currency', 'owner', 'created_at')
    list_filter = ('currency', 'owner')
    search_fields = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'color', 'owner')
    list_filter = ('type', 'owner')
    search_fields = ('name',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'type', 'amount', 'account', 'category', 'owner')
    list_filter = ('type', 'owner', 'date')
    search_fields = ('description',)
    date_hierarchy = 'date'
