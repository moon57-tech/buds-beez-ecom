from flask import Flask, render_template, redirect, url_for, flash, request, session, abort, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import uuid
import json
from dotenv import load_dotenv

from extensions import db, login_manager
from models import User, Category, Product, Order, OrderItem
from forms import RegistrationForm, LoginForm, ProductForm, CategoryForm, CheckoutForm
from cart import get_cart, add_to_cart, remove_from_cart, update_cart, clear_cart, cart_total, cart_count

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///budsbeez.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.context_processor
def inject_cart_count():
    return dict(cart_count=cart_count())


def generate_order_number():
    return f"BB-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"


def get_payfast_url(order, base_url):
    merchant_id = os.environ.get('PAYFAST_MERCHANT_ID', '30676571')
    merchant_key = os.environ.get('PAYFAST_MERCHANT_KEY', '')
    passphrase = os.environ.get('PAYFAST_PASSPHRASE', '')
    test_mode = os.environ.get('PAYFAST_TEST_MODE', 'True').lower() == 'true'
    
    payfast_url = 'https://payment.payfast.io/eng/process' if not test_mode else 'https://sandbox.payfast.co.za/eng/process'
    
    item_name = f"Order {order.order_number}"
    item_description = f"Purchase from Buds & Beez - {len(order.items)} items"
    amount = f"{order.total_amount:.2f}"
    
    return_url = os.environ.get('PAYFAST_RETURN_URL', f'{base_url}/payfast/return')
    cancel_url = os.environ.get('PAYFAST_CANCEL_URL', f'{base_url}/payfast/cancel')
    notify_url = os.environ.get('PAYFAST_NOTIFY_URL', f'{base_url}/payfast/notify')
    
    data = {
        'cmd': '_paynow',
        'receiver': merchant_id,
        'amount': amount,
        'item_name': item_name,
        'item_description': item_description,
        'return_url': return_url,
        'cancel_url': cancel_url,
        'notify_url': notify_url,
    }
    
    return payfast_url, data


@app.route('/')
def home():
    products = Product.query.filter_by(is_active=True).order_by(Product.created_at.desc()).limit(8).all()
    return render_template('home.html', products=products)


@app.route('/shop')
def shop():
    category_id = request.args.get('category')
    page = request.args.get('page', 1, type=int)
    per_page = 12
    query = Product.query.filter_by(is_active=True)
    if category_id:
        query = query.filter_by(category_id=category_id)
    products = query.order_by(Product.name).paginate(page=page, per_page=per_page, error_out=False)
    categories = Category.query.all()
    return render_template('shop.html', products=products, categories=categories, selected_category=category_id)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)



@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            phone=form.phone.data,
            password_hash=generate_password_hash(form.password.data),
            is_admin=False
        )
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('auth/register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.is_active and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check username and password.', 'danger')
    return render_template('auth/login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))



@app.route('/cart')
def cart():
    cart = get_cart()
    cart_products = []
    for item in cart:
        product = Product.query.get(item['product_id'])
        if product:
            cart_products.append((item, product))
    total = cart_total(cart_products)
    return render_template('cart.html', cart_products=cart_products, total=total)


@app.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart_route(product_id):
    product = Product.query.get_or_404(product_id)
    if product.stock_quantity < 1:
        flash('Product is out of stock!', 'danger')
        return redirect(url_for('product_detail', product_id=product_id))
    quantity = int(request.form.get('quantity', 1))
    if quantity > product.stock_quantity:
        quantity = product.stock_quantity
    add_to_cart(product_id, quantity)
    flash('Product added to cart!', 'success')
    return redirect(url_for('cart'))


@app.route('/cart/remove/<int:product_id>')
def remove_from_cart_route(product_id):
    remove_from_cart(product_id)
    flash('Product removed from cart!', 'info')
    return redirect(url_for('cart'))


@app.route('/cart/update/<int:product_id>', methods=['POST'])
def update_cart_route(product_id):
    quantity = int(request.form.get('quantity', 1))
    product = Product.query.get_or_404(product_id)
    if quantity < 1:
        quantity = 1
    if quantity > product.stock_quantity:
        quantity = product.stock_quantity
        flash(f'Only {product.stock_quantity} items available in stock.', 'warning')
    update_cart(product_id, quantity)
    return redirect(url_for('cart'))



@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart = get_cart()
    if not cart:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('shop'))
    cart_products = []
    for item in cart:
        product = Product.query.get(item['product_id'])
        if product:
            cart_products.append((item, product))
    total = cart_total(cart_products)
    form = CheckoutForm()
    if form.validate_on_submit():
        order = Order(
            order_number=generate_order_number(),
            user_id=current_user.id,
            status='pending',
            payment_status='pending',
            total_amount=total,
            shipping_address=form.shipping_address.data,
            notes=form.notes.data
        )
        db.session.add(order)
        db.session.commit()
        for item, product in cart_products:
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item['quantity'],
                price=product.price
            )
            db.session.add(order_item)
        db.session.commit()
        return redirect(url_for('payment', order_id=order.id))
    return render_template('checkout.html', form=form, cart_products=cart_products, total=total)


