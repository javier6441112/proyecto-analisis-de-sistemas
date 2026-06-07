# Sistema Comunitario de Gestion y Control del Agua

Aplicacion web para administrar el abastecimiento de agua en una comunidad. El proyecto integra un backend REST con **Python, Flask y SQLAlchemy**, una base de datos **PostgreSQL** y una interfaz web de una sola vista construida con **HTML, CSS y JavaScript vanilla**.

El sistema permite registrar usuarios, viviendas, habitantes, lecturas de cisterna, consumos mensuales, pagos, planes de distribucion, mantenimiento y notificaciones operativas.

## Caracteristicas principales

- Autenticacion con registro, inicio de sesion, hash de contrasenas, JWT y bloqueo de cuenta tras intentos fallidos.
- Control de acceso por roles: `administrador`, `empleado`, `soporte` y `cliente`.
- Dashboard con nivel de agua, viviendas, habitantes, consumo, pagos, mantenimiento, distribucion y notificaciones.
- Gestion de cisterna con capacidad, nivel actual, umbrales minimo/maximo y lecturas manuales o por sensor.
- Registro mensual de consumo por vivienda con deteccion simple de consumos anomalos.
- Censo comunitario mediante viviendas y residentes.
- Registro de pagos por periodo y consulta de morosidad.
- Calendarizacion semanal de distribucion con validacion de traslapes.
- Ordenes de mantenimiento e intervenciones tecnicas.
- Notificaciones generadas por eventos del sistema.
- Especificacion OpenAPI disponible en `openapi.yml`.
- Suite de pruebas automatizadas con `pytest` y reporte de cobertura.

## Tecnologias

- Python 3
- Flask 3
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-Cors
- PostgreSQL
- PyJWT
- Docker y Docker Compose
- Pytest y pytest-cov

## Estructura del proyecto

```text
proyecto-analisis-de-sistemas/
|-- app/
|   |-- factories/
|   |   `-- model_factory.py
|   |-- repositories/
|   |   |-- cistern_repository.py
|   |   |-- consumption_repository.py
|   |   |-- distribution_repository.py
|   |   |-- house_repository.py
|   |   |-- maintenance_repository.py
|   |   |-- notification_repository.py
|   |   |-- payment_repository.py
|   |   |-- resident_repository.py
|   |   |-- user_repository.py
|   |   `-- water_reading_repository.py
|   |-- routes/
|   |   |-- api.py
|   |   `-- auth.py
|   |-- static/
|   |   |-- css/styles.css
|   |   |-- img/
|   |   `-- js/app.js
|   |-- templates/index.html
|   |-- extensions.py
|   |-- models.py
|   `-- __init__.py
|-- tests/
|   |-- conftest.py
|   |-- test_api.py
|   |-- test_auth.py
|   `-- test_models.py
|-- docker-compose.yml
|-- Dockerfile
|-- openapi.yml
|-- pytest.ini
|-- requirements.txt
|-- requirements-test.txt
|-- run.py
|-- schema.sql
|-- TESTING.md
|-- TESTING_QUICK.md
`-- README.md
```

## Variables de entorno

Crea un archivo `.env` a partir de `.env.example` si ejecutas el proyecto sin Docker.

```env
FLASK_ENV=development
SECRET_KEY=cambia-esta-clave
JWT_SECRET=cambia-esta-clave-jwt
DATABASE_URL=postgresql+psycopg2://agua_user:agua_pass@localhost:5432/agua_db
```

En Docker Compose, estas variables ya estan definidas para que el servicio `web` se conecte al contenedor `db`.

## Ejecucion con Docker

1. Construir y levantar los servicios:

```bash
docker compose up -d --build
```

2. Crear tablas y cargar datos demo:

```bash
docker compose exec web flask init-db
```

3. Abrir la aplicacion:

```text
http://localhost:5000
```

Usuario demo:

```text
DPI: 1234567890101
Contrasena: Admin123*
Rol: administrador
```

## Ejecucion local

1. Crear y activar un entorno virtual:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Crear el archivo `.env`:

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Linux/macOS:

```bash
cp .env.example .env
```

4. Verificar que PostgreSQL este activo y que exista la base de datos indicada en `DATABASE_URL`.

5. Inicializar tablas y datos demo:

```bash
flask --app run.py init-db
```

6. Ejecutar la aplicacion:

```bash
python run.py
```

La aplicacion quedara disponible en:

```text
http://localhost:5000
```

## API REST

Los endpoints protegidos requieren el header:

```text
Authorization: Bearer <token>
```

### Salud

- `GET /api/health`

### Autenticacion

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

### Usuarios

- `GET /api/users`
- `POST /api/users`

### Dashboard

- `GET /api/dashboard`

### Agua almacenada

- `GET /api/cistern`
- `POST /api/cistern`
- `POST /api/sensor`
- `GET /api/water-readings`

### Viviendas y censo

- `GET /api/houses`
- `POST /api/houses`
- `GET /api/residents`
- `POST /api/residents`

### Consumo mensual

- `GET /api/consumptions`
- `POST /api/consumptions`

### Pagos y morosidad

- `GET /api/payments`
- `POST /api/payments`
- `GET /api/delinquency?period=2026-03&period=2026-04`

### Distribucion

- `GET /api/distribution-plans`
- `POST /api/distribution-plans`

### Mantenimiento

- `GET /api/maintenance-orders`
- `POST /api/maintenance-orders`
- `POST /api/maintenance-interventions`

### Notificaciones

- `GET /api/notifications`
- `POST /api/notifications/<id>/read`

La especificacion completa puede consultarse en `openapi.yml`.

## Ejemplos de uso

Iniciar sesion:

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"dpi": "1234567890101", "password": "Admin123*"}'
```

