from .serializers import buy_book_ser, EmailSerializer
from .models import Buy_book, Member
from rest_framework import generics, status
from django.core.mail import send_mail
from .serializers import EmailSerializer
from rest_framework.views import APIView
from django.db.models import F
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Book
from django.shortcuts import render, redirect, get_object_or_404
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
from collections import Counter


@login_required
def home(request):
    # Step 1: Retrieve the search query from the URL parameters
    search_query = request.GET.get('search', '')

    # Step 2: Create an API request factory
    factory = APIRequestFactory()

    # Step 3: Create a DRF request with the search query
    drf_request = factory.get('/book/', {'search': search_query})
    top = factory.get('http://127.0.0.1:8000/history?search=borrow')

    filtered_history = history.as_view()(top).data
    user_borrow = [
        item for item in filtered_history if item['member'] == request.user.member.id]

    print(f'user {user_borrow}')

    # Count occurrences of each book ID in the filtered history data
    book_counts = Counter(item['book'] for item in filtered_history)
    print(book_counts)
    book_counts_user = Counter(item['book'] for item in user_borrow)

    # Get the top 5 most borrowed book IDs
    top_5_books = [book_id for book_id, count in book_counts.most_common(5)]
    top_5_books_user = [book_id for book_id,
                        count in book_counts_user.most_common(5)]
    # Fetch the book details for these top 5 book IDs
    top_books_details = Book.objects.filter(id__in=top_5_books)

    top_books_details_user = Book.objects.filter(id__in=top_5_books_user)
    print(f'top books by the user borrowed {top_books_details_user}')

    genres = [book.genre for book in top_books_details_user]
    genre_ids = [genre.id for genre in genres]

    print(f' genre {genre_ids}')

    sugested = Book.objects.filter(genre__in=set(genre_ids))
    print(f'data {sugested}')
    filtered_book_ids = sugested.values_list('id', flat=True)

# Filter the history data to include only the books with these IDs
    filtered_history_books = [
        item for item in filtered_history if item['book'] in filtered_book_ids]
    print(f'mmmmmmmmmmm {filtered_history_books}')

    book_counts_genre = Counter(item['book']
                                for item in filtered_history_books)
    print(book_counts_genre)

    top_5_books_in_genre = [book_id for book_id,
                            count in book_counts_genre.most_common(5)]
    print(str(top_5_books_in_genre))
    top_sugestion = Book.objects.filter(id__in=top_5_books_in_genre)

    sugestion = BookSerializer(top_sugestion, many=True).data

    # Serialize the book details
    top_books_data = BookSerializer(top_books_details, many=True).data

    # Step 4: Call the DRF view with the DRF request and retrieve the filtered data
    books_data = Book_view.as_view()(drf_request).data

    # Step 5: Get the username of the logged-in user
    user_name = request.user.username

    # Step 6: Pass the serialized data and username to the template context
    return render(request, 'home.html', {'books': books_data, 'name': user_name, 'top_picks': top_books_data, 'sugestion': sugestion})


