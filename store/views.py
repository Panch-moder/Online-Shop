from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Cart, CartItem, Order, OrderItem
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse


def home(request):
    return render(request, 'store/home.html', {"products": [
        {"name": "Phone", "price": "15550 ₽", "desc": "The best phone ever!", "stock": 1},
        {"name": "Tablet", "price": "25550 ₽", "desc": "The best tablet ever!", "stock": 0},
        {"name": "PC", "price": "55550 ₽", "desc": "The best PC ever! Check it out! Low price!", "stock": 0},
        {"name": "Monitor", "price": "23550 ₽", "desc": "The best screen ever!", "stock": 1}
    ]})

def products(request):
    cart_quantities = {}

    try:
        products = Product.objects.all()
        max_price = request.GET.get("max_price")
        min_price = request.GET.get("min_price")
        allowed_sort_options = {"price", "-price", "name", "-name"}
        sort = request.GET.get("sort")

        if max_price is not None and max_price.isdigit():
            max_price = int(max_price)
        elif max_price is not None:
            messages.warning(request, "Please enter a valid MAX numeric parameter")
            max_price = None

        if min_price is not None and min_price.isdigit():
            min_price = int(min_price)
        elif min_price is not None:
            messages.warning(request, "Please enter a valid MIN numeric parameter")
            min_price = None

        if max_price is not None and min_price is not None and min_price > max_price:
            messages.warning(request, "MIN price can't be greater than MAX")
        else:
            if max_price is not None:
                products = products.filter(price__lte=max_price)
            if min_price is not None:
                products = products.filter(price__gte=min_price)

        if sort in allowed_sort_options:
            products = products.order_by(sort)

    except (ValueError, TypeError):
        messages.warning(request, "Please enter a valid numeric parameter")
        products = Product.objects.all()

    products = products.filter(stock__gt=0)

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

@login_required
@require_POST
def checkout(request):
    cart = request.user.cart
    cart_items = CartItem.objects.filter(cart=cart)
    has_stock_issues = False
    issue_items_list = []

    if not cart_items.exists():
        return redirect("cart")

    with transaction.atomic():

        for item in cart_items:
            if item.quantity > item.product.stock:
                has_stock_issues = True
                issue_items_list.append(
                    {"name": item.product.name,
                     "quantity": item.quantity,
                     "stock": item.product.stock}
                )

        if has_stock_issues:
            for item in issue_items_list:
                messages.warning(
                    request,
                    message=(
                        f"We have only {item['stock']} {item['name']} in stock, "
                        f"but you've selected {item['quantity']}. "
                        f"Please reduce the quantity to continue."
                    )
                )
            return redirect("cart")

        order = Order.objects.create(user=request.user)
        for item in cart_items:
            OrderItem.objects.create(
                order=order, product=item.product,
                product_name=item.product.name, price=item.product.price,
                quantity=item.quantity
            )
            item.product.stock -= item.quantity
            item.product.save()
        cart_items.delete()
        messages.success(request, message=f"Order {order.id} has been placed successfully!")
    return redirect("cart")

@login_required
def show_orders(request):
    user = request.user
    total = 0
    orders = Order.objects.filter(user=user)
    for order in orders:
        total += order.get_total()
    return render(request, "store/user_orders.html", {"orders": orders, "total": total})





