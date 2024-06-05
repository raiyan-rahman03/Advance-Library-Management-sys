from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import json


class Author(models.Model):
    """
    Represents an author with details like name, biography, date of birth, and nationality.
    """
    name = models.CharField(max_length=100)
    biography = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True)
    nationality = models.CharField(max_length=100, blank=True)

    def save(self, *args, **kwargs):
        """
        Overrides the save method to log history events.
        Logs 'add' event when a new author is created, and 'update' event when an existing author is updated.
        """
        is_new_author = not self.pk
        if not is_new_author:
            previous = Author.objects.get(pk=self.pk)

        super().save(*args, **kwargs)

        event = "New author added" if is_new_author else "Author updated"
        details = {
            "event": event,
            "author_name": self.name,
            "biography": self.biography,
            "date_of_birth": str(self.date_of_birth),
            "nationality": self.nationality
        }
        History.objects.create(
            event_type='add' if is_new_author else 'update',
            details=details
        )

    def __str__(self):
        return self.name


class Genre(models.Model):
    """
    Represents a genre with a name and description.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        """
        Overrides the save method to log history events.
        Logs 'add' event when a new genre is created, and 'update' event when an existing genre is updated.
        """
        is_new_genre = not self.pk
        if not is_new_genre:
            previous = Genre.objects.get(pk=self.pk)

        super().save(*args, **kwargs)

        event = "New genre added" if is_new_genre else "Genre updated"
        details = {
            "event": event,
            "genre_name": self.name,
            "description": self.description
        }
        History.objects.create(
            event_type='add' if is_new_genre else 'update',
            details=details
        )

    def __str__(self):
        return self.name


class Book(models.Model):
    """
    Represents a book with a title, author, genre, publisher, description, inventory, and price.
    """
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    genre = models.ForeignKey(
        Genre, on_delete=models.SET_NULL, null=True, default=0)
    publisher = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    inventory = models.IntegerField(
        null=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(50)
        ]
    )
    price = models.IntegerField(
        null=False,
        default=0,
        validators=[
            MinValueValidator(1)
        ]
    )

    def save(self, *args, **kwargs):
        """
        Overrides the save method to log history events.
        Logs 'add' event when a new book is created, and 'update' event when an existing book is updated.
        """
        is_new_book = not self.pk
        if not is_new_book:
            previous = Book.objects.get(pk=self.pk)

        super().save(*args, **kwargs)

        event = "New book added" if is_new_book else "Book updated"
        details = {
            "event": event,
            "book_title": self.title,
            "author": self.author.name,
            "genre": self.genre.name if self.genre else None,
            "publisher": self.publisher,
            "description": self.description
        }
        History.objects.create(
            event_type='add' if is_new_book else 'update',
            book=self,
            details=details
        )

    def __str__(self):
        return self.title


class Member(models.Model):
    """
    Represents a library member linked to a User, with membership status and expiry date.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    membership_status = models.CharField(
        max_length=20, choices=[('active', 'Active'), ('inactive', 'Inactive')])
    membership_expiry_date = models.DateField()



    def save(self, *args, **kwargs):
        """
        Overrides the save method to log history events.
        Logs 'add' event when a new member is created, and 'update' event when an existing member is updated.
        """
        is_new_member = not self.pk
        if not is_new_member:
            previous = Member.objects.get(pk=self.pk)

        super().save(*args, **kwargs)

        event = "New member added" if is_new_member else "Member updated"
        details = {
            "event": event,
            "username": self.user.username,
            "membership_status": self.membership_status,
            "membership_expiry_date": str(self.membership_expiry_date)
        }
        History.objects.create(
            event_type='add' if is_new_member else 'update',
            member=self,
            details=details
        )

    def __str__(self):
        return self.user.username


