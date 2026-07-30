from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('PLAYER', 'Player'),
        ('SHOP_OWNER', 'Shop Owner'),
    )

    name = models.CharField(
        max_length=100,
        blank=True,
        null=True
        )

    email = models.EmailField(unique=True)

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    money = models.IntegerField(default=0)

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
    
    class Meta:
        db_table = 'users'
