from django.db import models


class Supplier(models.Model):
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()
    location = models.TextField()

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name
