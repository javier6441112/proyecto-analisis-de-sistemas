# Sistema Comunitario de Gestión y Control del Agua

Aplicación web de primer release para el proyecto de gestión del agua comunitaria. Incluye backend en **Python + Flask**, base de datos **PostgreSQL** y frontend en **HTML/CSS/JavaScript vanilla** consumiendo endpoints REST.

## Módulos incluidos

- Autenticación con registro, login, hash de contraseña, JWT y bloqueo por intentos fallidos.
- Dashboard general con nivel de agua, viviendas, habitantes, consumo, pagos, mantenimiento y notificaciones.
- Agua almacenada: configuración de cisterna, edición manual, umbrales y endpoint de sensor.
- Gasto mensual por vivienda: registro, historial y detección simple de consumo anómalo.
- Censo por vivienda: viviendas y habitantes.
- Pagos de mantenimiento: registro por período y consulta de morosidad.
- Distribución semanal: calendarización con validación de traslapes.
- Mantenimiento: órdenes e intervenciones técnicas.
- Notificaciones generadas por eventos del sistema.

## Estructura

```text
comunidad_agua_app/
├── app/
│   ├── routes/
│   │   ├── api.py
│   │   └── auth.py
│   ├── static/
│   │   ├── css/styles.css
│   │   └── js/app.js
│   ├── templates/index.html
│   ├── extensions.py
│   ├── models.py
│   └── __init__.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── run.py
├── .env.example
└── README.md
```

## Ejecución rápida con Docker

1. Levantar PostgreSQL y Flask:

```bash
docker compose up -d --build
```

2. Inicializar tablas y datos demo:

```bash
docker compose exec web flask init-db
```

3. Abrir la aplicación:

```text
http://localhost:5000
```

Usuario demo:

```text
DPI: 1234567890101
Contraseña: Admin123*
```

## Ejecución local sin Docker

1. Crear entorno virtual:

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows
```

2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Crear archivo `.env` desde el ejemplo:

```bash
cp .env.example .env
```

4. Asegurar que PostgreSQL esté levantado y que exista la base de datos configurada en `DATABASE_URL`.

5. Inicializar la base de datos:

```bash
flask --app run.py init-db
```

6. Ejecutar:

```bash
python run.py
```

## Endpoints principales

### Auth

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

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

### Pagos

- `GET /api/payments`
- `POST /api/payments`
- `GET /api/delinquency?period=2026-03&period=2026-04`

### Distribución

- `GET /api/distribution-plans`
- `POST /api/distribution-plans`

### Mantenimiento

- `GET /api/maintenance-orders`
- `POST /api/maintenance-orders`
- `POST /api/maintenance-interventions`

### Notificaciones

- `GET /api/notifications`
- `POST /api/notifications/<id>/read`

## Ejemplo de lectura de sensor

```bash
curl -X POST http://localhost:5000/api/sensor \
  -H "Content-Type: application/json" \
  -d '{"liters": 9500, "observation": "Lectura enviada por sensor"}'
```

## Testing

El proyecto incluye una suite completa de tests con **89% de coverage** que supera el objetivo del 80%.

### Instalar dependencias de tests

```bash
pip install -r requirements-test.txt
```

### Ejecutar todos los tests

```bash
python -m pytest tests/ --cov=app --cov-report=html --cov-report=term
```

**Resultado esperado:** 77 tests pasando en ~10 segundos

### Ejecutar tests específicos

```bash
# Solo tests de modelos
python -m pytest tests/test_models.py -v

# Solo tests de autenticación
python -m pytest tests/test_auth.py -v

# Solo tests de API
python -m pytest tests/test_api.py -v

# Un test individual
python -m pytest tests/test_auth.py::TestAuthLogin::test_login_success -v
```

### Ver reporte de coverage

Después de ejecutar los tests, abre el reporte HTML en el navegador:

```bash
# Windows PowerShell
Start-Process htmlcov\index.html

# Linux/Mac
open htmlcov/index.html

# O abre manualmente: htmlcov/index.html
```

### Cobertura por módulo

- `app/routes/auth.py`: 99% ✅
- `app/models.py`: 98% ✅
- `app/routes/api.py`: 88% ✅
- `app/extensions.py`: 100% ✅
- **Total: 89%** 🎯

### Tests incluidos (77 total)

- **27 tests de modelos:** User, House, Resident, Cistern, WaterReading, MonthlyConsumption, Payment, DistributionPlan, MaintenanceOrder, Notification
- **15 tests de autenticación:** Registro, login, bloqueo de cuenta, tokens JWT, autorización
- **35 tests de API:** CRUD, validaciones, autorización por roles, manejo de errores

### Características de testing

✅ Base de datos mockeada con SQLite en memoria (sin dependencia de PostgreSQL)
✅ Fixtures reutilizables (app, client, auth_user, auth_headers, etc.)
✅ Validaciones completas de entrada y autorización
✅ Detección de anomalías y manejo de errores (400, 401, 403, 404, 409)

Para más detalles, consulta [TESTING.md](TESTING.md) o [TESTING_QUICK.md](TESTING_QUICK.md).

## Notas técnicas

- El frontend es una sola vista renderizada por Flask y consume el backend usando `fetch`.
- El token JWT se guarda en `localStorage` para simplificar el release académico.
- Para producción real se recomienda HTTPS obligatorio, expiración corta de token, refresh token seguro, cookies `HttpOnly`, respaldos automáticos y migraciones controladas.
