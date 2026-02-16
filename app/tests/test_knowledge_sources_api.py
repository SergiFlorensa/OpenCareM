from app.core.security import get_password_hash
from app.models.user import User


def _create_user(
    db_session,
    *,
    username: str,
    password: str,
    is_superuser: bool = False,
    specialty: str = "general",
) -> User:
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


def _auth_headers(client, *, username: str, password: str) -> dict[str, str]:
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_knowledge_source_requires_auth(client):
    response = client.post(
        "/api/v1/knowledge-sources/",
        json={
            "title": "Guia Sepsis 2025",
            "source_type": "guideline",
            "source_url": "https://www.who.int/news-room/fact-sheets/detail/sepsis",
        },
    )
    assert response.status_code == 401


def test_create_knowledge_source_rejects_non_whitelisted_domain(client, db_session):
    _create_user(
        db_session,
        username="clinician_a",
        password="StrongPass123",
        specialty="emergency",
    )
    headers = _auth_headers(client, username="clinician_a", password="StrongPass123")
    response = client.post(
        "/api/v1/knowledge-sources/",
        json={
            "title": "Blog no validado",
            "source_type": "guideline",
            "source_url": "https://randomblog.example.com/post/sepsis",
            "summary": "No debe aceptarse",
        },
        headers=headers,
    )
    assert response.status_code == 400
    assert "Dominio no permitido" in response.json()["detail"]


def test_create_seal_and_list_validated_knowledge_source(client, db_session):
    _create_user(
        db_session,
        username="clinician_b",
        password="StrongPass123",
        specialty="emergency",
    )
    _create_user(
        db_session,
        username="admin_b",
        password="StrongPass123",
        specialty="emergency",
        is_superuser=True,
    )
    clinician_headers = _auth_headers(client, username="clinician_b", password="StrongPass123")
    admin_headers = _auth_headers(client, username="admin_b", password="StrongPass123")

    create_response = client.post(
        "/api/v1/knowledge-sources/",
        json={
            "title": "Guia Sepsis WHO",
            "summary": "Bundle inicial de sepsis para urgencias",
            "content": "Antibioterapia en 1h, lactato serial y PAM objetivo >= 65 mmHg.",
            "source_type": "guideline",
            "source_url": "https://www.who.int/health-topics/sepsis",
            "tags": ["sepsis", "urgencias", "bundle"],
        },
        headers=clinician_headers,
    )
    assert create_response.status_code == 201
    source = create_response.json()
    assert source["status"] == "pending_review"
    source_id = source["id"]

    list_before = client.get("/api/v1/knowledge-sources/", headers=clinician_headers)
    assert list_before.status_code == 200
    assert list_before.json() == []

    seal_response = client.post(
        f"/api/v1/knowledge-sources/{source_id}/seal",
        json={"decision": "approve", "note": "Revisado por staff de guardia"},
        headers=admin_headers,
    )
    assert seal_response.status_code == 200
    assert seal_response.json()["decision"] == "approve"

    list_after = client.get("/api/v1/knowledge-sources/", headers=clinician_headers)
    assert list_after.status_code == 200
    items = list_after.json()
    assert len(items) == 1
    assert items[0]["id"] == source_id
    assert items[0]["status"] == "validated"

    validations = client.get(
        f"/api/v1/knowledge-sources/{source_id}/validations",
        headers=clinician_headers,
    )
    assert validations.status_code == 200
    assert len(validations.json()) == 1
    assert validations.json()[0]["decision"] == "approve"


def test_non_admin_cannot_seal_knowledge_source(client, db_session):
    _create_user(
        db_session,
        username="clinician_c",
        password="StrongPass123",
        specialty="general",
    )
    headers = _auth_headers(client, username="clinician_c", password="StrongPass123")
    create_response = client.post(
        "/api/v1/knowledge-sources/",
        json={
            "title": "PubMed trial",
            "source_type": "pubmed",
            "source_url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
            "summary": "Ensayo de referencia",
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    source_id = create_response.json()["id"]

    seal_response = client.post(
        f"/api/v1/knowledge-sources/{source_id}/seal",
        json={"decision": "approve"},
        headers=headers,
    )
    assert seal_response.status_code == 403


def test_get_trusted_domains_returns_whitelist(client, db_session):
    _create_user(
        db_session,
        username="clinician_trusted",
        password="StrongPass123",
        specialty="general",
    )
    headers = _auth_headers(client, username="clinician_trusted", password="StrongPass123")
    response = client.get("/api/v1/knowledge-sources/trusted-domains", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["web_whitelist_enforced"] is True
    assert "who.int" in payload["allowed_domains"]


def test_chat_uses_validated_knowledge_source(client, db_session):
    _create_user(
        db_session,
        username="clinician_d",
        password="StrongPass123",
        specialty="emergency",
    )
    _create_user(
        db_session,
        username="admin_d",
        password="StrongPass123",
        specialty="emergency",
        is_superuser=True,
    )
    clinician_headers = _auth_headers(client, username="clinician_d", password="StrongPass123")
    admin_headers = _auth_headers(client, username="admin_d", password="StrongPass123")

    source_response = client.post(
        "/api/v1/knowledge-sources/",
        json={
            "specialty": "emergency",
            "title": "Algoritmo Sepsis Validado",
            "summary": "Priorizar antibiotico precoz y perfusion.",
            "content": "Sepsis, lactato, noradrenalina, fluidoterapia 30 ml/kg.",
            "source_type": "guideline",
            "source_url": "https://www.semes.org/guias/sepsis-urgencias",
            "tags": ["sepsis", "noradrenalina", "lactato"],
        },
        headers=clinician_headers,
    )
    assert source_response.status_code == 201
    source_id = source_response.json()["id"]
    approve = client.post(
        f"/api/v1/knowledge-sources/{source_id}/seal",
        json={"decision": "approve"},
        headers=admin_headers,
    )
    assert approve.status_code == 200

    task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso sepsis para chat",
            "clinical_priority": "high",
            "specialty": "emergency",
            "patient_reference": "PAC-VAL-01",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert task_response.status_code == 201
    task_id = task_response.json()["id"]

    chat_response = client.post(
        f"/api/v1/care-tasks/{task_id}/chat/messages",
        json={
            "query": "Paciente con sepsis, lactato elevado y vasopresor inicial.",
            "session_id": "session-validated",
            "use_patient_history": False,
            "use_web_sources": False,
        },
        headers=clinician_headers,
    )
    assert chat_response.status_code == 200
    payload = chat_response.json()
    assert payload["knowledge_sources"]
    assert any(
        "semes.org/guias/sepsis-urgencias" in item["source"]
        for item in payload["knowledge_sources"]
    )
