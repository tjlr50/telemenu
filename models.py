import os
from pymodm import connect, fields, MongoModel, EmbeddedMongoModel

connect(os.environ.get('MONGO_URI'))


class User(MongoModel):
    # Usuario tiene correo
    # Nombre completo
    # Contraseña
    email = fields.EmailField(primary_key=True, required=True)
    full_name = fields.CharField(required=True, blank=False)
    password = fields.CharField(required=True)


class Menu(EmbeddedMongoModel):
    # Menu tiene composición
    # Precio
    # Fecha de validez (end timestamp)
    # fotografía
    composition = fields.CharField(required=True, blank=False)
    price = fields.FloatField(required=True)
    valid_date = fields.DateTimeField(required=True)
    photo_url = fields.CharField(required=True, blank=False)
    pass


class Order(MongoModel):
    # creadoPor -ref
    # Menu - ref
    # estado enum
    user = fields.ReferenceField(User, required=True)
    menu = fields.ReferenceField(Menu, required=True)
    # Manejar estado mediante logica de la aplicación
    state = fields.CharField(required=True, blank=False)
    pass


class Restaurant(MongoModel):
    # Correo
    # Nombre
    # Contraseña de acceso
    # Menus
    email = fields.EmailField(primary_key=True, required=True)
    full_name = fields.CharField(required=True, blank=False)
    password = fields.CharField(required=True)
    menus = fields.EmbeddedDocumentListField(Menu, default=[])
