from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Author)
admin.site.register(Genre)
admin.site.register(Book)
admin.site.register(Member)
admin.site.register(Borrow)
admin.site.register(Buy_book)
admin.site.register(History)


