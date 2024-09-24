from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def workflow(request):
    return render(request,"workflow.html")