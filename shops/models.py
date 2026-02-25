from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Shop(models.Model):
    name = models.CharField(max_length=100, unique=True)
    owner = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='shop'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'shops'