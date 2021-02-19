"""
Restaurantes a domicilio
Oferta de menus
~~~~ Gestion de Imagenes ~~~~ -> Cloudinary 
Usuario
Restaurante -> Menu <-> Pedido <- Usuario
Resturante crea menus
Usuario crea pedididos con menu
Resturante puede ver estado de un pedido

Rutas Usuario:
login
logup
idx (Ver todos los restaurantes)
orders/ order/create

Rutas Restaurant:
login
logup
idx (Ver todas las ordenes a mis menus)
menus/ menus/create menus/edit/:id menus/delete/:id

set MONGO_URI=mongodb://localhost:27017/telemenu
set SECRET=cambiar
... set PRODUCTION=True


"""

from models import Menu, Order, Restaurant, User
import datetime
import functools
import os

import bcrypt
import cloudinary
import cloudinary.api
import cloudinary.uploader
import pymongo.errors
from bson.objectid import ObjectId
from flask import Flask, redirect, request, session
from flask.templating import render_template
from pymodm.errors import ValidationError

cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_CLOUD_SECRET')
)


SECRET_KEY = os.environ.get('SECRET')
PROD = bool(os.environ.get('PRODUCTION', False))
app = Flask(__name__)
app.secret_key = SECRET_KEY


def format_date(value, format="%B %d"):
    return value.strftime(format)


app.jinja_env.filters['format_date'] = format_date


def user_logged_in(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            return redirect('/user/login')
        return func(*args, **kwargs)
    return wrapper


def restaurant_logged_in(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if 'restaurant' not in session:
            return redirect('/restaurant/login/')
        return func(*args, **kwargs)
    return wrapper


@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == "GET":
        return render_template('user/login.html')
    else:
        try:
            email, password = request.form['email'], request.form['password']
            user = User.objects.get({'_id': email})
            if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                session.pop('restaurant', None)
                session['user'] = user.email
                return redirect('/')
            else:
                return render_template('user/login.html', wrong_pass=True)
        except User.DoesNotExist:
            return render_template('user/login.html', no_user=True)


@app.route('/user/logup', methods=['GET', 'POST'])
def user_logup():
    if request.method == "GET":
        return render_template('user/logup.html')
    else:
        try:
            password = request.form['password']
            password = bcrypt.hashpw(
                password.encode('utf-8'), bcrypt.gensalt())
            User(email=request.form['email'], full_name=request.form['full_name'], password=password.decode('utf-8')).save(
                force_insert=True)
        except ValidationError as ve:
            return render_template('user/logup.html', email_error="Formato de correo Incorrecto")
        except pymongo.errors.DuplicateKeyError:
            return render_template('user/logup.html', email_error="Ya existe un usuario con ese correo")
    return redirect('/user/login')


@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('restaurant', None)
    return redirect('/')


@app.route('/orders')
def orders():
    pass  # -> noop


@app.route('/orders/<id>')
def order():
    pass  # -> noop


@app.route('/orders/create')
def order_create():
    pass  # -> noo


@app.route('/restaurant/login', methods=['GET', 'POST'])
def restaurant_login():
    if request.method == "GET":
        return render_template('restaurant/login.html')
    else:
        try:
            email, password = request.form['email'], request.form['password']
            restaurant = Restaurant.objects.get({'_id': email})
            if bcrypt.checkpw(password.encode('utf-8'), restaurant.password.encode('utf-8')):
                session.pop('user', None)
                session['restaurant'] = restaurant.email
                return redirect('/')
            else:
                return render_template('restaurant/login.html', wrong_pass=True)
        except Restaurant.DoesNotExist:
            return render_template('restaurant/login.html', no_restaurant=True)


@app.route('/restaurant/logup', methods=['GET', 'POST'])
def restaurant_logup():
    if request.method == "GET":
        return render_template('restaurant/logup.html')
    else:
        try:
            password = request.form['password']
            password = bcrypt.hashpw(
                password.encode('utf-8'), bcrypt.gensalt())
            Restaurant(email=request.form['email'], name=request.form['restaurant_name'], password=password.decode('utf-8')).save(
                force_insert=True)
        except ValidationError as ve:
            return render_template('restaurant/logup.html', email_error="Formato de correo Incorrecto")
        except pymongo.errors.DuplicateKeyError:
            return render_template('restaurant/logup.html', email_error="Ya existe un restaurante con ese correo")
    return redirect('/restaurant/login')


@app.route('/menus')
@restaurant_logged_in
def menus():
    return render_template('menus/index.html', menus=Restaurant.objects.only('menus').get(
        {'_id': session['restaurant']}).menus)


@app.route('/menus/create', methods=['GET', 'POST'])
@restaurant_logged_in
def menus_create():
    if request.method == "GET":
        return render_template('menus/create.html')
    else:
        restaurant = Restaurant.objects.get({'_id': session['restaurant']})
        try:
            composition = request.form['composition']
            price = float(request.form['price'])
            valid_date = datetime.datetime.strptime(
                request.form['valid_date'], '%Y-%m-%d')
            photo = request.files['photo']
            photo_url = cloudinary.uploader.upload_image(photo).build_url()
            menu = Menu(ObjectId(), composition, price, valid_date, photo_url)
            restaurant.menus.append(menu)
            restaurant.save()
        except Exception as e:
            print(e)
            restaurant.menus.pop()
            return render_template('menus/create.html', error=True)
        return render_template('menus/index.html')


@app.route('/')
def index():
    orders = []
    if 'restaurant' in session:
        menus = Restaurant.objects.only('menus').get(
            {'_id': session['restaurant']}).menus
        menus_ids = [menu._id for menu in menus]
        for id in menus_ids:
            sub_orders = Order.objects.get_queryset().raw({'menu': id})
            orders.extend(sub_orders)
    print(orders)
    return render_template('index.html', restaurants=Restaurant.objects.all(), orders=orders)


def main():
    app.run(debug=True)


if __name__ == "__main__":
    main()