@app.route('/orders/my')
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders/my_orders.html', orders=orders)


@app.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    return render_template('orders/order_detail.html', order=order)



@app.route('/payment/<int:order_id>')
@login_required
def payment(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        abort(403)
    if order.payment_status == 'paid':
        flash('This order has already been paid.', 'info')
        return redirect(url_for('order_detail', order_id=order.id))
    base_url = os.environ.get('SITE_URL', request.url_root.rstrip('/'))
    payfast_url, payfast_data = get_payfast_url(order, base_url)
    return render_template('payment.html', order=order, payfast_url=payfast_url, payfast_data=payfast_data)


@app.route('/payfast/return')
def payfast_return():
    flash('Payment completed. Please wait for confirmation.', 'success')
    return redirect(url_for('my_orders'))


@app.route('/payfast/cancel')
def payfast_cancel():
    flash('Payment was cancelled.', 'warning')
    return redirect(url_for('my_orders'))


@app.route('/payfast/notify', methods=['POST'])
def payfast_notify():
    order_number = request.form.get('item_name', '').replace('Order ', '')
    order = Order.query.filter_by(order_number=order_number).first()
    if order:
        order.payment_status = 'paid'
        order.status = 'processing'
        db.session.commit()
    return 'OK', 200



@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        abort(403)
    total_users = User.query.count()
    total_products = Product.query.count()
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='pending').count()
    return render_template('admin/dashboard.html', total_users=total_users, total_products=total_products, total_orders=total_orders, pending_orders=pending_orders)


@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        abort(403)
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@app.route('/admin/users/toggle/<int:user_id>')
@login_required
def admin_toggle_user(user_id):
    if not current_user.is_admin:
        abort(403)
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'User {user.username} status updated.', 'info')
    return redirect(url_for('admin_users'))


@app.route('/admin/users/make-admin/<int:user_id>')
@login_required
def admin_make_admin(user_id):
    if not current_user.is_admin:
        abort(403)
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    flash(f'User {user.username} admin status updated.', 'info')
    return redirect(url_for('admin_users'))



@app.route('/admin/products')
@login_required
def admin_products():
    if not current_user.is_admin:
        abort(403)
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('admin/products.html', products=products)


@app.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
def admin_add_product():
    if not current_user.is_admin:
        abort(403)
    form = ProductForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            stock_quantity=form.stock_quantity.data,
            category_id=form.category_id.data,
            image_url=form.image_url.data,
            is_active=form.is_active.data
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/product_form.html', form=form, title='Add Product')


@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_product(product_id):
    if not current_user.is_admin:
        abort(403)
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.stock_quantity = form.stock_quantity.data
        product.category_id = form.category_id.data
        product.image_url = form.image_url.data
        product.is_active = form.is_active.data
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/product_form.html', form=form, title='Edit Product')


@app.context_processor
def inject_globals():
    from datetime import datetime
    return dict(datetime=datetime)



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

