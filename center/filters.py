import django_filters
from .models import *


class ChannelFilter(django_filters.rest_framework.FilterSet):
    # 过滤器字段，label为字段名称，无意义，method为过滤规则方法
    product = django_filters.NumberFilter(label="产品ID", method='product_filter')

    def product_filter(self, queryset, name, value):
        return queryset.filter(product__id=value)

    class Meta:
        model = InterfaceChannel
        fields = ['product']
