import pytest

from app.services.auth_service import AuthService


def test_bootstrap_first_admin_success(db_session):
    created_admin = AuthService.bootstrap_first_admin(
        db=db_session,
        username="rootadmin",
        password="StrongAdmin123",
    )

    assert created_admin.id is not None
    assert created_admin.username == "rootadmin"
    assert created_admin.is_superuser is True
    assert created_admin.is_active is True


def test_bootstrap_first_admin_blocked_when_users_exist(db_session):
    AuthService.register_user(
        db=db_session,
        username="normaluser",
        password="StrongUser123",
    )

    with pytest.raises(ValueError, match="Bootstrap bloqueado"):
        AuthService.bootstrap_first_admin(
            db=db_session,
            username="rootadmin",
            password="StrongAdmin123",
        )
