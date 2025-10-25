from tortoise import fields, Tortoise
from tortoise.models import Model

class User(Model):
    id = fields.IntField(pk=True)
    username = fields.TextField()

class Chat(Model):
    id = fields.IntField(pk=True)
    chatname = fields.TextField()
    admins = fields.ManyToManyField("models.User")