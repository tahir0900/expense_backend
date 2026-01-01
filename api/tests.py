from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from decimal import Decimal
from datetime import date, timedelta
from .models import Category, Transaction, UserProfile


# ========== Model Tests ==========

class CategoryModelTest(TestCase):
    """Test cases for Category model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpass123'
        )
    
    def test_category_creation(self):
        """Test creating a category"""
        category = Category.objects.create(
            user=self.user,
            name='Food',
            color='#ff0000',
            icon='Restaurant',
            type='expense',
            budget=500.00
        )
        self.assertEqual(category.name, 'Food')
        self.assertEqual(category.type, 'expense')
        self.assertEqual(category.budget, Decimal('500.00'))
        self.assertEqual(str(category), f'Food ({self.user.email})')
    
    def test_unique_category_per_user(self):
        """Test that each user can't have duplicate category names"""
        Category.objects.create(
            user=self.user,
            name='Food',
            type='expense'
        )
        # Trying to create another category with same name should raise error
        with self.assertRaises(Exception):
            Category.objects.create(
                user=self.user,
                name='Food',
                type='expense'
            )


class TransactionModelTest(TestCase):
    """Test cases for Transaction model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            user=self.user,
            name='Food',
            type='expense'
        )
    
    def test_transaction_creation(self):
        """Test creating a transaction"""
        transaction = Transaction.objects.create(
            user=self.user,
            category=self.category,
            description='Lunch at restaurant',
            amount=25.50,
            type='expense',
            date=date.today()
        )
        self.assertEqual(transaction.description, 'Lunch at restaurant')
        self.assertEqual(transaction.amount, Decimal('25.50'))
        self.assertEqual(transaction.type, 'expense')
        self.assertIn('Lunch at restaurant', str(transaction))
    
    def test_transaction_without_category(self):
        """Test creating a transaction without category"""
        transaction = Transaction.objects.create(
            user=self.user,
            category=None,
            description='Cash payment',
            amount=50.00,
            type='expense',
            date=date.today()
        )
        self.assertIsNone(transaction.category)
        self.assertEqual(transaction.amount, Decimal('50.00'))


class UserProfileModelTest(TestCase):
    """Test cases for UserProfile model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpass123'
        )
    
    def test_profile_creation(self):
        """Test creating a user profile"""
        profile = UserProfile.objects.create(
            user=self.user,
            currency='USD',
            date_format='YYYY-MM-DD'
        )
        self.assertEqual(profile.currency, 'USD')
        self.assertEqual(profile.date_format, 'YYYY-MM-DD')
        self.assertIn(self.user.email, str(profile))


# ========== API Tests ==========

