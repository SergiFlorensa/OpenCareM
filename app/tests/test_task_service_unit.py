from app.schemas.task import TaskCreate, TaskUpdate
from app.services.task_service import TaskService


def test_task_service_create_and_get_by_id(db_session):
    """Create a task through the service and fetch it again by id."""
    created = TaskService.create_task(
        db=db_session,
        task_data=TaskCreate(
            title="Unit task",
            description="Created from unit test",
            completed=False,
        ),
    )
    assert created.id is not None
    assert created.title == "Unit task"

    loaded = TaskService.get_task_by_id(db=db_session, task_id=created.id)
    assert loaded is not None
    assert loaded.id == created.id
    assert loaded.description == "Created from unit test"


def test_task_service_get_all_with_filter_and_pagination(db_session):
    """Return tasks with completed filter and respect skip/limit pagination."""
    TaskService.create_task(
        db=db_session,
        task_data=TaskCreate(title="Pending 1", description=None, completed=False),
    )
    TaskService.create_task(
        db=db_session,
        task_data=TaskCreate(title="Done 1", description=None, completed=True),
    )
    TaskService.create_task(
        db=db_session,
        task_data=TaskCreate(title="Pending 2", description=None, completed=False),
    )

    completed_items = TaskService.get_all_tasks(db=db_session, completed=True)
    assert len(completed_items) == 1
    assert completed_items[0].title == "Done 1"

    paged_items = TaskService.get_all_tasks(db=db_session, skip=1, limit=1)
    assert len(paged_items) == 1


def test_task_service_update_existing_task(db_session):
    """Update only provided fields and keep other values unchanged."""
    created = TaskService.create_task(
        db=db_session,
        task_data=TaskCreate(title="Before", description="Old description", completed=False),
    )
    assert created.id is not None

    updated = TaskService.update_task(
        db=db_session,
        task_id=created.id,
        task_data=TaskUpdate(title="After", completed=True),
    )
    assert updated is not None
    assert updated.title == "After"
    assert updated.completed is True
    assert updated.description == "Old description"


def test_task_service_update_missing_task_returns_none(db_session):
    """Return None when trying to update a task that does not exist."""
    updated = TaskService.update_task(
        db=db_session,
        task_id=9999,
        task_data=TaskUpdate(title="No task"),
    )
    assert updated is None


def test_task_service_delete_and_delete_missing(db_session):
    """Delete existing task and return False for second delete attempt."""
    created = TaskService.create_task(
        db=db_session,
        task_data=TaskCreate(title="Delete me", description=None, completed=False),
    )
    assert created.id is not None

    deleted = TaskService.delete_task(db=db_session, task_id=created.id)
    assert deleted is True

    deleted_again = TaskService.delete_task(db=db_session, task_id=created.id)
    assert deleted_again is False


def test_task_service_count_total_completed_pending(db_session):
    """Count all tasks and by completed status."""
    TaskService.create_task(
        db=db_session,
        task_data=TaskCreate(title="Pending A", description=None, completed=False),
    )
    TaskService.create_task(
        db=db_session,
        task_data=TaskCreate(title="Done A", description=None, completed=True),
    )
    TaskService.create_task(
        db=db_session,
        task_data=TaskCreate(title="Done B", description=None, completed=True),
    )

    total = TaskService.get_tasks_count(db=db_session)
    completed = TaskService.get_tasks_count(db=db_session, completed=True)
    pending = TaskService.get_tasks_count(db=db_session, completed=False)

    assert total == 3
    assert completed == 2
    assert pending == 1
