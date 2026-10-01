from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User,Group
from .models import Category, MenuItem
from django.urls import reverse
from django.core.cache import cache

# API TEST
class MenuItemTest (APITestCase):
    def setUp(self):
        self.manager_group = Group.objects.create(name='Manager')
        self.manager= User.objects.create_user(username='vane', password='little@van')
        self.manager.groups.add(self.manager_group)

        self.customer = User.objects.create_user(username='Tefa',password='little@tef')

        self.category =Category.objects.create(slug='main',title='main')
        self.item = MenuItem.objects.create(
            title='Hot dog',price='4.5',featured=True,category =self.category
        )

    def test_customer_cannot_menu_item(self):
        self.client.force_authenticate(user =self.customer)
        reponse = self.client.post('/api/menu-items/',{
            'title': 'Pasta', 'price': 8.00, 'featured': False, 'category_id': self.category.id
        })
        self.assertEqual(reponse.status_code,status.HTTP_403_FORBIDDEN
        )

    def test_manager_can_create_menu_item(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.post('/api/menu-items/', {
            'title': 'Pasta', 'price': 8.00, 'featured': False, 'category_id': self.category.id
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_anyone_can_list_menu_items(self):
        response = self.client.get('/api/menu-items/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

# Cart TEST

class CartAndOrderTest (APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username='male',password='little@mal')

        self.category =Category.objects.create(slug='main',title='main')
        self.item = MenuItem.objects.create(
            title='Hot dog',price='4.5',featured=True,category =self.category
        )
        # self.item = MenuItem.objects.create(
        #     title='Hamburger',price='7.2',featured=True,category =self.category
        # )

        self.client.force_authenticate(user = self.customer)

    def test_add_to_cart(self):
        response = self.client.post('/api/cart/menu-items/', {
            "menuitem_id": self.item.id,
            "quantity": 2
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_to_order(self):
        self.client.post('/api/cart/menu-items/', {
            "menuitem_id": self.item.id,
            "quantity": 2
        })

        response = self.client.post('/api/orders/', {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

# THROTTLING TEST

class ThrottlingTestCase(APITestCase):

    def setUp(self):
        cache.clear()

        self.user = User.objects.create_user(username='pautest',password='little@pau')
        self.url = '/api/menu-items/'

    def test_anonymus_user_throttling(self):
        response1 = self.client.get(self.url)    
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        response2 = self.client.get(self.url)    
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        response3 = self.client.get(self.url)    
        self.assertEqual(response3.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_authenticated_user_throttling(self):
        self.client.force_authenticate(user=self.user)

        for _ in range(10):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)