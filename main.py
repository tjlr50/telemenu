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
dashboard

set MONGO_URI=mongodb://localhost:27017/telemenu
set SECRET=cambiar
... set PRODUCTION=True
"""
import os
from flask import (Flask)

from models import User, Menu, Order, Restaurant


SECRET_KEY = os.environ.get('SECRET')
PROD = bool(os.environ.get('PRODUCTION', False))
app = Flask(__name__)
app.secret = SECRET_KEY


def main():
    app.run(debug=True)


if __name__ == "__main__":
    main()
