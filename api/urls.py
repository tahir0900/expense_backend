# api/urls.py
from django.urls import path
from .views import (
    hello,
    signup_view,
    login_view,
    forgot_password_view,
    MeView,
    ProfileView,
    ChangePasswordView,
    CategoryListCreateView,
    CategoryDetailView,
    TransactionListCreateView,
    TransactionDetailView,
    DashboardSummaryView,
    AnalyticsOverviewView,
)

from django.http import JsonResponse

def health(request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path("health/", health, name="health"),
    path('hello/', hello, name='hello'),

    # auth
    path('auth/signup/', signup_view, name='signup'),
    path('auth/login/', login_view, name='login'),
    path('auth/forgot-password/', forgot_password_view, name='forgot-password'),

    # user/profile
    path('me/', MeView.as_view(), name='me'),
    path('settings/profile/', ProfileView.as_view(), name='profile'),
    path('settings/change-password/', ChangePasswordView.as_view(), name='change-password'),

    # path('me/', MeView.as_view(), name='me'),
    



    # categories
    path('categories/', CategoryListCreateView.as_view(), name='category-list'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),

    # transactions
    path('transactions/', TransactionListCreateView.as_view(), name='transaction-list'),
    path('transactions/<int:pk>/', TransactionDetailView.as_view(), name='transaction-detail'),

    # dashboard & analytics
    path('dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('analytics/overview/', AnalyticsOverviewView.as_view(), name='analytics-overview'),
]
