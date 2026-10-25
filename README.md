# Reservia — Sistema Automatizado de Gestión y Reservación de Espacios Recreativos y Salones de Eventos

Sistema web desarrollado con **Python 3.13 + Django + SQL Server**, siguiendo PEP8, SOLID, DRY, KISS
y arquitectura por capas (presentación / aplicación / dominio / datos), correspondiente al
trabajo de graduación de Elvin Eduardo Muralles Melgar.

## Stack tecnológico

- Backend: Python 3.13, Django 5.1, Django ORM
- Frontend: HTML5, CSS3, JavaScript ES6, Bootstrap 5, Bootstrap Icons, Chart.js, FullCalendar
- Base de datos: **Microsoft SQL Server** (administrable desde **SQL Server Management Studio, SSMS**),
  vía el driver `mssql-django` + `pyodbc`
- PDF: ReportLab

## Requisitos previos

- Python 3.13 instalado
- **SQL Server** en ejecución (Express, Developer o full — local o remoto)
- **ODBC Driver 17 (o 18) for SQL Server** instalado en tu máquina
  (Windows normalmente ya lo trae; si no, descárgalo desde el sitio oficial de Microsoft:
  "Microsoft ODBC Driver for SQL Server")
- SQL Server Management Studio (SSMS) para administrar la base de datos gráficamente

## Instalación paso a paso (VS Code)

### 1. Clonar / abrir el proyecto

Abre la carpeta del proyecto en VS Code (`File > Open Folder`).

### 2. Crear y activar entorno virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Crear la base de datos en SQL Server

Desde SQL Server Management Studio (SSMS), conéctate a tu instancia y ejecuta:

```sql
CREATE DATABASE sistema_reservaciones;
```

### 5. Configurar variables de entorno

Copia `.env.example` a `.env` y ajusta tus credenciales de SQL Server:

```bash
copy .env.example .env    # macOS / Linux: cp .env.example .env
```

Edita `.env` según tu tipo de autenticación:

**Autenticación SQL** (usuario y contraseña de SQL Server, p. ej. `sa`):
```
DB_NAME=sistema_reservaciones
DB_HOST=localhost
DB_PORT=1433
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_USER=sa
DB_PASSWORD=tu_password
```

**Autenticación de Windows** (usa tu sesión de Windows, sin usuario/contraseña de SQL):
```
DB_NAME=sistema_reservaciones
DB_HOST=localhost\SQLEXPRESS
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_USER=
DB_PASSWORD=
```

> Si usas SQL Server Express con instancia con nombre, `DB_HOST` suele ser
> `localhost\SQLEXPRESS` y puedes dejar `DB_PORT` vacío.

> Si no tienes el driver ODBC instalado, verás un error como
> `Data source name not found`. Instala "ODBC Driver 17 for SQL Server" desde
> el sitio de Microsoft y vuelve a intentar.

### 6. Aplicar migraciones

```bash
python manage.py migrate
```

### 7. Cargar roles iniciales (opcional pero recomendado)

```bash
python manage.py loaddata roles_iniciales
```

### 8. Crear el usuario Administrador

El registro público (`/cuenta/registro/`) es **solo para clientes**. La cuenta de
Administrador se crea una única vez desde la terminal, con un comando que crea
el superusuario y le asigna el rol "Administrador" en un solo paso:

```bash
python manage.py crear_admin
```

Te pedirá usuario, correo y contraseña (igual que `createsuperuser`), y al
finalizar ya queda con el rol correcto — no hace falta asignarlo manualmente
desde `/admin/`. Desde ahí, el propio Administrador puede crear el resto del
personal (Recepción, Cajero, otros Administradores) desde el módulo **Usuarios**.

### 9. Ejecutar el servidor

```bash
python manage.py runserver
```

Visita **http://127.0.0.1:8000** — serás redirigido al login.

## Estructura del proyecto

