from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Product, CartItem, Cart, ProductReview
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

class ProductFilterTests(TestCase):

    def setUp(self):
        self.product1 = Product.objects.create(name="TestProduct1", price=10, stock=1)
        self.product2 = Product.objects.create(name="TestProduct2", price=100, stock=2)
        self.user = User.objects.create_user(username="testuser", password="testpassword")

    def test_max_price_filter(self):
        response = self.client.get(reverse("products"), {"max_price": 50})
        self.assertEqual(response.status_code, 200)
        products = response.context["products"]
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].name, 'TestProduct1')

    def test_min_price_filter(self):
        response = self.client.get(reverse("products"), {"min_price": 50})
        self.assertEqual(response.status_code, 200)
        products = response.context["products"]
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].name, 'TestProduct2')

    def test_min_and_max_price_filter(self):
        response = self.client.get(reverse("products"), {"min_price": 20, "max_price": 150})
        self.assertEqual(response.status_code, 200)
        products = response.context["products"]
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].name, 'TestProduct2')

    def test_sortASC_price_filter(self):
        response = self.client.get(reverse("products"), {"sort": "price"})
        self.assertEqual(response.status_code, 200)
        products = response.context["products"]
        self.assertEqual(len(products), 2)
        self.assertEqual(products[0].name, 'TestProduct1')
        self.assertEqual(products[1].name, 'TestProduct2')

    def test_sortDESC_price_filter(self):
        response = self.client.get(reverse("products"), {"sort": "-price"})
        self.assertEqual(response.status_code, 200)
        products = response.context["products"]
        self.assertEqual(len(products), 2)
        self.assertEqual(products[0].name, 'TestProduct2')
        self.assertEqual(products[1].name, 'TestProduct1')

    def test_sortASC_name_filter(self):
        response = self.client.get(reverse("products"), {"sort": "name"})
        self.assertEqual(response.status_code, 200)
        products = response.context["products"]
        self.assertEqual(len(products), 2)
        self.assertEqual(products[0].name, 'TestProduct1')
        self.assertEqual(products[1].name, 'TestProduct2')

    def test_sortDESC_name_filter(self):
        response = self.client.get(reverse("products"), {"sort": "-name"})
        self.assertEqual(response.status_code, 200)
        products = response.context["products"]
        self.assertEqual(len(products), 2)
        self.assertEqual(products[0].name, 'TestProduct2')
        self.assertEqual(products[1].name, 'TestProduct1')

    def test_invalid_max_price_option(self):
        response = self.client.get(reverse("products"), {"max_price": "abc"})
        self.assertEqual(response.status_code, 200)
        products = response.context["products"]
        self.assertEqual(len(products), 2)
        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertEqual(messages, ["Please enter a valid MAX numeric parameter"])

    def test_price_equal_to_min_and_max(self):
        response = self.client.get(reverse("products"), {"min_price": 100, "max_price": 100})
        self.assertEqual(response.status_code, 200)
        products = response.context["products"]
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].name, 'TestProduct2')

    def test_max_less_than_min_price(self):
        response = self.client.get(reverse("products"), {"min_price": 150, "max_price": 50})
        self.assertEqual(response.status_code, 200)
        products = response.context["products"]
        self.assertEqual(len(products), 2)

    def test_min_price_is_invalid_and_max_price_correct(self):
        response = self.client.get(reverse("products"), {"min_price": "abc", "max_price": 50})
        self.assertEqual(response.status_code, 200)
        products = response.context["products"]
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].name, 'TestProduct1')

    def test_both_min_and_max_price_are_invalid(self):
        response = self.client.get(reverse("products"), {"min_price": "abc", "max_price": "abc"})
        self.assertEqual(response.status_code, 200)
        products = response.context["products"]
        self.assertEqual(len(products), 2)
        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertEqual(messages, ["Please enter a valid MAX numeric parameter", "Please enter a valid MIN numeric parameter"])

class ProductReviewTests(TestCase):

    def setUp(self):
        self.product = Product.objects.create(name="TestProduct1", price=10, stock=1)
        self.user = User.objects.create_user(username="testuser", password="testpassword")

    def test_normal_min_max_rate(self):
        self.productReview = ProductReview.objects.create(product=self.product, user=self.user, review="test", rate=1)
        self.productReview.full_clean()
        self.productReview.rate = 1
        self.productReview.full_clean()
        self.productReview.rate = 0
        with self.assertRaises(ValidationError):
            self.productReview.full_clean()
        self.productReview.rate = 6
        with self.assertRaises(ValidationError):
            self.productReview.full_clean()

    def test_unique_review(self):
        self.productReview1 = ProductReview.objects.create(product=self.product, user=self.user, review="test", rate=1)
        self.productReview1.full_clean()
        self.productReview2 = ProductReview(product=self.product, user=self.user, review="test2", rate=5)
        with self.assertRaises(ValidationError):
            self.productReview2.full_clean()
