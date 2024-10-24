from django.urls import path
from .views import index, admin_action, customer_page, place_order, login_view

urlpatterns = [
    path('index/', index, name='index'),
    path('admin/', admin_action, name='admin_action'),
     path('products/', customer_page, name='product_list'),
     path('place-order/', place_order, name='place_order'),
     path('login/', login_view, name='login'),
]
