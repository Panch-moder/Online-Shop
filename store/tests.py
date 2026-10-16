from django.test import TestCase
from .models import Product

# Create your tests here.
class ProductTest(TestCase):

    def setUp(self):
         self.product = Product.objects.create(name="Product Test", price=100, description="Test Description", stock=5)

    def test_product_str(self):
        self.assertEqual(str(self.product), "Product Test")