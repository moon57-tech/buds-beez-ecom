from flask import session, request, redirect, url_for, flash, render_template, abort
from flask_login import login_required, current_user
from app import app, db, Product, Category, Order, OrderItem, User
from forms import CheckoutForm
from datetime import datetime
import uuid
import os


def get_cart():
    if 'cart' not in session:
        session['cart'] = []
    return session['cart']


def clear_cart():
    session.pop('cart', None)
