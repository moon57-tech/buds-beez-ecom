from flask import session


def get_cart():
    if 'cart' not in session:
        session['cart'] = []
    return session['cart']


def add_to_cart(product_id, quantity=1):
    cart = get_cart()
    for item in cart:
        if item['product_id'] == product_id:
            item['quantity'] += quantity
            break
    else:
        cart.append({'product_id': product_id, 'quantity': quantity})
    session['cart'] = cart


def remove_from_cart(product_id):
    cart = get_cart()
    session['cart'] = [item for item in cart if item['product_id'] != product_id]


def update_cart(product_id, quantity):
    cart = get_cart()
    for item in cart:
        if item['product_id'] == product_id:
            item['quantity'] = quantity
            break
    session['cart'] = cart


def clear_cart():
    session.pop('cart', None)


def cart_total(products_data):
    total = 0
    for item, product in products_data:
        total += product.price * item['quantity']
    return total


def cart_count():
    cart = get_cart()
    return sum(item['quantity'] for item in cart)