Enviar una lectura de sensor:

```bash
curl -X POST http://localhost:5000/api/sensor \
  -H "Content-Type: application/json" \
  -d '{"liters": 9500, "observation": "Lectura enviada por sensor"}'
```

Consultar dashboard con token:

```bash
curl http://localhost:5000/api/dashboard \
  -H "Authorization: Bearer <token>"
```

## Pruebas

El proyecto incluye pruebas unitarias y de API con una base SQLite en memoria para evitar depender de PostgreSQL durante la ejecucion de tests.

Instalar dependencias de pruebas:

```bash
pip install -r requirements-test.txt
```

Ejecutar toda la suite:

```bash
python -m pytest
```

Ejecutar con cobertura:

```bash
python -m pytest tests/ --cov=app --cov-report=html --cov-report=term
```

Ejecutar archivos especificos:

```bash
python -m pytest tests/test_models.py -v
python -m pytest tests/test_auth.py -v
python -m pytest tests/test_api.py -v
```

Ver el reporte HTML de cobertura:

Windows PowerShell:

```powershell
Start-Process htmlcov\index.html
```

Linux/macOS:

```bash
open htmlcov/index.html
```

Mas informacion de pruebas:

- `TESTING.md`
- `TESTING_QUICK.md`
- `RESULTADO_TESTS.txt`

## Comandos utiles

Reiniciar la base de datos demo en Docker:

```bash
docker compose exec web flask init-db
```

Ver logs de la aplicacion:

```bash
docker compose logs -f web
```

Detener servicios Docker:

```bash
docker compose down
```

Detener servicios y eliminar el volumen de PostgreSQL:

```bash
docker compose down -v
```

## Notas tecnicas

- La aplicacion Flask se crea con el patron `create_app()` en `app/__init__.py`.
- El frontend se sirve desde `app/templates/index.html` y consume la API usando `fetch`.
- El token JWT se guarda en `localStorage` para simplificar el release academico.
- La ruta `/api/sensor` no exige autenticacion para facilitar la integracion con dispositivos externos.
- Para un entorno productivo se recomienda HTTPS obligatorio, secretos seguros, expiracion corta de tokens, cookies `HttpOnly`, respaldos automaticos, migraciones controladas y monitoreo de logs.