class Book_view(generics.ListAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ['title', 'author__name', 'genre__name', 'publisher']
    ordering_fields = ['title', 'author__name', 'genre__name']


class Book_post(generics.CreateAPIView):
    queryset = Book.objects.all()
    serializer_class = book_post

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            return Response({'message': 'Book added successfully'}, status=status.HTTP_201_CREATED)
        return response


class Book_update(generics.RetrieveUpdateAPIView):
    queryset = Book.objects.all()
    serializer_class = book_post


def update_book_html_view(request, pk):
    book = get_object_or_404(Book, pk=pk)
    authors = Author.objects.all()
    genres = Genre.objects.all()
    return render(request, 'update_book.html', {
        'book': book,
        'authors': authors,
        'genres': genres
    })


@login_required
def book_add_func(request):
    genre = Genre.objects.all()
    author = Author.objects.all()
    return render(request, 'add_book.html', {'genres': genre, 'authors': author})


class SingleBookAPIView(generics.RetrieveAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer


@login_required
def single_book(request, pk):
    response = requests.get(f'http://127.0.0.1:8000/book/{pk}/')
    print(response)
    return render(request, 'single_book.html', {'data': response.json()})


@login_required
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

        # Save the borrow instance and assign the member to it
        borrow_instance = serializer.save(member=member)

        # Retrieve the related book and due date information
        book = borrow_instance.book
        due_date = borrow_instance.due_back

        # Format the due date nicely
        formatted_due_date = due_date.strftime('%B %d, %Y')

        # Define the email subject and message
        subject = 'Borrow Confirmation'
        message = (
            f'Dear {member.user.username},\n\n'
            f'Thank you for borrowing the book "{book.title}" by {book.author}.\n\n'
            f'Your due date for returning this book is {formatted_due_date}.\n\n'
            f'We hope you enjoy reading it.\n\n'
            f'Best regards,\n'
            f'The Library Team'
        )
        recipient_list = [self.request.user.email]

        # Prepare data for email
        email_data = {
            'subject': subject,
            'message': message,
            'recipient_list': recipient_list
        }

        # Create a request factory
        factory = APIRequestFactory()

        # Create a POST request
        request = factory.post(
            'http://127.0.0.1:8000/email/', email_data, format='json')

        # Force authentication with the current user
        request.user = self.request.user

        # Get the response from SendEmailView
        view = SendEmailView.as_view()
        response = view(request)

        # Check response status
        if response.status_code != status.HTTP_200_OK:
            raise Exception('Failed to send email')


class return_book(generics.RetrieveDestroyAPIView):
    queryset = Borrow.objects.all()
    serializer_class = return_ser

    def perform_destroy(self, instance):
        # Retrieve the book details before deleting the instance
        book_title = instance.book.title
        book_author = instance.book.author

        # Call the original destroy method to delete the instance
        instance.delete()

        # Define email subject and message
        subject = 'Return Confirmation'
        message = (
            f'Dear {self.request.user.username},\n\n'
            f'Thank you for returning the book "{book_title} by {book_author}"!\n\n'
            f'We hope you enjoyed reading it.\n\n'
            f'Best regards,\n'
            f'The Library Team'
        )
        recipient_list = [self.request.user.email]

        # Prepare data for email
        email_data = {
            'subject': subject,
            'message': message,
            'recipient_list': recipient_list
        }

        # Create a request factory
        factory = APIRequestFactory()

        # Create a POST request
        request = factory.post('send-email/', email_data, format='json')

        # Force authentication with the current user
        request.user = self.request.user

        # Get the response from SendEmailView
        view = SendEmailView.as_view()
        response = view(request)

        # Check response status
        if response.status_code != status.HTTP_200_OK:
            raise Exception('Failed to send email')


@login_required
def book_return(request, pk):
    user = request.user
    try:
        # Attempt to retrieve the borrowed book entry
        borrowed_book = Borrow.objects.get(member=user.id, book=pk)
        # If the book is found, perform the return action (e.g., delete the borrowed book entry)
        book = borrowed_book.book
        book.inventory += 1  # Increment the book's inventory
        book.save()
        # Retrieve the corresponding Member instance for the current user
        member = Member.objects.get(user=user)
        # Log the return event in history
        History.objects.create(
            event_type='return',
            member=member,
            book=book,
            details=f"{book.title} returned by {user.username}"
        )
        borrowed_book.delete()
        messages.success(request, 'Your book has been returned successfully!')

        # Define email subject and message
        subject = 'Return Confirmation'
        message = (
            f'Dear {user.username},\n\n'
            f'Thank you for returning the book "{book.title}" by {book.author}!\n\n'
            f'We hope you enjoyed reading it.\n\n'
            f'Best regards,\n'
            f'The Library Team'
        )
        recipient_list = [user.email]

        # Prepare data for email
        email_data = {
            'subject': subject,
            'message': message,
            'recipient_list': recipient_list
        }

        # Create a request factory
        factory = APIRequestFactory()

        # Create a POST request
        request = factory.post(
            'http://127.0.0.1:8000/email/', email_data, format='json')

        # Force authentication with the current user
        request.user = user

        # Get the response from SendEmailView
        view = SendEmailView.as_view()
        response = view(request)

        # Check response status
        if response.status_code != status.HTTP_200_OK:
            raise Exception('Failed to send email')

        # Add a success message

        # Redirect the user to the home page
        return redirect('http://127.0.0.1:8000/home')
    except Borrow.DoesNotExist:
        # If the book is not found in the user's borrowed books, return a 404 error
        return HttpResponseNotFound()


@login_required
def return_html(request):

    borrow = Borrow.objects.filter(member=request.user.id)

    return render(request, 'return.html', {'data': borrow})


def buy_func(request, pk):
    try:
        book = Book.objects.get(id=pk)
    except Book.DoesNotExist:
        # Handle the case where the book does not exist
        # For example, you can return a 404 error page
        return HttpResponseNotFound("The requested book does not exist.")

    return render(request, 'buy.html', {'id': book.id})


class Buy(generics.ListCreateAPIView):
    queryset = Buy_book.objects.all()
    serializer_class = buy_book_ser

    def perform_create(self, serializer):
        # Get the Member object associated with the current user
        member = Member.objects.get(user=self.request.user)
        # Assign the Member object to the serializer's 'member' field
        serializer.save(member=member)

        # Define email subject and message
        subject = 'Purchase Confirmation'
        message = f'Thank you for your purchase, {member.user.username}!'
        recipient_list = [self.request.user.email]

        # Prepare data for email
        email_data = {
            'subject': subject,
            'message': message,
            'recipient_list': recipient_list
        }

        # Create a request factory
        factory = APIRequestFactory()

        # Create a POST request
        request = factory.post(
            'http://127.0.0.1:8000/email/', email_data, format='json')

        # Force authentication with the current user
        request.user = self.request.user

        # Get the response from SendEmailView
        view = SendEmailView.as_view()
        response = view(request)

        # Check response status
        if response.status_code != status.HTTP_200_OK:
            raise Exception('Failed to send email')


def profile(request):
    Data = History.objects.filter(member=request.user.id)
    return render(request, 'profile.html', {'data': Data})


class history(generics.ListAPIView):
    queryset = History.objects.all()
    serializer_class = History_ser
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)

    search_fields = ['event_type', 'details', 'timestamp']
    ordering_fields = ['member', 'event_type', 'id']


def admin_history(request):
    return render(request, 'history.html')


def mailed_person(request):

    pass


class SendEmailView(APIView):
    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        if serializer.is_valid():
            subject = serializer.validated_data['subject']
            message = serializer.validated_data['message']
            recipient_list = serializer.validated_data['recipient_list']
            email_from = 'mdraiyanrahman03@gmail.com'

            send_mail(subject, message, email_from, recipient_list)

            return Response({'status': 'Email sent'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
