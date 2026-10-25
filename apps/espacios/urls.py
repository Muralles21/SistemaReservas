from django.urls import path
from . import views

app_name = 'espacios'

urlpatterns = [
    path('', views.EspacioListView.as_view(), name='lista'),
    path('nuevo/', views.EspacioCreateView.as_view(), name='crear'),
    path('<int:pk>/', views.EspacioDetailView.as_view(), name='detalle'),
    path('<int:pk>/editar/', views.EspacioUpdateView.as_view(), name='editar'),
    path('<int:pk>/eliminar/', views.EspacioDeleteView.as_view(), name='eliminar'),
]
