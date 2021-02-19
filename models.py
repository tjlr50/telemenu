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


class Opinion(EmbeddedMongoModel):
    # Opinion tiene
    # Calificación
    # Comentario
    author = fields.ReferenceField(User, required=True)
    score = fields.FloatField(required=True)
    commentary = fields.CharField(required=True)


class Menu(EmbeddedMongoModel):
    # Menu tiene composición
    # Precio
    # Fecha de validez (end timestamp)
    # fotografía
    _id = fields.ObjectIdField(primary_key=True)
    composition = fields.CharField(required=True, blank=False)
    price = fields.FloatField(required=True)
    valid_date = fields.DateTimeField(required=True)
    opinions = fields.EmbeddedDocumentListField(Opinion, default=[])
    photo_url = fields.CharField(required=True, blank=False)


class Restaurant(MongoModel):
    # Correo
    # Nombre
    # Contraseña de acceso
    # Menus
    email = fields.EmailField(primary_key=True, required=True)
    name = fields.CharField(required=True, blank=False)
    password = fields.CharField(required=True)
    menus = fields.EmbeddedDocumentListField(Menu, default=[])


class Order(MongoModel):
    # creadoPor -ref
    # Menu - ref
    # estado enum
    _id = fields.ObjectIdField(primary_key=True)
    created_date = fields.DateTimeField(required=True)
    restaurant = fields.ReferenceField(Restaurant, required=True)
    user = fields.ReferenceField(User, required=True)
    menu_id = fields.ObjectIdField(required=True)
    # Manejar estado mediante logica de la aplicación
    state = fields.CharField(required=True, blank=False)
