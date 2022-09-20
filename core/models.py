from django.contrib.auth.models import AbstractUser
from django.db import models


# Exdending the user model. Add email - unique.
class User(AbstractUser):
    email = models.EmailField(unique=True)

# Then added changes to settings.py and registered in admin.py
