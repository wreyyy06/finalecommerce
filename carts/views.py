from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Variation
from .models import Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def add_cart(request, product_id):
    current_user = request.user
    product = Product.objects.get(id=product_id)
    # If user is authenticated

    if current_user.is_authenticated:
        product_variation = []

        if request.method == "POST":
            for key, value in request.POST.items():
                if value:  # Ensure empty selections are ignored
                    try:
                        variation = Variation.objects.get(
                            product=product, variation_category__iexact=key, variation_value__iexact=value
                        )
                        product_variation.append(variation)
                    except Variation.DoesNotExist:
                        pass 

        is_cart_item_exists = CartItem.objects.filter(product=product, user=current_user).exists()
        if is_cart_item_exists:
            cart_items = CartItem.objects.filter(product=product, user=current_user)
            
            ex_var_list = []
            id_list = []
            for item in cart_items:
                existing_variation = list(item.variations.all())
                ex_var_list.append(existing_variation)
                id_list.append(item.id)

            if product_variation in ex_var_list:
                index = ex_var_list.index(product_variation)
                item_id = id_list[index]
                item = CartItem.objects.get(id=item_id)
                item.quantity += 1
                item.save()
            else:
                item = CartItem.objects.create(product=product, quantity=1, user=current_user)
                if product_variation:
                    item.variations.set(product_variation)
                item.save()
        else:
            cart_item = CartItem.objects.create(product=product, quantity=1, user=current_user)
            if product_variation:
                cart_item.variations.set(product_variation)
            cart_item.save()
        
        return redirect('cart')

    else:
        product_variation = []

        if request.method == "POST":
            for key, value in request.POST.items():
                if value:  # Ensure empty selections are ignored
                    try:
                        variation = Variation.objects.get(
                            product=product, variation_category__iexact=key, variation_value__iexact=value
                        )
                        product_variation.append(variation)
                    except Variation.DoesNotExist:
                        pass  

        # Proceed to add to cart if all required variations are selected
        cart, created = Cart.objects.get_or_create(cart_id=_cart_id(request))

        is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()
        if is_cart_item_exists:
            cart_items = CartItem.objects.filter(product=product, cart=cart)
            
            ex_var_list = []
            id_list = []
            for item in cart_items:
                existing_variation = list(item.variations.all())
                ex_var_list.append(existing_variation)
                id_list.append(item.id)

            if product_variation in ex_var_list:
                index = ex_var_list.index(product_variation)
                item_id = id_list[index]
                item = CartItem.objects.get(id=item_id)
                item.quantity += 1
                item.save()
            else:
                item = CartItem.objects.create(product=product, quantity=1, cart=cart)
                if product_variation:
                    item.variations.set(product_variation)
                item.save()
        else:
            cart_item = CartItem.objects.create(product=product, quantity=1, cart=cart)
            if product_variation:
                cart_item.variations.set(product_variation)
            cart_item.save()
        
        return redirect('cart')


def remove_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    product_variation = []
    if request.method == "POST":
        for key, value in request.POST.items():
            try:
                variation = Variation.objects.get(
                    product=product, variation_category__iexact=key, variation_value__iexact=value
                )
                product_variation.append(variation)
            except:
                pass

    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(product=product, user=request.user)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(product=product, cart=cart)

    for cart_item in cart_items:
        existing_variations = list(cart_item.variations.all())
        if existing_variations == product_variation or not product_variation:
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
            break  

    return redirect('cart')



def remove_cart_item(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    product_variation = []
    if request.method == "POST":
        for key, value in request.POST.items():
            try:
                variation = Variation.objects.get(
                    product=product, variation_category__iexact=key, variation_value__iexact=value
                )
                product_variation.append(variation)
            except:
                pass

    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(product=product, user=request.user)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(product=product, cart=cart)

    for cart_item in cart_items:
        existing_variations = list(cart_item.variations.all())
        if existing_variations == product_variation:
            cart_item.delete()
            return redirect('cart')

    return redirect('cart')



def cart(request, total=0, quantity=0, cart_items=None):
    try:
        shipping = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += cart_item.product.price * cart_item.quantity
            quantity += cart_item.quantity

        shipping = (20 * total) / 100
        grand_total = total + shipping
    except ObjectDoesNotExist:
        cart_items = []
        shipping = 0
        grand_total = 0

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'shipping': shipping,
        'grand_total': grand_total,
    }
    return render(request, 'store/cart.html', context)

@login_required(login_url='login')
def checkout(request,  total=0, quantity=0, cart_items=None):
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += cart_item.product.price * cart_item.quantity
            quantity += cart_item.quantity

        shipping = (20 * total) / 100
        grand_total = total + shipping
    except ObjectDoesNotExist:
        cart_items = []
        shipping = 0
        grand_total = 0

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'shipping': shipping,
        'grand_total': grand_total,
    }
    return render(request, 'store/checkout.html', context)