from django.db import models
from django.contrib.auth.models import User

class Author(models.Model):
    name = models.CharField(max_length=100)
    biography = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True)
    nationality = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name

class Genre(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True)
    publisher = models.CharField(max_length=100)
    description = models.TextField(blank=True)


    def __str__(self):
        return self.title

class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    membership_status = models.CharField(max_length=20, choices=[('active', 'Active'), ('inactive', 'Inactive')])
    membership_expiry_date = models.DateField()

    def __str__(self):
        return self.user.username
