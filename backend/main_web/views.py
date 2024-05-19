from django.db.models import F
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Book
from django.shortcuts import render, redirect
from rest_framework import generics, filters
from .models import *
from .serializers import *
from rest_framework import status
from rest_framework.response import Response
import requests
from django.http import HttpResponseNotFound
from rest_framework.request import Request



from django.shortcuts import render
from rest_framework.test import APIRequestFactory


def home(request):
    # Step 1: Retrieve the search query from the URL parameters
    search_query = request.GET.get('search', '')

    # Step 2: Create an API request factory
    factory = APIRequestFactory()

    # Step 3: Create a DRF request with the search query
    drf_request = factory.get('/book/', {'search': search_query})

    # Step 4: Call the DRF view with the DRF request and retrieve the filtered data
    books_data = Book_view.as_view()(drf_request).data

    # Step 5: Get the username of the logged-in user
    user_name = request.user.username

    # Step 6: Pass the serialized data and username to the template context
    return render(request, 'home.html', {'books': books_data, 'name': user_name})



class Book_view(generics.ListAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ['title', 'author__name', 'genre__name','publisher']
    ordering_fields = ['title', 'author__name', 'genre__name']


class Book_post(generics.CreateAPIView):
    queryset = Book.objects.all()
    serializer_class = book_post

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            return Response({'message': 'Book added successfully'}, status=status.HTTP_201_CREATED)
        return response


def book_add_func(request):
    genre = Genre.objects.all()
    author = Author.objects.all()
    return render(request, 'add_book.html', {'genres': genre, 'authors': author})


class SingleBookAPIView(generics.RetrieveAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer


def single_book(request, pk):
    response = requests.get(f'http://127.0.0.1:8000/book/{pk}/')
    print(response)
    return render(request, 'single_book.html', {'data': response.json()})


def borrow(request, pk):
    try:
        book = Book.objects.get(id=pk)
    except Book.DoesNotExist:
        # Handle the case where the book does not exist
        # For example, you can return a 404 error page
        return HttpResponseNotFound("The requested book does not exist.")

    return render(request, 'borrow.html', {'id': book.id})


class Borrow_view(generics.ListCreateAPIView):
    queryset = Borrow.objects.all()
    serializer_class = borrow_ser

    def perform_create(self, serializer):
        # Get the Member object associated with the current user
        member = Member.objects.get(user=self.request.user)
        # Assign the Member object to the serializer's 'member' field
        serializer.save(member=member)


class return_book(generics.RetrieveDestroyAPIView):
    queryset = Borrow.objects.all()
    serializer_class = return_ser


@login_required
def book_return(request, pk):
    user = request.user
    try:
        # Attempt to retrieve the borrowed book entry
        borrowed_book = Borrow.objects.get(member=user.id, book=pk)

        # If the book is found, perform the return action (e.g., delete the borrowed book entry)
        book = borrowed_book.book
        book.inventory = F('inventory') + 1
        book.save()

        borrowed_book.delete()

        # Add a success message
        messages.success(request, 'Your book has been returned successfully!')
        # Redirect the user to the home page
        return redirect('http://127.0.0.1:8000/home')
    except Borrow.DoesNotExist:
        # If the book is not found in the user's borrowed books, return a 404 error
        return HttpResponseNotFound()


def return_html(request):

    borrow = Borrow.objects.filter(member=request.user.id)

    return render(request, 'return.html', {'data': borrow})
