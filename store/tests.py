from django.test import TestCase
from django.urls import reverse

from .models import Product, CartItem, Cart
from django.contrib.auth import get_user_model

# Create your tests here.
class ProductTest(TestCase):

    def setUp(self):
         self.product = Product.objects.create(name="Product Test", price=100, description="Test Description", stock=5)

    def test_product_str(self):
        self.assertEqual(str(self.product), "Product Test")

User = get_user_model()

class CartTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.product = Product.objects.create(name="Product Test", price=100, description="Test Description", stock=5)

    def test_add_product_to_cart(self):
        self.client.login(username="testuser", password="testpassword")
        url = reverse("update_cart", args=[self.product.id])
        response_add = self.client.post(url, data={"action": "add"})
        self.assertEqual(response_add.status_code, 200)
        self.assertEqual(response_add.json()['quantity'], 1)
        cart = Cart.objects.get(user=self.user)
        self.assertTrue(CartItem.objects.filter(cart=cart, product=self.product).exists())

    def test_increase_product_quantity(self):
        self.client.login(username="testuser", password="testpassword")
        url = reverse("update_cart", args=[self.product.id])
        self.client.post(url, data={"action": "add"})
        response_increase = self.client.post(url, data={"action": "increase"})
        self.assertEqual(response_increase.status_code, 200)
        self.assertEqual(response_increase.json()['quantity'], 2)
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(CartItem.objects.get(cart=cart, product=self.product).quantity, 2)

    def test_decrease_product_quantity(self):
        self.client.login(username="testuser", password="testpassword")
        url = reverse("update_cart", args=[self.product.id])
        self.client.post(url, data={"action": "add"})
        response_increase = self.client.post(url, data={"action": "increase"})
        self.assertEqual(response_increase.status_code, 200)
        self.assertEqual(response_increase.json()['quantity'], 2)
        response_decrease = self.client.post(url, data={"action": "decrease"})
        self.assertEqual(response_decrease.status_code, 200)
        self.assertEqual(response_decrease.json()['quantity'], 1)
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(CartItem.objects.get(cart=cart, product=self.product).quantity, 1)

    def test_decrease_to_zero(self):
        self.client.login(username="testuser", password="testpassword")
        url = reverse("update_cart", args=[self.product.id])
        response_add = self.client.post(url, data={"action": "add"})
        self.assertEqual(response_add.status_code, 200)
        self.assertEqual(response_add.json()['quantity'], 1)
        response_decrease = self.client.post(url, data={"action": "decrease"})
        self.assertEqual(response_decrease.status_code, 200)
        self.assertEqual(response_decrease.json()['quantity'], 0)
        cart = Cart.objects.get(user=self.user)
        self.assertFalse(CartItem.objects.filter(cart=cart, product=self.product).exists())

    def test_increase_quantity_cannot_exceed_stock(self):
        self.client.login(username="testuser", password="testpassword")
        url = reverse("update_cart", args=[self.product.id])
        response_add = self.client.post(url, data={"action": "add"})
        self.assertEqual(response_add.status_code, 200)
        self.assertEqual(response_add.json()['quantity'], 1)
        for i in range(1, 5):
            response_increase = self.client.post(url, data={"action": "increase"})
            self.assertEqual(response_increase.status_code, 200)
        self.assertEqual(response_increase.json()['quantity'], 5)
        response_increase = self.client.post(url, data={"action": "increase"})
        self.assertEqual(response_increase.status_code, 200)
        self.assertEqual(response_increase.json()['quantity'], 5)
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(CartItem.objects.get(cart=cart, product=self.product).quantity, 5)

    def test_invalid_action(self):
        self.client.login(username="testuser", password="testpassword")
        url = reverse("update_cart", args=[self.product.id])
        response = self.client.post(url, data={"action": "invalid"})
        self.assertEqual(response.status_code, 400)

    def test_set_quantity(self):
        self.client.login(username="testuser", password="testpassword")
        url = reverse("update_cart", args=[self.product.id])
        response = self.client.post(url, data={"action": "set", "quantity": 4})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['quantity'], 4)
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(CartItem.objects.get(cart=cart, product=self.product).quantity, 4)

    def test_unauthenticated_user_cannot_update_cart(self):
        url = reverse("update_cart", args=[self.product.id])
        response = self.client.post(url, data={"action": "add"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Cart.objects.filter(user=self.user).exists())
        self.assertFalse(CartItem.objects.filter(product=self.product).exists())