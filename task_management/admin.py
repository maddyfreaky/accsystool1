from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Project)
admin.site.register(Issue)
admin.site.register(Todolist)

