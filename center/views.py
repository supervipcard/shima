from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from .models import *


def global_setting(request):
    product = Product.objects.all()
    return {'product': product}


class Dashboard(View):
    @method_decorator(login_required)
    def get(self, request):
        return render(request, 'index.html')


class Service(View):
    def get(self, request, product_id):
        print(product_id)
        return render(request, 'service.html')
