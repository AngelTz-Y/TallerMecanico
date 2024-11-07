from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.core.paginator import Paginator
from django.forms import *
from django.db import transaction
from .models import *
from .decoradores import role_required  # Importa el decorador personalizado

# Vista para la página de inicio (sin restricciones)
def inicio_view(request):
    return render(request, "inicio.html")

# Vista de registro (sin restricciones)
def registro_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("repassword")
        role = request.POST.get("role", "cliente")

        if Registro.objects.filter(username=username).exists():
            messages.error(request, "El nombre de usuario ya está en uso.")
            return redirect("registro")

        if password != confirm_password:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect("registro")

        try:
            registro = Registro(username=username, password=password, role=role)
            registro.save()
            messages.success(request, "Registro exitoso. Puedes iniciar sesión.")
            return redirect("login")
        except Exception as e:
            print("Error al guardar el registro:", e)
            messages.error(request, "Ocurrió un error al intentar registrarte. Inténtalo nuevamente.")
            return redirect("registro")

    return render(request, "registro.html")

# Vista de inicio de sesión (sin restricciones)
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        admin_key = request.POST.get("admin_key")

        user = Registro.objects.filter(username=username, password=password).first()
        if user:
            if user.role == 'admin' and username == 'admin':
                administrador = Administrador.objects.filter(nombre="Admin").first()
                if administrador and administrador.clave_unica == admin_key:
                    messages.success(request, "Inicio de sesión como Administrador.")
                    Login.objects.update_or_create(user=user, defaults={'ultima_conexion': timezone.now()})
                    request.session['user_id'] = user.id
                    return redirect("admin_panel")
                else:
                    messages.error(request, "Clave de seguridad incorrecta para Administrador.")
                    return redirect("login")

            elif user.role == 'mecanico':
                messages.success(request, "Inicio de sesión como Mecánico.")
                Login.objects.update_or_create(user=user, defaults={'ultima_conexion': timezone.now()})
                request.session['user_id'] = user.id
                return redirect("dashboard_mecanico")
            else:
                messages.success(request, "Inicio de sesión como Cliente.")
                Login.objects.update_or_create(user=user, defaults={'ultima_conexion': timezone.now()})
                request.session['user_id'] = user.id
                return redirect("cliente_panel")
        else:
            messages.error(request, "Credenciales incorrectas. Inténtalo de nuevo.")

    return render(request, "login.html")

