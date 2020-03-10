import xadmin
from .models import *


xadmin.site.register(Product)
xadmin.site.register(ProductPackage)
xadmin.site.register(Order)
xadmin.site.register(OrderGoods)
xadmin.site.register(Service)
