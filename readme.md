# 🚀 Task Manager API

API REST profesional para gestión de tareas con autenticación, testing completo y deployment en Kubernetes.

## 📋 Stack Tecnológico

### Backend
- **Python 3.11+**
- **FastAPI** - Framework web moderno y rápido
- **PostgreSQL** - Base de datos relacional
- **Redis** - Caché y sesiones
- **SQLAlchemy** - ORM
- **Alembic** - Migraciones de BD

### Testing
- **pytest** - Framework de testing
- **pytest-cov** - Cobertura de código
- **pytest-asyncio** - Tests asíncronos
- **httpx** - Cliente HTTP para tests

### DevOps
- **Docker** - Containerización
- **Docker Compose** - Orquestación local
- **Kubernetes** - Orquestación producción
- **GitHub Actions** - CI/CD

### Calidad de Código
- **Black** - Formateo automático
- **Ruff** - Linting ultrarrápido
- **mypy** - Type checking
- **pre-commit** - Hooks de Git

## 🎯 Características

- ✅ API REST completa con CRUD
- ✅ Autenticación JWT
- ✅ Validación de datos con Pydantic
- ✅ Tests unitarios y de integración (>80% cobertura)
- ✅ Documentación automática (Swagger/OpenAPI)
- ✅ Containerización con Docker
- ✅ Deploy en Kubernetes
- ✅ CI/CD automatizado
- ✅ Logging y monitoring

## 📁 Estructura del Proyecto
```
task-manager-api/
├── app/
│   ├── api/           # Endpoints de la API
│   ├── core/          # Configuración y utilidades
│   ├── models/        # Modelos de base de datos
│   ├── schemas/       # Schemas Pydantic
│   ├── services/      # Lógica de negocio
│   ├── tests/         # Tests
│   └── main.py        # Punto de entrada
├── docker/            # Dockerfiles
├── k8s/              # Manifests de Kubernetes
├── docs/             # Documentación adicional
├── requirements.txt   # Dependencias
└── README.md         # Este archivo
```

## 🚀 Quick Start

### Prerequisitos
- Python 3.11+
- Docker y Docker Compose
- Git

### Instalación local
```bash
# Clonar el repositorio
git clone <tu-repo>
cd task-manager-api

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
uvicorn app.main:app --reload
```

La API estará disponible en: http://localhost:8000
Documentación: http://localhost:8000/docs

### Con Docker Compose
```bash
# Levantar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down
```

## 🧪 Testing
```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=app --cov-report=html

# Ver reporte de cobertura
open htmlcov/index.html
```

## 📚 Roadmap de Aprendizaje

Este proyecto cubre las habilidades más demandadas en 2026:

- [x] Python moderno (3.11+)
- [x] FastAPI y APIs REST
- [x] Testing profesional
- [x] Docker y containerización
- [ ] Kubernetes básico
- [ ] CI/CD con GitHub Actions
- [ ] Monitoring y observabilidad
- [ ] ML Ops (próxima fase)

## 🤝 Contribuir

Este es un proyecto de aprendizaje. Siéntete libre de:
- Reportar bugs
- Sugerir mejoras
- Hacer fork y experimentar

## 📝 Licencia

MIT License - Proyecto educativo

## 🎓 Recursos

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [pytest Docs](https://docs.pytest.org/)
- [Docker Docs](https://docs.docker.com/)
- [Kubernetes Docs](https://kubernetes.io/docs/)