from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('', views.UsuarioListView.as_view(), name='lista'),
    path('nuevo/', views.UsuarioCreateView.as_view(), name='crear'),
    path('<int:pk>/editar/', views.UsuarioUpdateView.as_view(), name='editar'),
    path('<int:pk>/eliminar/', views.UsuarioDeleteView.as_view(), name='eliminar'),
    path('<int:pk>/desbloquear/', views.UsuarioDesbloquearView.as_view(), name='desbloquear'),

    path('roles/', views.RolListView.as_view(), name='rol_lista'),
    path('roles/nuevo/', views.RolCreateView.as_view(), name='rol_crear'),
    path('roles/<int:pk>/editar/', views.RolUpdateView.as_view(), name='rol_editar'),
    path('roles/<int:pk>/eliminar/', views.RolDeleteView.as_view(), name='rol_eliminar'),

    path('bitacora/', views.BitacoraListView.as_view(), name='bitacora'),
]