# Vista para logout (sin restricciones)
def logout_view(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = Registro.objects.get(id=user_id)
        Login.objects.filter(user=user).update(ultima_desconexion=timezone.now())
        del request.session['user_id']
    return redirect("inicio")

# Vista de perfil (acceso solo para clientes)
@role_required("cliente")
def perfil_view(request):
    user_id = request.session.get('user_id')
    user = Registro.objects.get(id=user_id)
    login_data = Login.objects.filter(user=user).first()
    context = {"user": user, "login_data": login_data}
    return render(request, "perfil.html", context)

# Panel de administración (acceso solo para administradores)
@role_required("admin")
def admin_panel(request):
    user_id = request.session.get('user_id')
    user = Registro.objects.get(id=user_id)
    context = {"username": user.username}
    return render(request, "InterfazAdministrador/admin_panel.html", context)

# Agregar mecánico (acceso solo para administradores)
@role_required("admin")
def agregar_mecanico(request):
    user_id = request.session.get('user_id')
    username = Registro.objects.get(id=user_id).username
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        rut = request.POST.get("rut")
        nombre = request.POST.get("nombre")
        apellido = request.POST.get("apellido")
        fecha_nacimiento = request.POST.get("fecha_nacimiento")
        genero = request.POST.get("genero")
        email = request.POST.get("email")
        pin = request.POST.get("pin")

        if Mecanico.objects.filter(rut=rut).exists():
            messages.error(request, "Ya existe un mecánico con ese RUT.")
        elif Mecanico.objects.filter(pin=pin).exists():
            messages.error(request, "Ya existe un mecánico con ese PIN.")
        elif Registro.objects.filter(username=username).exists():
            messages.error(request, "El nombre de usuario ya está en uso.")
        else:
            try:
                with transaction.atomic():
                    registro = Registro.objects.create(
                        username=username,
                        password=password,
                        role="mecanico",
                        registro=timezone.now()
                    )
                    Mecanico.objects.create(
                        rut=rut,
                        nombre=nombre,
                        apellido=apellido,
                        fecha_nacimiento=fecha_nacimiento,
                        genero=genero,
                        email=email,
                        pin=pin,
                        registro=registro
                    )
                messages.success(request, "Mecánico agregado exitosamente.")
                return redirect("listar_mecanicos")
            except Exception as e:
                messages.error(request, f"Error al agregar el mecánico: {e}")
    return render(request, "InterfazAdministrador/agregar_mecanico.html", {"username": username})

# Listar mecánicos (acceso solo para administradores)
@role_required("admin")
def listar_mecanicos(request):
    mecanicos = Mecanico.objects.all()
    return render(request, "InterfazAdministrador/listar_mecanicos.html", {"mecanicos": mecanicos})

# Modificar mecánico (acceso solo para administradores)
@role_required("admin")
def modificar_mecanico(request, mecanico_id):
    mecanico = get_object_or_404(Mecanico, rut=mecanico_id)
    if request.method == "POST":
        mecanico.nombre = request.POST.get("nombre")
        mecanico.apellido = request.POST.get("apellido")
        mecanico.fecha_nacimiento = request.POST.get("fecha_nacimiento")
        mecanico.genero = request.POST.get("genero")
        mecanico.email = request.POST.get("email")
        mecanico.pin = request.POST.get("pin")
        mecanico.save()
        messages.success(request, "Mecánico modificado exitosamente.")
        return redirect("listar_mecanicos")
    return render(request, "InterfazAdministrador/modificar_mecanico.html", {"mecanico": mecanico})

# Eliminar mecánico (acceso solo para administradores)
@role_required("admin")
def eliminar_mecanico(request, mecanico_id):
    mecanico = get_object_or_404(Mecanico, rut=mecanico_id)
    if mecanico.registro:
        registro_id = mecanico.registro.id
        mecanico.delete()
        registro = Registro.objects.filter(id=registro_id).first()
        if registro:
            registro.delete()
            messages.success(request, "Mecánico y su cuenta asociados han sido eliminados exitosamente.")
        else:
            messages.info(request, "Mecánico eliminado exitosamente, pero no se encontró una cuenta asociada para eliminar.")
    else:
        mecanico.delete()
        messages.success(request, "Mecánico eliminado exitosamente, no había cuenta asociada.")
    return redirect("listar_mecanicos")

# Registrar informe (acceso solo para mecánicos)
@role_required("mecanico")
def registrar_informe(request, trabajo_id):
    trabajo = get_object_or_404(Trabajo, id=trabajo_id)
    if request.method == "POST":
        descripcion = request.POST.get("descripcion")
        Informe.objects.create(
            mecanico=trabajo.mecanico,
            trabajo=trabajo,
            descripcion=descripcion,
            fecha_informe=timezone.now()
        )
        messages.success(request, "Informe registrado exitosamente.")
        return redirect("listar_trabajos")
    return render(request, "InterfazAdministrador/registrar_informe.html", {"trabajo": trabajo})

# Consultar histórico de reparaciones (acceso solo para clientes)
@role_required("cliente")
def consultar_historico_reparaciones(request, patente):
    vehiculo = get_object_or_404(Vehiculo, patente=patente)
    reparaciones = Trabajo.objects.filter(vehiculo=vehiculo)
    return render(request, "consultar_historico_reparaciones.html", {"vehiculo": vehiculo, "reparaciones": reparaciones})

# Panel de mecánico (acceso solo para mecánicos)
@role_required("mecanico")
def mecanico_panel(request):
    return render(request, 'InterfazMecanico/mecanico_panel.html')

# Ingresar cliente (acceso solo para mecánicos)

class ClienteForm(ModelForm):
    class Meta:
        model = Cliente
        fields = ['rut', 'nombre', 'apellido', 'fecha_nacimiento', 'genero', 'email', 'telefono', 'direccion']
        widgets = {
            'fecha_nacimiento': DateInput(attrs={'type': 'date', 'placeholder': 'YYYY-MM-DD'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super(ClienteForm, self).__init__(*args, **kwargs)
        self.fields['fecha_nacimiento'].input_formats = ['%Y-%m-%d']
        
@role_required("mecanico")
def ingresar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente ingresado exitosamente.')
            return redirect('listar_cliente')
        else:
            messages.error(request, 'Hubo un error al ingresar el cliente. Por favor, revisa los campos.')
    else:
        form = ClienteForm()

    return render(request, 'InterfazMecanico/ingresar_cliente.html', {'form': form})

# Listar clientes (acceso solo para mecánicos)
@role_required("mecanico")
def listar_clientes(request):
    clientes = Cliente.objects.all().order_by('nombre')
    paginator = Paginator(clientes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, 'InterfazMecanico/listar_clientes.html', context)

# Panel de cliente (acceso solo para clientes)
@role_required("cliente")
def cliente_panel(request):
    user_id = request.session.get('user_id')
    registro = Registro.objects.get(id=user_id, role='cliente')
    cliente = Cliente.objects.filter(registro=registro).first()
    if not cliente or not cliente.datos_completos:
        if request.method == 'POST':
            if not cliente:
                cliente = Cliente(registro=registro)
            cliente.rut = request.POST.get('rut')
            cliente.nombre = request.POST.get('nombre')
            cliente.apellido = request.POST.get('apellido')
            cliente.fecha_nacimiento = request.POST.get('fecha_nacimiento')
            cliente.genero = request.POST.get('genero')
            cliente.email = request.POST.get('email')
            cliente.telefono = request.POST.get('telefono')
            cliente.direccion = request.POST.get('direccion')
            cliente.datos_completos = True
            with transaction.atomic():
                cliente.save()
            messages.success(request, "Datos personales completados exitosamente.")
            return redirect('cliente_panel')
    return render(request, 'InterfazCliente/cliente_panel.html', {
        'username': registro.username,
        'cliente': cliente,
        'mostrar_modal': not cliente or not cliente.datos_completos
    })