class Borrow(models.Model):
    """
    Represents a borrow transaction linking a book to a member with borrow and due dates.
    """
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    borrowed_at = models.DateTimeField(auto_now_add=True, null=True)
    due_back = models.DateTimeField()

    def clean(self):
        """
        Validates borrow transactions to ensure due date is after borrow date,
        borrowing period does not exceed 10 days, and the book has not already been borrowed by the same member.
        """
        if self.borrowed_at and self.due_back <= self.borrowed_at:
            raise ValidationError("Due date must be after the borrowing date.")
        if self.borrowed_at and (self.due_back - self.borrowed_at).days > 10:
            raise ValidationError("Borrowing period cannot exceed 10 days.")

        existing_borrow = Borrow.objects.filter(
            book=self.book, member=self.member).exists()
        if existing_borrow:
            raise ValidationError("You have already borrowed this book.")
        inventory = self.book.inventory
        if int(inventory) < 1:
            raise ValidationError("Book is not available for borrowing.")

    def save(self, *args, **kwargs):
        """
        Overrides the save method to validate and log history events.
        Logs 'borrow' event when a new borrow transaction is created, and 'update' event when an existing transaction is updated.
        """
        self.clean()  # Ensure validation is performed before saving
        is_new_borrow = not self.pk
        if not is_new_borrow:
            previous = Borrow.objects.get(pk=self.pk)

        super().save(*args, **kwargs)
        self.book.inventory -= 1
        self.book.save()

        event = "Book borrowed" if is_new_borrow else "Borrow updated"
        details = {
            "event": event,
            "book_title": self.book.title,
            "author": self.book.author.name,
            "genre": self.book.genre.name if self.book.genre else None,
            "publisher": self.book.publisher,
            "borrowed_at": str(self.borrowed_at),
            "due_back": str(self.due_back),
            "member": self.member.user.username
        }
        History.objects.create(
            event_type='borrow' if is_new_borrow else 'update',
            member=self.member,
            book=self.book,
            details=details
        )

    def __str__(self):
        return f"{self.book.title} borrowed by {self.member.user.username} on {self.borrowed_at}"


class Buy_book(models.Model):
    """
    Represents a book purchase transaction linking a book to a member with the purchase price.
    """
    book = models.ForeignKey(Book, on_delete=models.PROTECT)
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    price = models.IntegerField(null=False, validators=[MinValueValidator(1)])

    def clean(self):

        inventory = self.book.inventory
        if int(inventory) < 1:
            raise ValidationError("Book is not available for buying.")

    def save(self, *args, **kwargs):
        self.clean()
        """
        Overrides the save method to log history events.
        Logs 'buy' event when a new book purchase is created, and 'update' event when an existing purchase is updated.
        """
        self.price = self.book.price
        self.book.inventory -= 1
        self.book.save()
        is_new_buy = not self.pk
        if not is_new_buy:
            previous = Buy_book.objects.get(pk=self.pk)

        super().save(*args, **kwargs)

        event = "Book bought" if is_new_buy else "Buy updated"
        details = {
            "event": event,
            "book_title": self.book.title,
            "author": self.book.author.name,
            "genre": self.book.genre.name if self.book.genre else None,
            "publisher": self.book.publisher,
            "price": self.price,
            "member": self.member.user.username
        }
        History.objects.create(
            event_type='buy' if is_new_buy else 'update',
            member=self.member,
            book=self.book,
            details=details
        )

    def __str__(self):
        return f"{self.book.title} bought by {self.member.user.username}"


class History(models.Model):
    """
    Represents a history of significant events such as additions, updates, borrows, purchases, and returns.
    """
    EVENT_TYPES = [
        ('borrow', 'Borrowed'),
        ('buy', 'Bought'),
        ('add', 'Added'),
        ('return', 'Returned'),
        ('update', 'Updated')
    ]
    event_type = models.CharField(max_length=10, choices=EVENT_TYPES)
    member = models.ForeignKey(
        Member, on_delete=models.PROTECT, null=True, blank=True)
    book = models.ForeignKey(
        Book, on_delete=models.PROTECT, null=True, blank=True)
    details = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.book.title if self.book else 'N/A'} by {self.member.user.username if self.member else 'N/A'} at {self.timestamp}"
