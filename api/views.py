# api/views.py
from decimal import Decimal
from datetime import date
from collections import defaultdict

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.db.models import Sum, F
from django.db import models

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.db.models.functions import Abs

from .models import Category, Transaction, UserProfile
from .serializers import (
    UserSerializer,
    CategorySerializer,
    TransactionSerializer,
    UserProfileSerializer,
    ProfileUpdateSerializer,
    PasswordChangeSerializer,
)


# ---------- Simple hello (from earlier) ----------

@api_view(['GET'])
@permission_classes([AllowAny])
def hello(request):
    data = {
        "message": "Hello from Django backend!",
        "status": "ok"
    }
    return Response(data)


# ---------- Auth endpoints (signup/login/forgot) ----------

@api_view(['POST'])
@permission_classes([AllowAny])
def signup_view(request):
    name = request.data.get('name')
    email = request.data.get('email')
    password = request.data.get('password')

    if not name or not email or not password:
        return Response(
            {"error": "Name, email and password are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(email=email).exists():
        return Response(
            {"error": "Email is already registered."},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = User.objects.create_user(
        username=email,
        email=email,
        password=password,
        first_name=name
    )

    # Create profile with defaults
    UserProfile.objects.create(user=user)

    token, _ = Token.objects.get_or_create(user=user)

    return Response(
        {
            "token": token.key,
            "user": {
                "id": user.id,
                "name": user.first_name,
                "email": user.email,
            },
        },
        status=status.HTTP_201_CREATED
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response(
            {"error": "Email and password are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(username=email, password=password)

    if user is None:
        return Response(
            {"error": "Invalid email or password."},
            status=status.HTTP_400_BAD_REQUEST
        )

    token, _ = Token.objects.get_or_create(user=user)

    return Response(
        {
            "token": token.key,
            "user": {
                "id": user.id,
                "name": user.first_name,
                "email": user.email,
            },
        }
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_view(request):
    email = request.data.get('email')

    if not email:
        return Response(
            {"error": "Email is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # TODO: real email logic later
    return Response(
        {
            "message": "If an account with that email exists, a password reset link has been sent."
        }
    )


# ---------- Me / profile ----------

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)
        return Response({
            "user": UserSerializer(user).data,
            "profile": UserProfileSerializer(profile).data,
        })


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)
        return Response({
            "user": UserSerializer(user).data,
            "profile": UserProfileSerializer(profile).data,
        })

    def put(self, request):
        user = request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)
        serializer = ProfileUpdateSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        updated = serializer.update({'user': user, 'profile': profile}, serializer.validated_data)

        return Response({
            "user": UserSerializer(updated['user']).data,
            "profile": UserProfileSerializer(updated['profile']).data,
        })


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        current_password = serializer.validated_data['current_password']
        new_password = serializer.validated_data['new_password']

        user = request.user

        if not user.check_password(current_password):
            return Response(
                {"error": "Current password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            validate_password(new_password, user)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        return Response({"message": "Password changed successfully."})


# ---------- Category CRUD ----------

class CategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user).order_by('name')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)


# ---------- Transaction CRUD ----------

class TransactionListCreateView(generics.ListCreateAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Transaction.objects.filter(user=self.request.user).order_by('-date', '-id')

        # Optional filters (type, category, search)
        t_type = self.request.query_params.get('type')
        category_id = self.request.query_params.get('category')
        search = self.request.query_params.get('search')

        if t_type in ['income', 'expense']:
            qs = qs.filter(type=t_type)
        if category_id:
            qs = qs.filter(category_id=category_id)
        if search:
            qs = qs.filter(description__icontains=search)

        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)


# ---------- Dashboard summary ----------

class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        qs = Transaction.objects.filter(user=user)

        income_total = qs.filter(type='income').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

        expense_total = qs.filter(type='expense').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

        # expense_total will be negative if we store negative numbers; use abs
        expense_total_abs = abs(expense_total)

        balance = income_total - expense_total_abs

        # Last 6 months chart (income vs expenses per month)
        # We'll build it in python for simplicity
        chart_data_dict = defaultdict(lambda: {'income': Decimal('0'), 'expenses': Decimal('0')})

        for t in qs:
            month_label = t.date.strftime('%b')  # Jan, Feb, etc.
            if t.type == 'income':
                chart_data_dict[month_label]['income'] += t.amount
            else:
                chart_data_dict[month_label]['expenses'] += abs(t.amount)

        chart_data = [
            {"month": month, "income": float(vals['income']), "expenses": float(vals['expenses'])}
            for month, vals in chart_data_dict.items()
        ]

        # Recent transactions
        recent_qs = qs.order_by('-date', '-id')[:5]
        recent_transactions = TransactionSerializer(recent_qs, many=True).data

        return Response({
            "summary": {
                "total_income": float(income_total),
                "total_expenses": float(expense_total_abs),
                "balance": float(balance),
            },
            "chart": chart_data,
            "recent_transactions": recent_transactions,
        })


# ---------- Analytics ----------

class AnalyticsOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        qs = Transaction.objects.filter(user=user)

        # Spending by category (expenses only)
        expenses = qs.filter(type='expense', category__isnull=False).values(
            'category__name'
        ).annotate(
            total=Sum(Abs(F('amount')))
        ).order_by('-total')

        category_data = [
            {"name": item['category__name'], "value": float(item['total'])}
            for item in expenses
        ]

        # Simple monthly trend (net amount)
        trend_dict = defaultdict(Decimal)
        for t in qs:
            month_label = t.date.strftime('%b')
            # For trend: income positive, expenses negative
            trend_dict[month_label] += t.amount

        trend_data = [
            {"month": month, "amount": float(amount)}
            for month, amount in trend_dict.items()
        ]

        # Average daily spending (last 30 days, expenses)
        today = date.today()
        last_30 = today.fromordinal(today.toordinal() - 30)
        last_30_expenses = qs.filter(
            type='expense',
            date__gte=last_30,
            date__lte=today
        ).aggregate(
            total=Sum(Abs(F('amount')))
        )['total'] or Decimal('0')

        avg_daily = last_30_expenses / Decimal('30')

        # Top category (by expense)
        top_category = category_data[0]['name'] if category_data else None
        top_category_percent = None
        total_expenses_value = sum(c['value'] for c in category_data)
        if total_expenses_value > 0 and category_data:
            top_category_percent = (
                category_data[0]['value'] / total_expenses_value * 100.0
            )

        # Savings rate (income minus expense / income)
        income_total = qs.filter(type='income').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        expense_total = qs.filter(type='expense').aggregate(
            total=Sum(Abs(F('amount')))
        )['total'] or Decimal('0')

        savings_rate = None
        if income_total > 0:
            savings_rate = float(
                (income_total - expense_total) / income_total * Decimal('100')
            )

        return Response({
            "category_data": category_data,
            "trend_data": trend_data,
            "average_daily_spending": float(avg_daily),
            "top_category": top_category,
            "top_category_percent": top_category_percent,
            "savings_rate": savings_rate,
        })
