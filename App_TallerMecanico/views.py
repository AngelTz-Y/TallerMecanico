from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from .models import *
from django.core.paginator import Paginator
from django.forms import ModelForm,DateInput


# Vista para la página de inicio
def inicio_view(request):
    return render(request, "inicio.html")

def registro_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("repassword")  # Asegúrate de usar "repassword" si es el nombre en el HTML
        role = request.POST.get("role", "cliente")  # Asigna "cliente" si el rol no se proporciona

        # Verifica si el nombre de usuario ya existe
        if Registro.objects.filter(username=username).exists():
            messages.error(request, "El nombre de usuario ya está en uso.")
            return redirect("registro")

        # Verifica que las contraseñas coincidan
        if password != confirm_password:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect("registro")

        # Intenta guardar el registro
        try:
            registro = Registro(username=username, password=password, role=role)
            registro.save()
            messages.success(request, "Registro exitoso. Puedes iniciar sesión.")
            return redirect("login")
        except Exception as e:
            # En caso de error, imprime el error en consola y muestra un mensaje de error
            print("Error al guardar el registro:", e)
            messages.error(request, "Ocurrió un error al intentar registrarte. Inténtalo nuevamente.")
            return redirect("registro")

    return render(request, "registro.html")

# Vista de inicio de sesión
# Vista de inicio de sesión sin encriptación de contraseña
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Registro, Administrador, Login
from django.utils import timezone

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        admin_key = request.POST.get("admin_key")  # Clave de seguridad solo para el administrador

        # Buscar el usuario en el modelo Registro
        user = Registro.objects.filter(username=username, password=password).first()

        if user:
            # Si el username es "admin" y el rol es "admin", verifica la clave de seguridad
            if user.role == 'admin' and username == 'admin':
                # Busca el administrador con username "admin"
                administrador = Administrador.objects.filter(nombre="Admin").first()  # O el campo que tenga el nombre correspondiente

                # Verifica si el administrador existe y que la clave coincida
                if administrador and administrador.clave_unica == admin_key:
                    # Clave de seguridad correcta
                    messages.success(request, "Inicio de sesión como Administrador.")
                    Login.objects.update_or_create(user=user, defaults={'ultima_conexion': timezone.now()})
                    request.session['user_id'] = user.id  # Guarda el ID de usuario en la sesión
                    return redirect("admin_panel")
                else:
                    messages.error(request, "Clave de seguridad incorrecta para Administrador.")
                    return redirect("login")

            # Si el usuario es un mecánico o cliente, procede sin la clave de seguridad adicional
            elif user.role == 'mecanico':
                messages.success(request, "Inicio de sesión como Mecánico.")
                Login.objects.update_or_create(user=user, defaults={'ultima_conexion': timezone.now()})
                request.session['user_id'] = user.id  # Guarda el ID de usuario en la sesión
                return redirect("dashboard_mecanico")
            else:
                messages.success(request, "Inicio de sesión como Cliente.")
                Login.objects.update_or_create(user=user, defaults={'ultima_conexion': timezone.now()})
                request.session['user_id'] = user.id  # Guarda el ID de usuario en la sesión
                return redirect("cliente_panel")
        else:
            messages.error(request, "Credenciales incorrectas. Inténtalo de nuevo.")

    return render(request, "login.html")

