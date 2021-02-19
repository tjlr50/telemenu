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

from models import Menu, Opinion, Order, Restaurant, User
import datetime
import functools
import os

import bcrypt
import cloudinary
import cloudinary.api
import cloudinary.uploader
import pymongo
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


def calculate_menu_score(menu: Menu) -> float:
    c = 0
    for opinion in menu.opinions:
        c += opinion.score
    return c/(len(menu.opinions) if len(menu.opinions) > 0 else 1)


app.jinja_env.filters['calculate_menu_score'] = calculate_menu_score


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
            return redirect('/restaurant/login')
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
@user_logged_in
def orders():
    orders = list(Order.objects.get_queryset().order_by(
        [('created_at', pymongo.DESCENDING)]).raw({'user': session['user']}))
    for order in orders:
        restaurant_menu = [menu for menu in
                           order.restaurant.menus if menu._id == order.menu_id]
        restaurant_menu = restaurant_menu[0] if restaurant_menu else None
        order.menu = restaurant_menu
    return render_template('orders/index.html', orders=orders)


@app.route('/orders/create/<restaurant_id>/<menu_id>', methods=['GET', 'POST'])
@user_logged_in
def order_create(restaurant_id, menu_id):
    restaurant = Restaurant.objects.get({'_id': restaurant_id})
    menu = [menu for menu in
            restaurant.menus if menu._id == ObjectId(menu_id)]
    menu = menu[0] if menu else None
    if menu.valid_date >= datetime.datetime.now():
        menu = None
    if request.method == "GET":
        return render_template('orders/create.html', menu=menu)
    else:
        try:
            if menu:
                Order(ObjectId(), datetime.datetime.now(), restaurant.email,
                      session['user'], menu._id, "Preparación").save()
            else:
                return render_template('orders/create.html', menu=None)
        except Exception as e:
            print(e)
            return render_template('orders/create.html', menu=menu, error=True)
        return redirect('/orders')


@app.route('/orders/setdone/<order_id>', methods=["GET", "POST"])
@restaurant_logged_in
def order_setdone(order_id):
    if request.method == "GET":
        return redirect('/')
    else:
        orders = list(Order.objects.get_queryset().raw(
            {'restaurant': session['restaurant']}))
        for order in orders:
            if order._id == ObjectId(order_id):
                if order.restaurant.email == session['restaurant']:
                    order.state = "Entregado"
                    order.save()
        return redirect('/')


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
            menu = Menu(ObjectId(), composition, price,
                        valid_date, [], photo_url)
            restaurant.menus.append(menu)
            restaurant.save()
        except Exception as e:
            print(e)
            restaurant.menus.pop()
            return render_template('menus/create.html', error=True)
        return redirect('/menus')


@app.route('/menus/edit/<id>', methods=['GET', 'POST'])
@restaurant_logged_in
def menus_edit(id):
    restaurant = Restaurant.objects.get({'_id': session['restaurant']})
    menu_and_idx = [(menu, idx) for idx, menu in enumerate(
        restaurant.menus) if menu._id == ObjectId(id)]
    menu = menu_and_idx[0][0] if menu_and_idx else None
    if request.method == "GET":
        return render_template('menus/edit.html', menu=menu)
    else:
        try:
            if menu:
                composition = request.form['composition']
                price = float(request.form['price'])
                valid_date = datetime.datetime.strptime(
                    request.form['valid_date'], '%Y-%m-%d')
                photo = request.files['photo']
                photo_url = cloudinary.uploader.upload_image(photo).build_url()
                menu.composition = composition
                menu.price = price
                menu.valid_date = valid_date
                menu.photo_url = photo_url
                restaurant.save()
            else:
                return render_template('menus/edit.html', menu=None)
        except Exception as e:
            print(e)
            return render_template('menus/edit.html', menu=menu, error=True)
        return redirect('/menus')


@app.route('/menus/delete/<id>', methods=['GET', 'POST'])
@restaurant_logged_in
def menus_delete(id):
    restaurant = Restaurant.objects.get({'_id': session['restaurant']})
    menu = [menu for menu in
            restaurant.menus if menu._id == ObjectId(id)]
    menu = menu[0] if menu else None
    if request.method == "GET":
        return render_template('menus/delete.html', menu=menu)
    else:
        try:
            if menu:
                restaurant.menus.remove(menu)
                restaurant.save()
            else:
                return render_template('menus/delete.html', menu=None)
        except Exception as e:
            print(e)
            return render_template('menus/delete.html', menu=menu, error=True)
        return redirect('/menus')


@app.route('/menus/calificate/<restaurant_id>/<menu_id>', methods=['GET', 'POST'])
@user_logged_in
def menus_calificate(restaurant_id, menu_id):
    restaurant = Restaurant.objects.get({'_id': restaurant_id})
    menu = [menu for menu in
            restaurant.menus if menu._id == ObjectId(menu_id)]
    menu = menu[0] if menu else None
    if menu.valid_date >= datetime.datetime.now():
        menu = None
    if request.method == "GET":
        return render_template('menus/calificate.html', menu=menu)
    else:
        try:
            if menu:
                opinion = Opinion(
                    session['user'], request.form['score'], request.form['commentary'])
                menu.opinions.append(opinion)
                restaurant.save()
            else:
                return render_template('menus/calificate.html', menu=None)
        except Exception as e:
            print(e)
            return render_template('menus/calificate.html', menu=menu, error=True)
        return redirect('/')


@ app.route('/')
def index():
    orders = []
    if 'restaurant' in session:
        menus = Restaurant.objects.only('menus').get(
            {'_id': session['restaurant']}).menus
        menus_ids = [menu._id for menu in menus]
        for id in menus_ids:
            sub_orders = Order.objects.get_queryset().raw({'menu_id': id})
            orders.extend(sub_orders)
    return render_template('index.html', restaurants=Restaurant.objects.all(), orders=orders)


def main():
    app.run(debug=True)


if __name__ == "__main__":
    main()
