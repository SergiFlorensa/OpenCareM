"""
Task Schemas - Definición de estructura de datos para tareas

¿QUÉ SON LOS SCHEMAS?
Los schemas son "contratos" que definen cómo deben verse los datos.
Pydantic valida automáticamente que los datos cumplan estas reglas.

¿POR QUÉ USAMOS SCHEMAS?
- Validación automática de datos
- Documentación automática en /docs
- Conversión de tipos automática
- Mensajes de error claros
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TaskBase(BaseModel):
    """
    Schema base con campos comunes

    Heredamos de BaseModel de Pydantic para obtener:
    - Validación automática
    - Serialización JSON
    - Documentación
    """

    title: str = Field(
        ...,  # ... significa "requerido"
        min_length=1,
        max_length=200,
        description="Título de la tarea",
        examples=["Comprar leche"],
    )
    description: Optional[str] = Field(
        None,  # None significa "opcional"
        max_length=1000,
        description="Descripción detallada de la tarea",
        examples=["Comprar 2 litros de leche desnatada en el supermercado"],
    )
    completed: bool = Field(default=False, description="Estado de completitud de la tarea")


class TaskCreate(TaskBase):
    """
    Schema para CREAR una tarea

    ¿CUÁNDO SE USA?
    Cuando el cliente envía datos para crear una nueva tarea.

    EJEMPLO DE JSON:
    {
        "title": "Estudiar FastAPI",
        "description": "Completar tutorial básico",
        "completed": false
    }
    """

    pass  # Hereda todo de TaskBase


class TaskUpdate(BaseModel):
    """
    Schema para ACTUALIZAR una tarea

    ¿POR QUÉ TODO ES OPCIONAL?
    Porque en una actualización, el cliente puede enviar solo
    los campos que quiere cambiar (PATCH).

    EJEMPLO DE JSON:
    {
        "completed": true  # Solo actualiza el estado
    }
    """

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    completed: Optional[bool] = None


class TaskResponse(TaskBase):
    """
    Schema para RESPONDER al cliente

    ¿QUÉ AGREGA?
    - id: Identificador único de la tarea
    - created_at: Fecha de creación
    - updated_at: Fecha de última actualización

    Estos campos NO los envía el cliente, los genera el sistema.

    EJEMPLO DE RESPUESTA:
    {
        "id": 1,
        "title": "Estudiar FastAPI",
        "description": "Completar tutorial básico",
        "completed": false,
        "created_at": "2026-02-05T20:30:00",
        "updated_at": "2026-02-05T20:30:00"
    }
    """

    id: int = Field(..., description="ID único de la tarea")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Fecha de última actualización")

    # Configuración para trabajar con modelos de SQLAlchemy
    model_config = ConfigDict(from_attributes=True)


# RESUMEN:
# - TaskCreate: Lo que el cliente ENVÍA para crear
# - TaskUpdate: Lo que el cliente ENVÍA para actualizar
# - TaskResponse: Lo que el servidor DEVUELVE