# Vista para logout de usuario
def logout_view(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = Registro.objects.get(id=user_id)
        # Actualiza la última desconexión
        Login.objects.filter(user=user).update(ultima_desconexion=timezone.now())
        del request.session['user_id']  # Elimina al usuario de la sesión
    return redirect("inicio")

# Vista para perfil de usuario
def perfil_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect("login")  # Redirige al login si no está autenticado
    
    user = Registro.objects.get(id=user_id)
    login_data = Login.objects.filter(user=user).first()

    context = {
        "user": user,
        "login_data": login_data
    }
    return render(request, "perfil.html", context)


def admin_panel(request):
    # Obtenemos el ID del usuario de la sesión
    user_id = request.session.get('user_id')
    if user_id:
        # Obtenemos el usuario de la base de datos usando el modelo Registro
        try:
            user = Registro.objects.get(id=user_id)
            context = {"username": user.username}
            return render(request, "InterfazAdministrador/admin_panel.html", context)
        except Registro.DoesNotExist:
            # Si el usuario no existe, redirige a la página de inicio de sesión
            return redirect("login")
    else:
        # Si no hay usuario en la sesión, redirige a la página de inicio de sesión
        return redirect("login")
    
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Registro, Mecanico
from django.utils import timezone
from django.db import transaction  # Importar para asegurar transacción atómica

## Vista para agregar un mecánico
def agregar_mecanico(request):
    # Obtener el user_id desde la sesión
    user_id = request.session.get('user_id')
    username = None

    # Si el usuario está autenticado, obtener su nombre de usuario
    if user_id:
        username = Registro.objects.get(id=user_id).username

    if request.method == "POST":
        # Obtener datos del formulario
        username = request.POST.get("username")
        password = request.POST.get("password")
        rut = request.POST.get("rut")
        nombre = request.POST.get("nombre")
        apellido = request.POST.get("apellido")
        fecha_nacimiento = request.POST.get("fecha_nacimiento")
        genero = request.POST.get("genero")
        email = request.POST.get("email")
        pin = request.POST.get("pin")

        # Validaciones previas para evitar duplicados
        if Mecanico.objects.filter(rut=rut).exists():
            messages.error(request, "Ya existe un mecánico con ese RUT.")
        elif Mecanico.objects.filter(pin=pin).exists():
            messages.error(request, "Ya existe un mecánico con ese PIN.")
        elif Registro.objects.filter(username=username).exists():
            messages.error(request, "El nombre de usuario ya está en uso.")
        else:
            try:
                # Iniciar una transacción atómica
                with transaction.atomic():
                    # Crear el usuario en la tabla `Registro`
                    registro = Registro.objects.create(
                        username=username,
                        password=password,  # Sin encriptación; para encriptarlo usa `make_password(password)`
                        role="mecanico",
                        registro=timezone.now()
                    )

                    # Crear el mecánico en la tabla `Mecanico` y asociarlo al `Registro`
                    Mecanico.objects.create(
                        rut=rut,
                        nombre=nombre,
                        apellido=apellido,
                        fecha_nacimiento=fecha_nacimiento,
                        genero=genero,
                        email=email,
                        pin=pin,
                        registro=registro  # Asociar el registro al mecánico
                    )

                # Mensaje de éxito y redirección
                messages.success(request, "Mecánico agregado exitosamente.")
                return redirect("listar_mecanicos")

            except Exception as e:
                # Captura cualquier excepción y muestra el error
                messages.error(request, f"Error al agregar el mecánico: {e}")

    # Pasar el `username` al contexto de la plantilla
    return render(request, "InterfazAdministrador/agregar_mecanico.html", {"username": username})

# Vista para listar mecánicos
def listar_mecanicos(request):
    mecanicos = Mecanico.objects.all()
    return render(request, "InterfazAdministrador/listar_mecanicos.html", {"mecanicos": mecanicos})

# Vista para modificar un mecánico
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

def eliminar_mecanico(request, mecanico_id):
    try:
        # Obtener el mecánico por el rut (o identificador único)
        mecanico = get_object_or_404(Mecanico, rut=mecanico_id)
        
        # Verificar si el mecánico tiene una cuenta asociada en Registro
        if mecanico.registro:
            registro_id = mecanico.registro.id
            mecanico.delete()  # Elimina primero el mecánico
            
            # Luego, intenta eliminar el registro asociado
            registro = Registro.objects.filter(id=registro_id).first()
            if registro:
                registro.delete()
                messages.success(request, "Mecánico y su cuenta asociados han sido eliminados exitosamente.")
            else:
                messages.info(request, "Mecánico eliminado exitosamente, pero no se encontró una cuenta asociada para eliminar.")
        else:
            # Si no tiene cuenta asociada, solo elimina el mecánico
            mecanico.delete()
            messages.success(request, "Mecánico eliminado exitosamente, no había cuenta asociada.")
    
    except Exception as e:
        # Si ocurre un error, registra el mensaje
        messages.error(request, f"Error al eliminar el mecánico: {str(e)}")

    # Redireccionar a la lista de mecánicos
    return redirect("listar_mecanicos")

    return redirect("listar_mecanicos")
# Vista para registrar un informe de reparación
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

# Vista para consultar el histórico de reparaciones de un vehículo
def consultar_historico_reparaciones(request, patente):
    vehiculo = get_object_or_404(Vehiculo, patente=patente)
    reparaciones = Trabajo.objects.filter(vehiculo=vehiculo)
    return render(request, "consultar_historico_reparaciones.html", {"vehiculo": vehiculo, "reparaciones": reparaciones})


def mecanico_panel(request):
    return render(request, 'InterfazMecanico/mecanico_panel.html')


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


def listar_clientes(request):
    # Obtener todos los clientes
    clientes = Cliente.objects.all().order_by('nombre')
    # Paginador para mostrar 10 clientes por página
    paginator = Paginator(clientes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'InterfazMecanico/listar_clientes.html', context)


def cliente_panel(request):
    return render(request, 'InterfazCliente/cliente_panel.html')