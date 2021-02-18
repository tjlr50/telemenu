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
idx (el muro)
dashboard -> ver ordenes
orders/ orders/:id order/create

Rutas Restaurant:
login
logup
dashboard -> ver ordenes
menus/ menus/:id menus/create

set MONGO_URI=mongodb://localhost:27017/telemenu
set SECRET=cambiar
... set PRODUCTION=True


"""
import os
import bcrypt
from flask import (Flask, request, session, redirect)
from flask.templating import render_template
from pymodm.errors import ValidationError
import pymongo.errors
from models import User, Menu, Order, Restaurant


SECRET_KEY = os.environ.get('SECRET')
PROD = bool(os.environ.get('PRODUCTION', False))
app = Flask(__name__)
app.secret_key = SECRET_KEY


@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == "GET":
        return render_template('user_login.html')
    else:
        try:
            email, password = request.form['email'], request.form['password']
            user = User.objects.get({'_id': email})
            if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                session.pop('restaurant', None)
                session['user'] = user.email
                return redirect('/')
            else:
                return render_template('user_login.html', wrong_pass=True)
        except User.DoesNotExist:
            return render_template('user_login.html', no_user=True)


@app.route('/user/logup', methods=['GET', 'POST'])
def user_logup():
    if request.method == "GET":
        return render_template('user_logup.html')
    else:
        try:
            password = request.form['password']
            password = bcrypt.hashpw(
                password.encode('utf-8'), bcrypt.gensalt())
            User(email=request.form['email'], full_name=request.form['full_name'], password=password.decode('utf-8')).save(
                force_insert=True)
        except ValidationError as ve:
            return render_template('user_logup.html', email_error="Formato de correo Incorrecto")
        except pymongo.errors.DuplicateKeyError:
            return render_template('user_logup.html', email_error="Ya existe un usuario con ese correo")
    return redirect('/user/login')


@app.route('/orders')
def orders():
    pass  # -> noop


@app.route('/orders/<id>')
def order():
    pass  # -> noop


@app.route('/orders/create')
def order_create():
    pass  # -> noop

# Comprobar si es usuario o restaurante mediante sesión, ofrecer login si no hay sesión


@app.route('/dasboard')
def dashboard():
    pass


@app.route('/restaurant/login', methods=['GET', 'POST'])
def restaurant_login():
    if request.method == "GET":
        return render_template('restaurant_login.html')
    else:
        try:
            email, password = request.form['email'], request.form['password']
            restaurant = Restaurant.objects.get({'_id': email})
            if bcrypt.checkpw(password.encode('utf-8'), restaurant.password.encode('utf-8')):
                session.pop('user', None)
                session['restaurant'] = restaurant.email
                return redirect('/')
            else:
                return render_template('restaurant_login.html', wrong_pass=True)
        except User.DoesNotExist:
            return render_template('restaurant_login.html', no_restaurant=True)


@app.route('/restaurant/logup')
def restaurant_logup():
    if request.method == "GET":
        return render_template('restaurant_logup.html')
    else:
        try:
            password = request.form['password']
            password = bcrypt.hashpw(
                password.encode('utf-8'), bcrypt.gensalt())
            Restaurant(email=request.form['email'], name=request.form['restaurant_name'], password=password.decode('utf-8')).save(
                force_insert=True)
        except ValidationError as ve:
            return render_template('restaurant_logup.html', email_error="Formato de correo Incorrecto")
        except pymongo.errors.DuplicateKeyError:
            return render_template('restaurant_logup.html', email_error="Ya existe un restaurante con ese correo")
    return redirect('/restaurant/login')


# Comprobar si es usuario o restaurante mediante sesión, ofrecer login si no hay sesión


@app.route('/')
def index():
    return render_template('index.html', restaurants=list(Restaurant.objects.all()))


def main():
    app.run(debug=True)


if __name__ == "__main__":
    main()
