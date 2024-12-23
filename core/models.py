from django.db import models

class Bank(models.Model):
    name = models.CharField(max_length=100, default="AspireBank")
    is_bankrupt = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    