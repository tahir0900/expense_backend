# api/models.py
from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    TYPE_CHOICES = (
        ('income', 'Income'),
        ('expense', 'Expense'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='categories'
    )
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default="#3b82f6")  # hex color
    icon = models.CharField(max_length=50, default="ShoppingCart")
    type = models.CharField(max_length=7, choices=TYPE_CHOICES, default='expense')
    budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'name')  # each user can't have two "Food" categories

    def __str__(self):
        return f"{self.name} ({self.user.email})"


class Transaction(models.Model):
    TYPE_CHOICES = (
        ('income', 'Income'),
        ('expense', 'Expense'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=7, choices=TYPE_CHOICES)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.description} - {self.amount} ({self.type})"


class UserProfile(models.Model):
    CURRENCY_CHOICES = (
        ('USD', 'USD ($)'),
        ('EUR', 'EUR (€)'),
        ('GBP', 'GBP (£)'),
    )

    DATE_FORMAT_CHOICES = (
        ('MM/DD/YYYY', 'MM/DD/YYYY'),
        ('DD/MM/YYYY', 'DD/MM/YYYY'),
        ('YYYY-MM-DD', 'YYYY-MM-DD'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='USD')
    date_format = models.CharField(max_length=20, choices=DATE_FORMAT_CHOICES, default='YYYY-MM-DD')

    def __str__(self):
        return f"Profile for {self.user.email}"
