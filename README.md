Liga Timidina
Aplicación web para gestionar una liga semanal de Magic: The Gathering · Commander, con temporadas, jornadas, clasificación, mazos, eventos especiales, administración de partidas y un sistema propio de poderes/penalizaciones denominado “No te flipes”.
El proyecto está dividido en un backend Django + Django REST Framework y un frontend React + Vite.
---
Estado del proyecto
Liga Timidina se encuentra en desarrollo activo.
La aplicación ya dispone de las funciones principales de gestión de liga y está preparada para ejecutarse tanto en local como mediante un despliegue separado:
Frontend: Vercel
Backend/API: Render
Base de datos: PostgreSQL
Entorno local: PostgreSQL o SQLite para desarrollo
URL de la aplicación desplegada:
`https://ligatimidina.vercel.app`
Backend de pruebas:
`https://ligatimidina.onrender.com`
Comprobación de salud del backend:
`https://ligatimidina.onrender.com/health/`
---
Funcionalidades principales
Usuarios
Registro mediante nombre de usuario y contraseña.
Nombre y apellidos privados para administración.
Nombre visible público.
Avatar.
Aceptación de las normas de la liga.
Activación y validación administrativa de nuevas cuentas.
Cambio de contraseña.
Perfil público de jugadores.
Roles de usuario, administrador y superadministrador.
El superadministrador puede promover otros usuarios a administrador.
Temporadas y jornadas
Creación y gestión de temporadas.
Fechas de inicio y fin.
Generación de jornadas.
Jornada actual.
Cierre de jornadas.
Histórico por temporada.
Finalización de temporada manteniendo el histórico.
Clasificación acumulada con:
puntos;
partidas;
victorias;
eliminaciones;
semanas jugadas;
estados especiales.
Partidas
Registro administrativo de partidas Commander.
Asociación de jugadores y mazos.
Posición inicial y final.
Eliminaciones.
Primera eliminación.
Concesiones.
Puntos extraordinarios con motivo obligatorio.
Cierre de partida.
Recalculo de puntuación.
Protección frente a modificaciones de partidas cerradas.
Eliminación histórica administrativa con reconstrucción de datos dependientes cuando sea necesario.
Límite de partidas por jornada según la configuración de la liga.
Eventos semanales
Cada jornada puede disponer de un evento especial con:
nombre;
descripción;
normas;
puntuación adicional.
La bonificación del evento semanal solo puede concederse una vez por jugador y jornada, aunque el jugador dispute varias partidas esa misma semana.
Entre los tipos de evento admitidos se encuentran, por ejemplo:
Planechase;
Archenemy;
2v2;
manos abiertas;
restricciones de ataque;
cambios de vidas iniciales;
Treasure inicial;
tierras básicas adicionales;
reglas de tiempo;
otros modificadores definidos por administración.
Mazos y DeckCheck
Registro de mazos Commander.
Comandante.
Descripción.
Lista de cartas.
Marcado de mazo original.
Estado activo/inactivo.
Integración con información de DeckCheck.
Visualización del bracket del mazo.
Perfil público con los mazos del jugador.
Referencia visual de los diferentes Commander Brackets.
Normas específicas de Bracket 3 · Upgraded dentro de la aplicación.
Carpetas de cartas
Cada jugador puede disponer de una carpeta pública para enseñar cartas disponibles.
Incluye:
hasta 100 entradas de cartas por usuario;
imagen de carta;
cantidad;
estado;
FOIL;
precio de referencia;
enlace de referencia;
selección múltiple;
eliminación múltiple con confirmación;
visualización pública de carpetas de otros jugadores.
La Liga Timidina no actúa como intermediaria en pagos o compraventas realizadas entre jugadores.
“No te flipes”
“No te flipes” es un sistema especial de la liga.
Un No te flipes es un poder, no una penalización asignada directamente.
Flujo:
Administración concede un poder a un jugador.
El jugador ve que tiene el poder disponible.
El titular elige a otro jugador como objetivo.
El titular no puede elegirse a sí mismo.
Al pulsar Lanzar, el backend selecciona aleatoriamente la penalización.
La selección respeta los pesos configurados.
La penalización se asigna al jugador objetivo.
El poder queda consumido.
La ruleta del frontend representa visualmente el resultado decidido por el backend.
Antes del lanzamiento, el titular no conoce la penalización que contiene el poder.
Después del lanzamiento puede conocer el resultado que acaba de enviar.
El jugador afectado puede consultar su propia penalización y administración puede auditar todas.
Handicaps y penalizaciones
El sistema admite categorías configurables:
leve;
media;
grave.
Cada definición puede incluir:
nombre;
descripción;
categoría;
peso de aparición;
partidas de gracia;
puntos de penalización;
parámetros de reversión;
estado activo/inactivo.
Los pesos permiten controlar la probabilidad relativa de aparición.
El sistema conserva snapshots históricos para evitar que una modificación posterior de una definición cambie el significado de penalizaciones ya asignadas.
Mensajería
Conversaciones entre jugador y administración.
Respuestas encadenadas.
Estado leído/no leído.
Apertura y cierre de conversaciones.
Eliminación administrativa.
Medidas anti-spam mediante throttling de API.
Premios y configuración de liga
La administración puede configurar:
límite de partidas;
aportaciones;
porcentaje destinado al bote;
enlace de pago;
avisos de convivencia;
reparto de premios.
El reparto previsto del bote mensual es:
1.º: 50 %
2.º: 30 %
3.º: 20 %
Los premios se plantean en material relacionado con Magic: The Gathering proporcionado por la tienda colaboradora.
---
Normas permanentes de la liga
Horario
Las partidas oficiales de Liga Timidina se juegan:
Día	Mañana	Tarde
Martes	11:30	18:30
Jueves	11:30	18:30
Viernes	11:30	18:30
Mazos
La liga se juega con intención de Commander Bracket 3 · Upgraded.
El mazo debe estar registrado previamente antes de utilizarse.
No se permiten proxies de ningún tipo.
Utilizar una carta que no figure en la lista registrada del mazo se considera trampa y puede conllevar sanciones.
Se permiten hasta 3 Game Changers dentro de las restricciones definidas para Bracket 3.
No se permite negación masiva de tierras.
No se permiten cierres mediante combos intencionados de dos cartas durante el early game en los supuestos restringidos por las normas de la liga.
Los jugadores deben comunicar de buena fe los elementos relevantes del mazo que puedan modificar las expectativas de la mesa.
Convivencia
No se toleran:
insultos;
amenazas;
acoso;
discriminación;
trampas;
manipulación de resultados;
suplantación;
hostigamiento mediante la aplicación.
Las conductas graves o reiteradas pueden implicar advertencias, suspensión o expulsión de la liga.
---
Stack tecnológico
Backend
Python 3.13
Django 6.1
Django REST Framework
PostgreSQL
psycopg
Gunicorn
WhiteNoise
dj-database-url
Pillow
Requests
python-dotenv
Frontend
React 19
Vite 8
React Router
JavaScript / JSX
CSS
Producción
Vercel para el frontend.
Render para Django/Gunicorn.
PostgreSQL administrado para los datos.
---
Estructura del proyecto
```text
ligatimidina/
│
├── backend/
│   ├── accounts/       # Usuarios, registro, perfiles y mensajería
│   ├── binders/        # Carpetas públicas de cartas
│   ├── config/         # Configuración Django
│   ├── decks/          # Mazos y análisis DeckCheck
│   ├── events/         # Eventos semanales
│   ├── handicaps/      # No te flipes, handicaps y pesos
│   ├── league/         # Temporadas, jornadas, clasificación y ajustes
│   ├── matches/        # Partidas, participantes y eliminaciones
│   ├── penalties/      # Penalizaciones
│   ├── watches/        # Funciones auxiliares de seguimiento
│   ├── manage.py
│   └── media/
│
├── frontend/
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
│
├── requirements.txt
├── .python-version
└── README.md
```
---
Instalación local
Requisitos
Necesitas tener instalado:
Python 3.13
Node.js
npm
Git
PostgreSQL es recomendable, aunque para desarrollo puede utilizarse SQLite.
---
1. Clonar el repositorio
```bat
git clone TU_REPOSITORIO
cd ligatimidina
```
---
2. Crear el entorno virtual
En Windows CMD:
```bat
python -m venv backend\.venv
call backend\.venv\Scripts\activate.bat
```
Instalar las dependencias:
```bat
pip install -r requirements.txt
```
---
3. Variables de entorno del backend
Crea:
```text
backend\.env
```
Ejemplo para desarrollo local con SQLite:
```env
DJANGO_SECRET_KEY=cambia-esta-clave-en-tu-equipo
DJANGO_DEBUG=True
DJANGO_USE_SQLITE=True

DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```
Nunca subas el archivo `.env` real al repositorio.
Para PostgreSQL también puede utilizarse:
```env
DJANGO_USE_SQLITE=False
DATABASE_URL=postgresql://USUARIO:PASSWORD@HOST:5432/BASE_DE_DATOS
```
Alternativamente, el backend admite las variables:
```env
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
```
---
4. Migraciones
Desde la raíz:
```bat
python backend\manage.py migrate
```
Crear administrador:
```bat
python backend\manage.py createsuperuser
```
---
5. Iniciar backend
```bat
python backend\manage.py runserver
```
Backend local:
```text
http://127.0.0.1:8000
```
Panel Django:
```text
http://127.0.0.1:8000/admin/
```
Health check:
```text
http://127.0.0.1:8000/health/
```
---
6. Instalar frontend
En otra consola:
```bat
cd frontend
npm install
```
Ejecutar:
```bat
npm run dev
```
Frontend local:
```text
http://localhost:5173
```
---
Comandos útiles
Backend
Comprobar configuración:
```bat
python backend\manage.py check
```
Comprobar migraciones pendientes:
```bat
python backend\manage.py makemigrations --check
```
Aplicar migraciones:
```bat
python backend\manage.py migrate
```
Crear administrador:
```bat
python backend\manage.py createsuperuser
```
Ejecutar todos los tests:
```bat
python backend\manage.py test
```
O por aplicación:
```bat
python backend\manage.py test accounts
python backend\manage.py test binders
python backend\manage.py test decks
python backend\manage.py test events
python backend\manage.py test handicaps
python backend\manage.py test league
python backend\manage.py test matches
python backend\manage.py test penalties
python backend\manage.py test watches
```
Frontend
```bat
cd frontend
npm run dev
npm run lint
npm run build
```
---
API
La API está situada bajo:
```text
/api/
```
Principales grupos:
```text
/api/accounts/
/api/binders/
/api/decks/
/api/events/
/api/handicaps/
/api/league/
/api/matches/
/api/penalties/
/api/watches/
```
La autenticación utilizada por la aplicación es mediante sesión Django, cookies y protección CSRF.
Entre los endpoints relevantes se encuentran:
```text
GET  /api/accounts/me/
GET  /api/accounts/players/

GET  /api/league/standings/
GET  /api/league/current-week/

GET  /api/handicaps/categories/
GET  /api/handicaps/definitions/
GET  /api/handicaps/grants/mine/

GET  /api/binders/
```
Los permisos y la privacidad se validan en backend, no solamente ocultando información desde React.
---
Seguridad
La configuración incluye:
protección CSRF;
cookies de sesión HttpOnly;
cookies Secure en producción;
SameSite;
Content Security Policy;
`X-Frame-Options: DENY`;
protección MIME sniffing;
política de referrer;
throttling de API;
límites de carga;
validación de archivos de avatar;
WhiteNoise para estáticos;
soporte HTTPS detrás de proxy;
HSTS configurable.
Variables relacionadas con producción:
```env
DJANGO_DEBUG=False
DJANGO_CSRF_TRUSTED_ORIGINS=https://ligatimidina.vercel.app

DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True

DJANGO_SECURE_SSL_REDIRECT=False
DJANGO_SECURE_HSTS_SECONDS=3600
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=False
DJANGO_SECURE_HSTS_PRELOAD=False
```
La redirección HTTPS puede delegarse en el proxy/plataforma de despliegue.
---
Correo
En desarrollo, Django utiliza el backend de correo por consola.
En producción pueden configurarse:
```env
DJANGO_DEFAULT_FROM_EMAIL=
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_USE_TLS=True
SMTP_TIMEOUT=10
```
Nunca almacenes contraseñas SMTP en Git.
---
Despliegue
Backend en Render
Build command:
```text
pip install -r requirements.txt && python backend/manage.py collectstatic --noinput && python backend/manage.py migrate
```
Start command:
```text
gunicorn --chdir backend config.wsgi:application --bind 0.0.0.0:$PORT
```
Health check:
```text
/health/
```
Variables principales:
```text
DATABASE_URL
DJANGO_SECRET_KEY
DJANGO_DEBUG=False
DJANGO_USE_SQLITE=False
DJANGO_CSRF_TRUSTED_ORIGINS=https://ligatimidina.vercel.app
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
```
No compartas nunca públicamente:
`DATABASE_URL`;
contraseñas de PostgreSQL;
`DJANGO_SECRET_KEY`;
`.env`;
credenciales SMTP.
---
Frontend en Vercel
Configura como Root Directory:
```text
frontend
```
Build:
```text
npm run build
```
El frontend utiliza rutas `/api/...`.
En el despliegue actual, Vercel reescribe las solicitudes de API hacia Render.
Regla:
```text
Request Path:
 /api/:path*

Rewrite:
 https://ligatimidina.onrender.com/api/$1/
```
La barra final del destino es importante para evitar un bucle de redirecciones con las rutas Django que terminan en `/`.
---
Archivos multimedia
Los avatares utilizan actualmente `MEDIA_ROOT` y almacenamiento de archivos del servidor.
Para un despliegue permanente se recomienda utilizar almacenamiento externo compatible con producción para evitar depender del disco efímero del servidor.
Ejemplos de soluciones futuras:
Amazon S3;
Cloudflare R2;
Cloudinary;
otro almacenamiento de objetos compatible.
---
Flujo de registro
El usuario rellena el formulario.
Acepta las normas.
Django crea la cuenta en estado pendiente.
Administración revisa la solicitud.
Administración activa la cuenta.
El jugador puede iniciar sesión.
El nombre y los apellidos reales son datos de administración y no deben publicarse en el perfil del jugador.
---
Administración
La administración tiene autoridad para:
validar usuarios;
gestionar temporadas;
generar y cerrar jornadas;
crear eventos;
registrar partidas;
cerrar partidas;
corregir resultados;
conceder No te flipes;
gestionar definiciones y pesos;
consultar penalizaciones;
gestionar premios;
responder mensajes;
realizar correcciones históricas.
Las acciones sensibles deben mantenerse protegidas por permisos de backend.
---
Privacidad del sistema “No te flipes”
Regla crítica del proyecto:
el titular sabe que dispone de un poder;
puede elegir a quién lanzarlo;
no puede conocer de antemano la penalización;
la penalización se sortea únicamente cuando se lanza;
el backend decide el resultado;
la ruleta no decide el resultado;
el jugador afectado puede consultar su penalización;
administración puede auditar todos los datos;
otros jugadores no deben recibir información sensible de una penalización ajena.
---
Mejoras y tareas pendientes
Las siguientes mejoras forman parte del trabajo previsto y no deben considerarse terminadas hasta que estén implementadas y probadas.
Gestión de participación y fechas
La fecha asociada a una aportación debe ser opcional.
Un jugador sin aportación de pago no necesita fecha de caducidad.
El vencimiento de una aportación no debe desactivar la cuenta.
Al vencer, el jugador debe continuar activo con las condiciones generales de participación.
Corregir el formulario de administración si actualmente obliga a introducir una fecha.
Rendimiento inicial
Reducir el tiempo de espera al aceptar cookies o volver a entrar.
Permitir que el usuario vea y rellene el login mientras se realizan en segundo plano las comprobaciones iniciales.
Evitar bloquear la interfaz por la carga del estado completo de la aplicación.
Revisar la latencia producida por el arranque del backend en el entorno de despliegue.
Registro de backend
Incorporar un sistema de logging persistente/configurable.
Generar un `log.txt` en entorno local.
Registrar acciones relevantes en tiempo real:
login;
registro;
errores;
acciones administrativas;
partidas;
eventos;
No te flipes;
cambios sensibles.
Evitar guardar contraseñas, tokens, secretos o datos sensibles dentro de los logs.
En producción, preferir logs de plataforma o almacenamiento persistente frente a depender exclusivamente de un archivo local.
Registro de nuevos usuarios
Tras completar correctamente un registro:
mostrar el mensaje de cuenta pendiente de validación;
abandonar el formulario de alta;
regresar automáticamente a la pantalla de login.
Hitos para obtener un “No te flipes”
Se prevé incorporar un catálogo configurable de hitos de partida que pueda justificar la concesión de un No te flipes.
Ejemplos iniciales:
controlar 40 o más permanentes simultáneamente;
hacer 100 o más puntos de daño a un único oponente de una vez;
ganar una partida con 100 o más vidas;
alcanzar otros hitos extraordinarios definidos por administración.
El sistema deberá registrar el motivo del hito y permitir a administración decidir si la recompensa se concede automáticamente o requiere validación.
---
Colaboración
Liga Timidina incluye referencias a:
Magic: The Gathering;
DeckCheck;
A Dado y Pluma · Triana.
Los nombres, marcas y recursos de terceros pertenecen a sus respectivos titulares.
---
Desarrollo
Antes de subir cambios:
```bat
git status
python backend\manage.py check
python backend\manage.py makemigrations --check
```
Frontend:
```bat
cd frontend
npm run lint
npm run build
cd ..
```
Después:
```bat
git add .
git commit -m "Describe aqui el cambio realizado"
git push origin main
```
El despliegue conectado a Git puede actualizar automáticamente Vercel y Render tras el `push`.
---
Importante
No subas al repositorio:
```text
backend/.env
backend/.venv/
frontend/node_modules/
frontend/dist/
backend/staticfiles/
__pycache__/
*.pyc
```
Tampoco deben versionarse bases de datos locales, copias de seguridad ni archivos que contengan credenciales.
---
Liga Timidina
Commander semanal, clasificación, eventos y caos controlado.
