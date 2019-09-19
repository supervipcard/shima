"""shima URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
import xadmin
from users.views import *
from center.views import *

urlpatterns = [
    path('xadmin/', xadmin.site.urls),

    path('sign_in/', SignInView.as_view(), name='sign_in'),
    path('sign_up/', SignUpView.as_view(), name='sign_up'),
    path('sendmail/', SendEmail.as_view(), name='sendmail'),
    path('captcha/', CreateCaptcha.as_view(), name='captcha'),

    path('login/', Login.as_view(), name='login'),
    path('logout/', Logout.as_view(), name='logout'),
    path('register/', Register.as_view(), name='register'),

    path('forget_password/', ForgetPasswordView.as_view(), name='forget_password'),
    path('forget_password2/', ForgetPasswordView2.as_view(), name='forget_password2'),
    path('verify_email/', VerifyEmail.as_view(), name='verify_email'),
    path('reset_password/', ResetPassword.as_view(), name='reset_password'),

    path('dashboard/', Dashboard.as_view(), name='dashboard'),
    path('service/<int:product_id>/', Service.as_view(), name='service'),
]
