from rest_framework import serializers
from .models import *

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__' 

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = '__all__' 

class BookSerializer(serializers.ModelSerializer):
    author = AuthorSerializer()
    genre = GenreSerializer()

    class Meta:
        model = Book
        fields = '__all__'
        
class book_post(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['title','author','genre','publisher','inventory','description']

  # Include all fields of the Book model
class borrow_ser(serializers.ModelSerializer):
    class Meta:
        model = Borrow
        fields = ['book','borrowed_at','due_back']

class return_ser(serializers.ModelSerializer):
    class Meta:
        model = Borrow
        fields = '__all__'

class buy_book_ser(serializers.ModelSerializer):
    class Meta:
        model=Buy_book
        fields=['book']

class History_ser(serializers.ModelSerializer):
    class Meta:
        model = History
        fields = '__all__'