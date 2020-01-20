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
from .views import *

urlpatterns = [
    path('index/', Index.as_view(), name='index'),
    path('account/profile/', AccountProfile.as_view(), name='account_profile'),
    path('account/wallet/', AccountWallet.as_view(), name='account_wallet'),
    path('account/order/', AccountOrder.as_view(), name='account_order'),
    path('service/<int:pk>', Service.as_view(), name='service'),
    path('order/details/<str:pk>', OrderDetails.as_view(), name='order_details'),

    path('alipay/return/', AliPayAPIView.as_view(), name='alipay_return'),
    path('order/place/', OrderPlace.as_view(), name='order_place'),
    path('order/list/', OrderListAPIView.as_view(), name='order_list'),
    path('order/cancel/', OrderCancel.as_view(), name='order_cancel'),
    path('channel/list/', ChannelListAPIView.as_view(), name='channel_list'),
    path('wallet/top-up/', WalletTopUp.as_view(), name='wallet_top_up'),
    path('channel/renew/', Renew.as_view(), name='channel_renew'),
    path('channel/upgrade/', Upgrade.as_view(), name='channel_upgrade'),

    path('api/geetest/crack/', GeetestAPIView.as_view(), name='geetest_crack'),
]
