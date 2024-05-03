from django.shortcuts import render ,redirect

# Create your views hee.
def home(request):
    return render(request,'home.html')