# 🧪 TESTING - Guía Rápida de Ejecución

## ✅ Estado Actual

- **77 tests** - Todos pasando ✅
- **89% coverage** - Supera el objetivo del 80% ✅  
- **Base de datos** - Completamente mocked con SQLite en memoria ✅
- **Reporte HTML** - Generado automáticamente ✅

## 🚀 Ejecución Rápida

### Opción 1: Ejecutar todos los tests (Recomendado)

```bash
cd c:\Users\casa\Documents\umg\proyecto-analisis-de-sistemas
python -m pytest tests/ --cov=app --cov-report=html --cov-report=term
```

**Resultado esperado:**
```
77 passed in ~10s
Coverage: 89%
```

### Opción 2: Ver el reporte HTML en el navegador

Después de ejecutar los tests, abre:
```bash
start htmlcov\index.html
```

### Opción 3: Ejecutar solo modelos/auth/api

```bash
# Solo tests de modelos
python -m pytest tests/test_models.py -v

# Solo tests de autenticación
python -m pytest tests/test_auth.py -v

# Solo tests de API
python -m pytest tests/test_api.py -v
```

### Opción 4: Ejecutar un test específico

```bash
python -m pytest tests/test_auth.py::TestAuthLogin::test_login_success -v
```

## 📊 Cobertura Detallada

| Módulo | Coverage | Estado |
|--------|----------|--------|
| `app/extensions.py` | 100% | ✅ Perfecto |
| `app/routes/auth.py` | 99% | ✅ Excelente |
| `app/models.py` | 98% | ✅ Excelente |
| `app/routes/api.py` | 88% | ✅ Muy bueno |
| `app/__init__.py` | 49% | ℹ️ Configuración |
| **TOTAL** | **89%** | ✅ **Excelente** |

## 📋 Tests Incluidos (77 total)

### Modelos (27 tests)
- ✅ User (contraseñas, autenticación)
- ✅ House (viviendas)
- ✅ Resident (residentes)
- ✅ Cistern (cisternas)
- ✅ WaterReading (lecturas de agua)
- ✅ MonthlyConsumption (consumo mensual)
- ✅ Payment (pagos)
- ✅ DistributionPlan (planes de distribución)
- ✅ MaintenanceOrder (órdenes de mantenimiento)
- ✅ Notification (notificaciones)

### Autenticación (15 tests)
- ✅ Registro de usuarios
- ✅ Login exitoso
- ✅ Login con contraseña incorrecta
- ✅ Cuenta bloqueada
- ✅ Token JWT
- ✅ Autorización por roles

### API (35 tests)
- ✅ Health check
- ✅ Dashboard con roles
- ✅ Cisternas (CRUD)
- ✅ Lecturas de sensores
- ✅ Viviendas (CRUD)
- ✅ Residentes (CRUD)
- ✅ Consumo (CRUD)
- ✅ Pagos (CRUD)
- ✅ Delinquencia
- ✅ Planes de distribución (CRUD)
- ✅ Órdenes de mantenimiento (CRUD)
- ✅ Control de autorización

## 🔧 Requisitos Instalados

```bash
pytest==7.4.3
pytest-cov==4.1.0
pytest-mock==3.12.0
Faker==20.1.0
```

## 📁 Estructura de Tests

```
tests/
├── conftest.py          # Fixtures y configuración
├── test_models.py       # Tests de modelos ORM
├── test_auth.py         # Tests de autenticación
└── test_api.py          # Tests de endpoints API
```

## 🎯 Características Principales

### ✅ Mocking Completo de BD
- SQLite en memoria (`:memory:`)
- Totalmente independiente de PostgreSQL
- Rápido y aislado

### ✅ Fixtures Reutilizables
```python
- app           # Aplicación Flask
- client        # Cliente de prueba
- auth_user     # Usuario administrador
- auth_token    # Token JWT válido
- auth_headers  # Headers con autorización
- house/houses  # Viviendas
- cistern       # Cisterna
- resident      # Residente
- payment       # Pago
- Etc.
```

### ✅ Cobertura de Errores
- Validación de entrada
- Autorización por roles
- Integridad de datos
- Casos límite

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: psycopg2"
**Solución:**
```bash
pip install psycopg2-binary
```

### Error: "FAILED - coverage not found"
**Solución:**
```bash
pip install -r requirements-test.txt
```

### Tests lentos
**Solución:** Los tests usan SQLite en memoria, deberían ser rápidos (~10s). Si son lentos, revisa el antivirus.

## 📊 Interpretación del Reporte HTML

Después de ejecutar los tests, abre `htmlcov/index.html`:

1. **Verde (coverage > 80%)**: Bien cubierto
2. **Amarillo (coverage 60-80%)**: Aceptable
3. **Rojo (coverage < 60%)**: Mejorar

Haz click en cualquier archivo para ver qué líneas NO están cubiertas.

## 🔄 Integración Continua

Para CI/CD (GitHub Actions, GitLab CI):

```bash
python -m pytest tests/ \
  --cov=app \
  --cov-report=xml \
  --cov-report=html \
  --junitxml=test-results.xml
```

Esto genera:
- `coverage.xml` → Sonarqube, Codecov
- `htmlcov/` → Reportes visuales
- `test-results.xml` → CI tools

## 📞 Soporte

Consulta [TESTING.md](TESTING.md) para más detalles técnicos.

---

**¡Tu proyecto está completamente testeado con 89% de coverage! 🎉**