class AuthAPITest(APITestCase):
    """Test cases for authentication endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.signup_url = '/api/auth/signup/'
        self.login_url = '/api/auth/login/'
        self.forgot_password_url = '/api/auth/forgot-password/'
    
    def test_user_signup(self):
        """Test user registration"""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'securepass123'
        }
        response = self.client.post(self.signup_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['email'], 'john@example.com')
        
        # Check that user profile was created
        user = User.objects.get(email='john@example.com')
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
    
    def test_signup_with_existing_email(self):
        """Test signup with already registered email"""
        User.objects.create_user(
            username='john@example.com',
            email='john@example.com',
            password='pass123'
        )
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'securepass123'
        }
        response = self.client.post(self.signup_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_signup_missing_fields(self):
        """Test signup with missing fields"""
        data = {'email': 'john@example.com'}
        response = self.client.post(self.signup_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_user_login(self):
        """Test user login"""
        # Create user first
        user = User.objects.create_user(
            username='john@example.com',
            email='john@example.com',
            password='securepass123'
        )
        
        data = {
            'email': 'john@example.com',
            'password': 'securepass123'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['email'], 'john@example.com')
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        data = {
            'email': 'wrong@example.com',
            'password': 'wrongpass'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_forgot_password(self):
        """Test forgot password endpoint"""
        data = {'email': 'john@example.com'}
        response = self.client.post(self.forgot_password_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)


class ProfileAPITest(APITestCase):
    """Test cases for profile endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpass123',
            first_name='Test User'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.profile = UserProfile.objects.create(user=self.user)
    
    def test_get_me(self):
        """Test getting current user info"""
        response = self.client.get('/api/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertIn('profile', response.data)
        self.assertEqual(response.data['user']['email'], 'testuser@example.com')
    
    def test_get_profile(self):
        """Test getting user profile"""
        response = self.client.get('/api/settings/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertIn('profile', response.data)
    
    def test_update_profile(self):
        """Test updating user profile"""
        data = {
            'name': 'Updated Name',
            'currency': 'EUR',
            'date_format': 'DD/MM/YYYY'
        }
        response = self.client.put('/api/settings/profile/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify changes
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated Name')
        self.assertEqual(self.profile.currency, 'EUR')


class CategoryAPITest(APITestCase):
    """Test cases for category endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
    
    def test_create_category(self):
        """Test creating a category"""
        data = {
            'name': 'Food',
            'color': '#ff0000',
            'icon': 'Restaurant',
            'type': 'expense',
            'budget': 500.00
        }
        response = self.client.post('/api/categories/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Food')
        self.assertEqual(Category.objects.count(), 1)
    
    def test_list_categories(self):
        """Test listing categories"""
        Category.objects.create(user=self.user, name='Food', type='expense')
        Category.objects.create(user=self.user, name='Salary', type='income')
        
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_get_category_detail(self):
        """Test getting a specific category"""
        category = Category.objects.create(
            user=self.user,
            name='Food',
            type='expense'
        )
        response = self.client.get(f'/api/categories/{category.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Food')
    
    def test_update_category(self):
        """Test updating a category"""
        category = Category.objects.create(
            user=self.user,
            name='Food',
            type='expense'
        )
        data = {'name': 'Groceries', 'budget': 600.00}
        response = self.client.patch(f'/api/categories/{category.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        category.refresh_from_db()
        self.assertEqual(category.name, 'Groceries')
    
    def test_delete_category(self):
        """Test deleting a category"""
        category = Category.objects.create(
            user=self.user,
            name='Food',
            type='expense'
        )
        response = self.client.delete(f'/api/categories/{category.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Category.objects.count(), 0)
    
    def test_user_can_only_see_own_categories(self):
        """Test that users can only see their own categories"""
        other_user = User.objects.create_user(
            username='other@example.com',
            email='other@example.com',
            password='pass123'
        )
        Category.objects.create(user=other_user, name='Other Food', type='expense')
        Category.objects.create(user=self.user, name='My Food', type='expense')
        
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'My Food')


class TransactionAPITest(APITestCase):
    """Test cases for transaction endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.category = Category.objects.create(
            user=self.user,
            name='Food',
            type='expense'
        )
    
    def test_create_transaction(self):
        """Test creating a transaction"""
        data = {
            'category': self.category.id,
            'description': 'Lunch',
            'amount': 25.50,
            'type': 'expense',
            'date': str(date.today())
        }
        response = self.client.post('/api/transactions/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['description'], 'Lunch')
        self.assertEqual(Transaction.objects.count(), 1)
    
    def test_list_transactions(self):
        """Test listing transactions"""
        Transaction.objects.create(
            user=self.user,
            category=self.category,
            description='Lunch',
            amount=25.50,
            type='expense',
            date=date.today()
        )
        Transaction.objects.create(
            user=self.user,
            category=self.category,
            description='Dinner',
            amount=35.00,
            type='expense',
            date=date.today()
        )
        
        response = self.client.get('/api/transactions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_get_transaction_detail(self):
        """Test getting a specific transaction"""
        transaction = Transaction.objects.create(
            user=self.user,
            category=self.category,
            description='Lunch',
            amount=25.50,
            type='expense',
            date=date.today()
        )
        response = self.client.get(f'/api/transactions/{transaction.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Lunch')
    
    def test_update_transaction(self):
        """Test updating a transaction"""
        transaction = Transaction.objects.create(
            user=self.user,
            category=self.category,
            description='Lunch',
            amount=25.50,
            type='expense',
            date=date.today()
        )
        data = {'description': 'Business Lunch', 'amount': 30.00}
        response = self.client.patch(f'/api/transactions/{transaction.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        transaction.refresh_from_db()
        self.assertEqual(transaction.description, 'Business Lunch')
    
    def test_delete_transaction(self):
        """Test deleting a transaction"""
        transaction = Transaction.objects.create(
            user=self.user,
            category=self.category,
            description='Lunch',
            amount=25.50,
            type='expense',
            date=date.today()
        )
        response = self.client.delete(f'/api/transactions/{transaction.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Transaction.objects.count(), 0)
    
    def test_user_can_only_see_own_transactions(self):
        """Test that users can only see their own transactions"""
        other_user = User.objects.create_user(
            username='other@example.com',
            email='other@example.com',
            password='pass123'
        )
        other_category = Category.objects.create(
            user=other_user,
            name='Food',
            type='expense'
        )
        Transaction.objects.create(
            user=other_user,
            category=other_category,
            description='Other Lunch',
            amount=20.00,
            type='expense',
            date=date.today()
        )
        Transaction.objects.create(
            user=self.user,
            category=self.category,
            description='My Lunch',
            amount=25.50,
            type='expense',
            date=date.today()
        )
        
        response = self.client.get('/api/transactions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['description'], 'My Lunch')


class DashboardAPITest(APITestCase):
    """Test cases for dashboard and analytics endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        # Create test data
        self.category_expense = Category.objects.create(
            user=self.user,
            name='Food',
            type='expense',
            budget=500.00
        )
        self.category_income = Category.objects.create(
            user=self.user,
            name='Salary',
            type='income'
        )
        
        # Create transactions
        Transaction.objects.create(
            user=self.user,
            category=self.category_expense,
            description='Lunch',
            amount=25.50,
            type='expense',
            date=date.today()
        )
        Transaction.objects.create(
            user=self.user,
            category=self.category_income,
            description='Monthly Salary',
            amount=3000.00,
            type='income',
            date=date.today()
        )
    
    def test_dashboard_summary(self):
        """Test dashboard summary endpoint"""
        response = self.client.get('/api/dashboard/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('summary', response.data)
        self.assertIn('total_income', response.data['summary'])
        self.assertIn('total_expenses', response.data['summary'])
        self.assertIn('balance', response.data['summary'])
        self.assertIn('chart', response.data)
        self.assertIn('recent_transactions', response.data)
    
    def test_analytics_overview(self):
        """Test analytics overview endpoint"""
        response = self.client.get('/api/analytics/overview/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Add assertions based on your analytics structure


class AuthenticationTest(APITestCase):
    """Test authentication requirements"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_categories_require_authentication(self):
        """Test that categories endpoint requires authentication"""
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_transactions_require_authentication(self):
        """Test that transactions endpoint requires authentication"""
        response = self.client.get('/api/transactions/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_profile_requires_authentication(self):
        """Test that profile endpoint requires authentication"""
        response = self.client.get('/api/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # end 
        