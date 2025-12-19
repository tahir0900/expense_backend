# api/admin.py
from django.contrib import admin
from .models import Category, Transaction, UserProfile

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'type', 'budget')
    list_filter = ('type', 'user')
    search_fields = ('name', 'user__email')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'description', 'user', 'category', 'amount', 'type', 'date')
    list_filter = ('type', 'date', 'user')
    search_fields = ('description', 'user__email')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'currency', 'date_format')
