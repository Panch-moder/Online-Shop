from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    description = models.TextField()
    stock = models.IntegerField()

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products')

class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    review = models.TextField()
    rate = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "product"], name="unique_review")]

    def __str__(self):
        return f"Review №{self.id}"

class Cart(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='cart')

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    class Meta:
        unique_together = (('cart', 'product'),)

class Order(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
    )
    time_created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        choices=[
            ("new", "New"), ("processing", "Processing"),
            ("packed", "Packed"), ("shipped", "Shipped"),
            ("completed", "Completed"), ("cancelled", "Cancelled")
        ],
        default="new",
        max_length=50
    )

    def get_total(self):
        total = 0
        for item in self.orderitem_set.all():
            total += item.quantity * item.price
        return total

    def __str__(self):
        return f"Order №{self.id}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    product_name = models.CharField(max_length=100)
    price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product_name} — {self.quantity}"