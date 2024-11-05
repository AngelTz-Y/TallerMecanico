from django.urls import path
from App_TallerMecanico.views import *
urlpatterns = [
    path('', inicio_view, name='inicio'),
    path('registro/', registro_view, name='registro'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('perfil/', perfil_view, name='perfil'),
    path('admin_panel/', admin_panel, name='admin_panel'),
    path('admin_panel/agregar_mecanico/', agregar_mecanico, name='ingresar_mecanico'),
    path('admin_panel/listar_mecanicos/', listar_mecanicos, name='listar_mecanicos'),
    path('admin_panel/modificar_mecanico/<str:mecanico_id>/', modificar_mecanico, name='modificar_mecanico'),
    path('admin_panel/eliminar_mecanico/<str:mecanico_id>/', eliminar_mecanico, name='eliminar_mecanico'),
    path('admin_panel/registrar_informe/<int:trabajo_id>/', registrar_informe, name='registrar_informe'),
    path('admin_panel/consultar_historico_reparaciones/<str:patente>/', consultar_historico_reparaciones, name='consultar_historico_reparaciones'),
    path('mecanico_panel/', mecanico_panel, name='dashboard_mecanico'),
    path('mecanico_panel/ingresar_cliente/', ingresar_cliente, name='ingresar_cliente'),
    path('mecanico_panel/listar/', listar_clientes, name="listar_cliente")
]
