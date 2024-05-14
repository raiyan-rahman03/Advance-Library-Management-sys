from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
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
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True,default=0)
    publisher = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    inventory = models.IntegerField(
        null=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(50)
        ]
    )


    def __str__(self):
        return self.title

class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    membership_status = models.CharField(max_length=20, choices=[('active', 'Active'), ('inactive', 'Inactive')])
    membership_expiry_date = models.DateField()

    def __str__(self):
        return self.user.username
    





from django.utils import timezone

class Borrow(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    borrowed_at = models.DateTimeField(auto_now_add=True ,null=True)
    due_back = models.DateTimeField()

    def clean(self):
        if self.borrowed_at and self.due_back <= self.borrowed_at:
            raise ValidationError("Due date must be after the borrowing date.")
        if self.borrowed_at and (self.due_back - self.borrowed_at).days > 10:
            raise ValidationError("Borrowing period cannot exceed 10 days.")
        
        existing_borrow = Borrow.objects.filter(book=self.book, member=self.member).exists()
        if existing_borrow:
            raise ValidationError("You have already borrowed this book.")

    def save(self, *args, **kwargs):
        self.clean()  # Ensure validation is performed before saving
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.book.title} borrowed by {self.member.user.username} on {self.borrowed_at}"

