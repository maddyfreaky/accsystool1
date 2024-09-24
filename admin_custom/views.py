from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.

def admin_custom(request):
    return render(request,"admin.html")

def components(request):
    return render(request,"components.html")