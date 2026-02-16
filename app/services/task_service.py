"""
Task Service - Lógica de negocio para tareas

¿QUÉ ES UN SERVICE?
Es la capa que contiene TODA la lógica de negocio.
Los endpoints (API) solo llaman al service, no hacen lógica directamente.

¿POR QUÉ SEPARAR EN SERVICE?
- Reutilización: La misma lógica se puede usar desde API, CLI, o tests
- Testing: Fácil de testear sin necesitar FastAPI
- Mantenibilidad: Cambios en lógica no afectan los endpoints
- Responsabilidad única: Endpoints = HTTP, Services = Lógica

ARQUITECTURA:
Cliente → Endpoint (HTTP) → Service (Lógica) → Model (BD) → PostgreSQL
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    """
    Servicio de gestión de tareas

    Este es el "AGENTE" que maneja todas las operaciones de tareas.
    Cada método representa una operación de negocio.
    """

    @staticmethod
    def create_task(db: Session, task_data: TaskCreate) -> Task:
        """
        Crear una nueva tarea

        ¿QUÉ HACE?
        1. Recibe datos validados (TaskCreate schema)
        2. Crea objeto Task (model)
        3. Lo guarda en la base de datos
        4. Devuelve la tarea creada con su ID

        PARÁMETROS:
        - db: Sesión de base de datos (inyectada)
        - task_data: Datos validados de la tarea

        RETORNA:
        - Task: Objeto de la tarea creada (con ID, created_at, etc.)

        EJEMPLO:
        task_data = TaskCreate(title="Estudiar", description="FastAPI")
        nueva_tarea = TaskService.create_task(db, task_data)
        print(nueva_tarea.id)  # 1
        """
        # Convertir schema a model
        db_task = Task(
            title=task_data.title, description=task_data.description, completed=task_data.completed
        )

        # Guardar en la base de datos
        db.add(db_task)  # Añadir a la sesión
        db.commit()  # Hacer commit (guardar en BD)
        db.refresh(db_task)  # Recargar para obtener ID y timestamps

        return db_task

    @staticmethod
    def get_task_by_id(db: Session, task_id: int) -> Optional[Task]:
        """
        Obtener una tarea por su ID

        ¿QUÉ HACE?
        Busca una tarea específica en la base de datos.

        PARÁMETROS:
        - db: Sesión de base de datos
        - task_id: ID de la tarea a buscar

        RETORNA:
        - Task si existe
        - None si no existe

        EJEMPLO:
        task = TaskService.get_task_by_id(db, 1)
        if task:
            print(task.title)
        else:
            print("No encontrada")
        """
        return db.query(Task).filter(Task.id == task_id).first()

    @staticmethod
    def get_all_tasks(
        db: Session, skip: int = 0, limit: int = 100, completed: Optional[bool] = None
    ) -> List[Task]:
        """
        Obtener lista de tareas con filtros y paginación

        ¿QUÉ HACE?
        Lista tareas con opciones de:
        - Paginación (skip/limit)
        - Filtro por estado (completed)

        PARÁMETROS:
        - db: Sesión de base de datos
        - skip: Número de registros a saltar (para paginación)
        - limit: Número máximo de registros a devolver
        - completed: Filtrar por estado (None = todas)

        RETORNA:
        - Lista de tareas

        EJEMPLOS:
        # Primeras 10 tareas
        tasks = TaskService.get_all_tasks(db, skip=0, limit=10)

        # Solo completadas
        done = TaskService.get_all_tasks(db, completed=True)

        # Solo pendientes
        pending = TaskService.get_all_tasks(db, completed=False)
        """
        query = db.query(Task)

        # Filtrar por estado si se especifica
        if completed is not None:
            query = query.filter(Task.completed == completed)

        # Aplicar paginación
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_task(db: Session, task_id: int, task_data: TaskUpdate) -> Optional[Task]:
        """
        Actualizar una tarea existente

        ¿QUÉ HACE?
        1. Busca la tarea
        2. Actualiza solo los campos enviados (parcial)
        3. Guarda cambios
        4. Devuelve tarea actualizada

        PARÁMETROS:
        - db: Sesión de base de datos
        - task_id: ID de la tarea a actualizar
        - task_data: Datos a actualizar (solo campos enviados)

        RETORNA:
        - Task actualizada si existe
        - None si no existe

        EJEMPLO:
        # Solo actualizar el estado
        update_data = TaskUpdate(completed=True)
        updated = TaskService.update_task(db, 1, update_data)
        """
        # Buscar la tarea
        db_task = db.query(Task).filter(Task.id == task_id).first()

        if not db_task:
            return None

        # Actualizar solo los campos enviados
        update_dict = task_data.model_dump(exclude_unset=True)
        # exclude_unset=True significa: solo campos que el cliente envió

        for field, value in update_dict.items():
            setattr(db_task, field, value)

        # Guardar cambios
        db.commit()
        db.refresh(db_task)

        return db_task

    @staticmethod
    def delete_task(db: Session, task_id: int) -> bool:
        """
        Eliminar una tarea

        ¿QUÉ HACE?
        1. Busca la tarea
        2. La elimina de la base de datos

        PARÁMETROS:
        - db: Sesión de base de datos
        - task_id: ID de la tarea a eliminar

        RETORNA:
        - True si se eliminó
        - False si no existía

        EJEMPLO:
        eliminada = TaskService.delete_task(db, 1)
        if eliminada:
            print("Tarea eliminada")
        else:
            print("Tarea no encontrada")
        """
        db_task = db.query(Task).filter(Task.id == task_id).first()

        if not db_task:
            return False

        db.delete(db_task)
        db.commit()

        return True

    @staticmethod
    def get_tasks_count(db: Session, completed: Optional[bool] = None) -> int:
        """
        Contar tareas

        ¿PARA QUÉ?
        - Estadísticas
        - Saber cuántas páginas hay (paginación)

        PARÁMETROS:
        - db: Sesión de base de datos
        - completed: Filtrar por estado

        RETORNA:
        - Número de tareas

        EJEMPLO:
        total = TaskService.get_tasks_count(db)
        completadas = TaskService.get_tasks_count(db, completed=True)
        pendientes = TaskService.get_tasks_count(db, completed=False)
        """
        query = db.query(Task)

        if completed is not None:
            query = query.filter(Task.completed == completed)

        return query.count()


# RESUMEN DE OPERACIONES (CRUD):
#
# CREATE: create_task()        → POST   /tasks
# READ:   get_task_by_id()     → GET    /tasks/{id}
#         get_all_tasks()      → GET    /tasks
# UPDATE: update_task()        → PUT    /tasks/{id}
# DELETE: delete_task()        → DELETE /tasks/{id}
#
# EXTRAS:
# - get_tasks_count() → Estadísticas
# - Filtrado por completed
# - Paginación con skip/limit
