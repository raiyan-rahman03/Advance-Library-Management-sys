from django.shortcuts import render ,redirect
from django.views import generic
from rest_framework import generics
from .models import *
from .serializers import *
from rest_framework import status
from rest_framework.response import Response
import requests
from django.http import HttpResponseNotFound

# Create your views hee.
def home(request):
    books_data = Book_view.as_view()(request).data
    user_name = request.user.username
    
    # Pass the serialized data to the template context
    return render(request,'home.html',{'books':books_data ,'name':user_name})
from rest_framework import generics
from .models import Book
from .serializers import BookSerializer
from django.http import Http404

class Book_view(generics.ListAPIView):
    queryset = Book.objects.all()
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
class SingleBookAPIView(generics.RetrieveAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

def single_book(request,pk):
    response = requests.get(f'http://127.0.0.1:8000/book/{pk}/')
    print(response)
    return render(request, 'single_book.html', {'data': response.json()})

def borrow(request,pk):
    try:
        book = Book.objects.get(id=pk)
    except Book.DoesNotExist:
        # Handle the case where the book does not exist
        # For example, you can return a 404 error page
        return HttpResponseNotFound("The requested book does not exist.")

    return render(request, 'borrow.html', {'id': book.id})

class Borrow_view(generics.ListCreateAPIView):
    queryset = Borrow.objects.all()
    serializer_class =borrow_ser

    def perform_create(self, serializer):
        # Get the Member object associated with the current user
        member = Member.objects.get(user=self.request.user)
        # Assign the Member object to the serializer's 'member' field
        serializer.save(member=member)