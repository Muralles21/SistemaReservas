from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.LandingView.as_view(), name='inicio'),
    path('catalogo/', views.CatalogoView.as_view(), name='catalogo'),
]
