from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Cart, CartItem
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse


def home(request):
    return render(request, 'store/home.html', {"products": [
        {"name": "Phone", "price": "15550 ₽", "desc": "The best phone ever!", "stock": 1},
        {"name": "Tablet", "price": "25550 ₽", "desc": "The best tablet ever!", "stock": 0},
        {"name": "PC", "price": "55550 ₽", "desc": "The best PC ever! Check it out! Low price!", "stock": 0},
        {"name": "Monitor", "price": "23550 ₽", "desc": "The best screen ever!", "stock": 1}
    ]})

def products(request):
    products = list(Product.objects.all())
    cart_quantities = {}

    if request.user.is_authenticated:
        cart_quantities = dict(
            CartItem.objects
            .filter(cart__user=request.user)
            .values_list("product_id", "quantity")
        )

    for product in products:
        product.cart_quantity = cart_quantities.get(product.id, 0)

    return render(request,"store/products.html",{"products": products})

def product_page(request, id):
    product = get_object_or_404(Product, id=id)
    product.cart_quantity = 0

    if request.user.is_authenticated:
        product.cart_quantity = (
            CartItem.objects
            .filter(cart__user=request.user, product=product)
            .values_list("quantity", flat=True)
            .first() or 0
        )

    return render(request, 'store/product_page.html', {"product": product})

def register(request):

    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserCreationForm()
    return render(request, 'registration/registration.html', {"form": form})

@login_required
@require_POST
def update_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    action = request.POST.get("action")

    if action not in {"add", "increase", "decrease", "set"}:
        return JsonResponse({"error": "Invalid action"}, status=400)

    cart, _ = Cart.objects.get_or_create(user=request.user)

    cart_item = CartItem.objects.filter(
        cart=cart,
        product=product
    ).first()

    quantity = cart_item.quantity if cart_item else 0

    if action == "add":
        if quantity == 0 and product.stock > 0:
            quantity = 1

    elif action == "increase":
        if quantity < product.stock:
            quantity += 1

    elif action == "decrease":
        quantity = max(0, quantity - 1)

    elif action == "set":
        try:
            quantity = int(request.POST.get("quantity", ""))
        except ValueError:
            return JsonResponse({"error": "Invalid quantity"}, status=400)

        quantity = max(0, min(quantity, product.stock))

    if quantity == 0:
        if cart_item:
            cart_item.delete()
    elif cart_item:
        cart_item.quantity = quantity
        cart_item.save(update_fields=["quantity"])
    else:
        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=quantity
        )

    return JsonResponse({
        "quantity": quantity,
        "stock": product.stock
    })

@login_required
def cart(request):
    cart = request.user.cart
    cart_items = CartItem.objects.filter(cart=cart)
    quantity_of_items = 0
    total = 0
    for item in cart_items:
        quantity_of_items += item.quantity
        item.line_total = item.product.price * item.quantity
        total += item.line_total
    discount = total * Decimal("0.10")
    final_total = total - discount
    return render(request, "store/cart.html", {
        "cart_items": cart_items,
        "quantity_of_items": quantity_of_items,
        "total": total, "discount": discount,
        "final_total": final_total
    })
