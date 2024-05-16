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
        
  # Include all fields of the Book model
class borrow_ser(serializers.ModelSerializer):
    class Meta:
        model = Borrow
        fields = ['due_back','book']

class return_ser(serializers.ModelSerializer):
    class Meta:
        model = Borrow
        fields = '__all__'