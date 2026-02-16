"""
Task Model - Representación de la tabla 'tasks' en la base de datos

¿QUÉ ES UN MODEL?
Un model es una clase Python que representa una TABLA en la base de datos.
SQLAlchemy traduce esta clase a SQL automáticamente.

¿POR QUÉ USAR MODELS?
- No escribir SQL manualmente
- Validación a nivel de base de datos
- Relaciones entre tablas fáciles
- Migrations automáticas con Alembic
"""
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class Task(Base):
    """
    Model de Tarea

    ¿QUÉ REPRESENTA?
    Esta clase se convierte en una tabla llamada 'tasks' en PostgreSQL

    ESTRUCTURA EN SQL:
    CREATE TABLE tasks (
        id SERIAL PRIMARY KEY,
        title VARCHAR(200) NOT NULL,
        description TEXT,
        completed BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    """

    # Nombre de la tabla en la base de datos
    __tablename__ = "tasks"

    # Columnas de la tabla
    id = Column(
        Integer,
        primary_key=True,  # Clave primaria (único, auto-incrementable)
        index=True,  # Crear índice para búsquedas rápidas
        comment="ID único de la tarea",
    )

    title = Column(
        String(200),  # VARCHAR(200) en SQL
        nullable=False,  # NOT NULL - campo obligatorio
        index=True,  # Índice para búsquedas por título
        comment="Título de la tarea",
    )

    description = Column(
        Text,  # TEXT en SQL (sin límite de caracteres)
        nullable=True,  # Puede ser NULL - campo opcional
        comment="Descripción detallada de la tarea",
    )

    completed = Column(
        Boolean,  # BOOLEAN en SQL
        default=False,  # Valor por defecto
        nullable=False,
        index=True,  # Índice para filtrar por completadas/pendientes
        comment="Estado de completitud",
    )

    created_at = Column(
        DateTime(timezone=True),  # TIMESTAMP WITH TIME ZONE en SQL
        server_default=func.now(),  # PostgreSQL NOW() automático
        nullable=False,
        comment="Fecha y hora de creación",
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),  # Se actualiza automáticamente al modificar
        nullable=False,
        comment="Fecha y hora de última actualización",
    )

    def __repr__(self):
        """
        Representación legible del objeto

        ¿PARA QUÉ?
        Cuando imprimes un objeto Task, verás algo útil en lugar de
        <Task object at 0x...>

        EJEMPLO:
        print(task)  # Output: Task(id=1, title='Estudiar FastAPI')
        """
        return f"Task(id={self.id}, title='{self.title}', " f"completed={self.completed})"


# RESUMEN DE DIFERENCIAS: Schema vs Model
#
# SCHEMA (Pydantic):
# - Validación de datos de entrada/salida
# - Se usa en los endpoints de la API
# - Define el "contrato" con el cliente
# - NO interactúa con la base de datos
#
# MODEL (SQLAlchemy):
# - Representación de tabla en base de datos
# - Se usa para guardar/leer datos
# - Define la estructura de la tabla
# - SÍ interactúa con PostgreSQL
#
# FLUJO:
# Cliente → Schema (validación) → Service → Model (BD) →
# Schema (respuesta) → Cliente
