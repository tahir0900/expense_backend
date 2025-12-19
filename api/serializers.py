# api/serializers.py
from decimal import Decimal
from django.db.models import Sum, F
from django.db.models.functions import Abs
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Category, Transaction, UserProfile


class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='first_name')

    class Meta:
        model = User
        fields = ['id', 'name', 'email']



class CategorySerializer(serializers.ModelSerializer):
    count = serializers.SerializerMethodField()
    spent = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'color', 'icon', 'type', 'budget', 'count', 'spent']

    def get_count(self, obj):
        """
        Number of transactions in this category for the current user.
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0

        return obj.transactions.filter(user=request.user).count()

    def get_spent(self, obj):
        """
        Total spent in this category (sum of ABS(expense amounts)) for current user.
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0.0

        total = obj.transactions.filter(
            user=request.user,
            type='expense',
        ).aggregate(
            total=Sum(Abs(F('amount')))
        )['total'] or Decimal('0')

        return float(total)

class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id',
            'description',
            'amount',
            'category',
            'category_name',
            'type',
            'date',
        ]

    def validate(self, attrs):
        t_type = attrs.get('type')
        amount = attrs.get('amount')

        # Ensure amount sign is consistent:
        # - income: positive
        # - expense: negative
        if t_type == 'income' and amount < 0:
            attrs['amount'] = abs(amount)
        if t_type == 'expense' and amount > 0:
            attrs['amount'] = -abs(amount)

        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['currency', 'date_format']


class ProfileUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    email = serializers.EmailField(required=False)
    currency = serializers.ChoiceField(
        choices=UserProfile.CURRENCY_CHOICES, required=False
    )
    date_format = serializers.ChoiceField(
        choices=UserProfile.DATE_FORMAT_CHOICES, required=False
    )

    def update(self, instance, validated_data):
        user = instance['user']
        profile = instance['profile']

        name = validated_data.get('name')
        email = validated_data.get('email')
        currency = validated_data.get('currency')
        date_format = validated_data.get('date_format')

        if name is not None:
            user.first_name = name
        if email is not None:
            user.email = email
            user.username = email  # keep username == email if you're using that pattern
        user.save()

        if currency is not None:
            profile.currency = currency
        if date_format is not None:
            profile.date_format = date_format
        profile.save()

        return {'user': user, 'profile': profile}


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField()
