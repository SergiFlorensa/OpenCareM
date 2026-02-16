from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User


def _create_user(
    db_session,
    username: str,
    password: str,
    is_superuser: bool = False,
    specialty: str = "general",
):
    """Create a user in tests and allow marking it as admin when needed."""
    user = User(
        username=username,
        hashed_password=get_password_hash(password),
        specialty=specialty,
        is_active=True,
        is_superuser=is_superuser,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_login_success(client, db_session):
    _create_user(db_session, username="admin", password="admin12345")
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "admin12345"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert "access_token" in payload
    assert "refresh_token" in payload


def test_login_failure(client, db_session):
    _create_user(db_session, username="admin", password="admin12345")
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "wrong-password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401


def test_me_requires_token(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_with_valid_token(client, db_session):
    _create_user(db_session, username="admin", password="admin12345", specialty="emergency")
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "admin12345"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login_response.json()["access_token"]

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["username"] == "admin"
    assert me_response.json()["specialty"] == "emergency"
    assert me_response.json()["is_superuser"] is False


def test_me_with_admin_user_returns_admin_flag(client, db_session):
    _create_user(
        db_session,
        username="rootadmin",
        password="AdminPass123",
        is_superuser=True,
        specialty="critical_care",
    )
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "rootadmin", "password": "AdminPass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login_response.json()["access_token"]
    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["username"] == "rootadmin"
    assert me_response.json()["specialty"] == "critical_care"
    assert me_response.json()["is_superuser"] is True


def test_register_success(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "newuser", "password": "StrongPass123", "specialty": "cardiology"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["username"] == "newuser"
    assert payload["specialty"] == "cardiology"
    assert "id" in payload


def test_register_rejects_duplicate_username(client, db_session):
    _create_user(db_session, username="existing", password="StrongPass123")
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "existing", "password": "StrongPass123"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "El nombre de usuario ya existe."


def test_register_rejects_weak_password(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "weakuser", "password": "weakpass"},
    )
    assert response.status_code == 400
    assert "La contrasena debe" in response.json()["detail"]


def test_admin_users_requires_auth(client):
    response = client.get("/api/v1/auth/admin/users")
    assert response.status_code == 401


def test_admin_users_forbidden_for_non_admin(client, db_session):
    _create_user(db_session, username="basicuser", password="BasicPass123", is_superuser=False)
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "basicuser", "password": "BasicPass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login_response.json()["access_token"]
    users_response = client.get(
        "/api/v1/auth/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert users_response.status_code == 403
    assert users_response.json()["detail"] == "Se requieren permisos de administrador."


def test_admin_users_success_for_superuser(client, db_session):
    _create_user(
        db_session,
        username="rootadmin",
        password="AdminPass123",
        is_superuser=True,
        specialty="critical_care",
    )
    _create_user(
        db_session,
        username="worker",
        password="WorkerPass123",
        is_superuser=False,
        specialty="neurology",
    )
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "rootadmin", "password": "AdminPass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login_response.json()["access_token"]
    users_response = client.get(
        "/api/v1/auth/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert users_response.status_code == 200
    payload = users_response.json()
    assert len(payload) == 2
    assert payload[0]["username"] == "rootadmin"
    assert payload[0]["specialty"] == "critical_care"
    assert payload[0]["is_superuser"] is True
    assert payload[1]["username"] == "worker"
    assert payload[1]["specialty"] == "neurology"
    assert payload[1]["is_superuser"] is False


def test_refresh_rotates_tokens(client, db_session):
    _create_user(db_session, username="rotateuser", password="RotatePass123")
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "rotateuser", "password": "RotatePass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    old_refresh = login_response.json()["refresh_token"]

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert refresh_response.status_code == 200
    payload = refresh_response.json()
    assert payload["token_type"] == "bearer"
    assert payload["refresh_token"] != old_refresh

    reused_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert reused_response.status_code == 401


def test_logout_revokes_refresh_session(client, db_session):
    _create_user(db_session, username="logoutuser", password="LogoutPass123")
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "logoutuser", "password": "LogoutPass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    refresh_token = login_response.json()["refresh_token"]

    logout_response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert logout_response.status_code == 200
    assert logout_response.json()["message"] == "Sesion revocada"

    refresh_after_logout = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_after_logout.status_code == 401


def test_login_is_temporarily_blocked_after_too_many_failures(client, db_session):
    _create_user(db_session, username="throttleuser", password="CorrectPass123")
    original_max_attempts = settings.LOGIN_MAX_ATTEMPTS
    original_block_minutes = settings.LOGIN_BLOCK_MINUTES
    original_window_minutes = settings.LOGIN_WINDOW_MINUTES
    settings.LOGIN_MAX_ATTEMPTS = 3
    settings.LOGIN_BLOCK_MINUTES = 10
    settings.LOGIN_WINDOW_MINUTES = 10
    try:
        for _ in range(3):
            failed_response = client.post(
                "/api/v1/auth/login",
                data={"username": "throttleuser", "password": "wrong-password"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            assert failed_response.status_code == 401

        blocked_response = client.post(
            "/api/v1/auth/login",
            data={"username": "throttleuser", "password": "CorrectPass123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert blocked_response.status_code == 429
        assert "Demasiados intentos fallidos de inicio de sesion" in blocked_response.json()[
            "detail"
        ]
    finally:
        settings.LOGIN_MAX_ATTEMPTS = original_max_attempts
        settings.LOGIN_BLOCK_MINUTES = original_block_minutes
        settings.LOGIN_WINDOW_MINUTES = original_window_minutes


def test_login_success_resets_failed_attempt_counter(client, db_session):
    _create_user(db_session, username="resetuser", password="CorrectPass123")
    original_max_attempts = settings.LOGIN_MAX_ATTEMPTS
    original_block_minutes = settings.LOGIN_BLOCK_MINUTES
    original_window_minutes = settings.LOGIN_WINDOW_MINUTES
    settings.LOGIN_MAX_ATTEMPTS = 3
    settings.LOGIN_BLOCK_MINUTES = 10
    settings.LOGIN_WINDOW_MINUTES = 10
    try:
        first_failed_response = client.post(
            "/api/v1/auth/login",
            data={"username": "resetuser", "password": "wrong-password"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert first_failed_response.status_code == 401

        successful_response = client.post(
            "/api/v1/auth/login",
            data={"username": "resetuser", "password": "CorrectPass123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert successful_response.status_code == 200

        for _ in range(2):
            failed_response = client.post(
                "/api/v1/auth/login",
                data={"username": "resetuser", "password": "wrong-password"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            assert failed_response.status_code == 401

        should_not_be_blocked_yet = client.post(
            "/api/v1/auth/login",
            data={"username": "resetuser", "password": "CorrectPass123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert should_not_be_blocked_yet.status_code == 200
    finally:
        settings.LOGIN_MAX_ATTEMPTS = original_max_attempts
        settings.LOGIN_BLOCK_MINUTES = original_block_minutes
        settings.LOGIN_WINDOW_MINUTES = original_window_minutes
