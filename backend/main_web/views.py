from django.shortcuts import render ,redirect
from django.views import generic
from rest_framework import generics
from .models import *
from .serializers import *
from rest_framework import status
from rest_framework.response import Response
# Create your views hee.
def home(request):


    books_data = Book_view.as_view()(request).data
    user_name = request.user.username

    # Pass the serialized data to the template context

    return render(request,'home.html',{'books':books_data ,'name':user_name})

class Book_view(generics.ListAPIView):
    queryset=  Book.objects.all()
    serializer_class = BookSerializer
    
class Book_post(generics.CreateAPIView):
    queryset=  Book.objects.all()
    serializer_class = BookSerializer
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            return Response({'message': 'Book added successfully'}, status=status.HTTP_201_CREATED)
        return response
def book_add_func(request):
    genre =Genre.objects.all()
    author =Author.objects.all()
    return render(request, 'add_book.html', {'genres': genre, 'authors': author})