```
config/                 Configuración del proyecto (settings, urls raíz)
apps/
  core/                 Modelos base, bitácora, mixins de rol/auditoría, middleware
  autenticacion/        Login, recuperación y cambio de contraseña, bloqueo por intentos
  usuarios/              CRUD usuarios, roles y permisos, bitácora
  clientes/              CRUD clientes, historial, puntos
  espacios/               CRUD espacios/salones, galería de fotos, disponibilidad
  reservaciones/          Crear/editar/cancelar/reprogramar/confirmar, calendario
  pagos/                  Anticipos, pagos parciales/finales, métodos de pago
  fidelizacion/           Acumulación y canje de puntos, catálogo de premios
  reportes/               Generación de reportes en PDF
  dashboard/              KPIs, gráficas e indicadores
templates/               Plantillas base, sidebar, navbar
static/                  CSS y JS propios del sistema
```

## Roles y accesos

| Rol | Cómo se obtiene | Acceso |
|---|---|---|
| **Cliente** | Se registra él mismo en `/cuenta/registro/` | Solo su portal de autoservicio (`Mi cuenta`): ver/solicitar/cancelar sus reservaciones, ver y canjear sus puntos |
| **Administrador** | Se crea una sola vez con `python manage.py crear_admin` | Acceso total, incluida la creación de Recepción/Cajero/otros Administradores |
| **Recepción / Cajero** | Los crea el Administrador desde el módulo **Usuarios** | Módulos operativos (clientes, canchas/salones, reservaciones, pagos, fidelización, reportes, dashboard) |

Un cliente **nunca** puede acceder a los módulos internos (dashboard, listado de
clientes, reportes, etc.) aunque conozca la URL — el sistema lo redirige
automáticamente a su portal. De la misma manera, un cliente solo puede cancelar
sus propias reservaciones y canjear puntos a su propio nombre, nunca a nombre
de otro cliente.

## Funcionalidades incluidas

- Registro público de clientes (`/cuenta/registro/`) con inicio de sesión automático
- Portal de autoservicio del cliente (`Mi cuenta`): solicitar/cancelar sus propias
  reservaciones, ver su historial, canjear puntos — completamente aislado de los
  módulos de personal interno
- Login con bloqueo temporal tras intentos fallidos configurables (`.env`)
- Recuperación y cambio de contraseña
- Gestión de usuarios, roles y permisos (apoyada en el sistema nativo de Django)
- Bitácora de auditoría automática (creación, edición, eliminación, login/logout)
- CRUD de clientes con foto, DPI, historial y puntos
- CRUD de espacios/salones con galería de fotos y control de disponibilidad real
  (bloqueo de reservas duplicadas por solapamiento de horario)
- Reservaciones: crear, editar, confirmar, cancelar, reprogramar, finalizar, con
  historial de cambios de estado y calendario interactivo (FullCalendar)
- Pagos: anticipos, pagos parciales y finales, con cálculo de saldo pendiente
- Fidelización: acumulación automática de puntos al finalizar una reservación,
  catálogo de premios, canje con validación de stock y puntos, configuración editable
- Reportes en PDF: clientes, reservaciones, pagos, espacios, puntos, ingresos
- Dashboard con KPIs y gráficas (espacios más reservados, clientes frecuentes, ventas)
- Seguridad: CSRF, hash de contraseñas, control de sesiones, permisos por rol,
  validaciones cliente/servidor, protección XSS/SQLi vía ORM

## Notas de siguientes fases

Este entregable cubre las fases 1–20 de forma funcional end-to-end sobre SQLite en
pruebas automatizadas internas (creación de reservación, bloqueo de duplicados,
confirmación, pago, finalización, acreditación de puntos, canje y generación de PDF).
Para producción se recomienda:

1. Ajustar `config/settings/production.py` (dominio, `ALLOWED_HOSTS`, HTTPS).
2. Configurar un servidor de correo real para la recuperación de contraseña.
3. Ejecutar `python manage.py collectstatic` antes de desplegar.
4. Revisar y ajustar los roles/permisos según la operación real de la organización.
