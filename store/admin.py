from django.contrib import admin
from django import forms
from django.db import models
from django.urls import reverse
from django.utils.html import format_html

from .models import Product, ProductImage, ProductReview, Order, OrderItem

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 2

class ProductReviewInline(admin.StackedInline):
    model = ProductReview
    extra = 0
    fields = (("user", "date", "rate"), "review")
    readonly_fields = ("user", "date")
    formfield_overrides = {
        models.TextField: {
            "widget": forms.Textarea(attrs={"rows": 2})
        },
    }

class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline, ProductReviewInline]

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ("product", "product_name", "price", "quantity")

    def has_add_permission(self, request, obj=None):
        return False

class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]
    list_display = ('id', 'user', 'time_created', 'status', 'open_order')
    list_filter = ('time_created', 'status')

    def open_order(self, obj):
        url = reverse("admin:store_order_change", args=(obj.id,))
        return format_html('<a href="{}">Open Order</a>', url)

# Register your models here.
admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
