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
from django.conf import settings
from django.urls import path, include
from django.views import static
from rest_framework import routers
import xadmin

from users.views import UserViewSet
from console.views import ProductViewSet, ProductPackageViewSet, OrderViewSet, OrderGoodsViewSet, ServiceViewSet
from utils.upload import UploadAvatar

router = routers.DefaultRouter()
router.register(r'user', UserViewSet)
router.register(r'product', ProductViewSet)
router.register(r'product_package', ProductPackageViewSet)
router.register(r'order', OrderViewSet, base_name="order")  # 加 base_name 避免因没有 queryset 而报错
router.register(r'order_goods', OrderGoodsViewSet, base_name="order_goods")
router.register(r'service', ServiceViewSet, base_name="service")

urlpatterns = [
    path('media/<path:path>', static.serve, {'document_root': settings.MEDIA_ROOT}),
    path('upload/', UploadAvatar.as_view()),
    path('xadmin/', xadmin.site.urls),
    path('api-auth/', include('rest_framework.urls')),  # 增加REST框架的登录和注销视图
    path('', include(router.urls)),
    path('', include('users.urls')),
    path('', include('console.urls')),
]
