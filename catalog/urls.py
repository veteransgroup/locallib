from django.urls import path
from catalog import views

urlpatterns = [
    path('hello', views.hello),
    path('', views.index, name='index'),
]