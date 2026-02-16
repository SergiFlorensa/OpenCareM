def test_contexto_clinico_resumen(client):
    response = client.get("/api/v1/clinical-context/resumen")
    assert response.status_code == 200
    payload = response.json()
    assert payload["version_contexto"] == "urgencias_es_v1"
    assert payload["total_areas"] >= 6
    assert payload["total_circuitos"] >= 2
    assert payload["total_roles"] >= 4
    assert payload["total_procedimientos"] >= 2
    assert payload["total_estandares"] >= 3


def test_contexto_clinico_areas_incluye_observacion_36h(client):
    response = client.get("/api/v1/clinical-context/areas")
    assert response.status_code == 200
    areas = response.json()
    observacion = next(item for item in areas if item["codigo"] == "observacion_24_36h")
    assert observacion["capacidad_total"] == 18
    assert observacion["estancia_objetivo_horas_max"] == 36


def test_contexto_clinico_circuitos_contiene_reglas_operativas(client):
    response = client.get("/api/v1/clinical-context/circuitos")
    assert response.status_code == 200
    circuits = response.json()
    circuito_1 = next(item for item in circuits if item["codigo"] == "circuito_1_ambulantes")
    assert "fiebre" in " ".join(circuito_1["acciones_tempranas"]).lower()
    circuito_2 = next(item for item in circuits if item["codigo"] == "circuito_2_encamados")
    assert "observacion" in circuito_2["destino_recomendado"].lower()


def test_contexto_clinico_roles_contiene_enfermeria_y_admision(client):
    response = client.get("/api/v1/clinical-context/roles")
    assert response.status_code == 200
    roles = response.json()
    role_names = {item["nombre"] for item in roles}
    assert "enfermeria_tcae" in role_names
    assert "admision" in role_names


def test_contexto_clinico_procedimiento_por_clave(client):
    ok_response = client.get("/api/v1/clinical-context/procedimientos/montaje_lucas")
    assert ok_response.status_code == 200
    payload = ok_response.json()
    assert payload["clave"] == "montaje_lucas"
    assert len(payload["pasos"]) == 4

    not_found_response = client.get("/api/v1/clinical-context/procedimientos/no-existe")
    assert not_found_response.status_code == 404
    assert (
        not_found_response.json()["detail"]
        == "Procedimiento no encontrado en contexto clinico."
    )


def test_triage_levels_manchester_contiene_5_niveles_y_slas(client):
    response = client.get("/api/v1/clinical-context/triage-levels/manchester")
    assert response.status_code == 200
    payload = response.json()

    assert len(payload) == 5
    niveles = [item["nivel"] for item in payload]
    assert niveles == [1, 2, 3, 4, 5]

    colores = {item["nivel"]: item["color"] for item in payload}
    assert colores[1] == "rojo"
    assert colores[2] == "naranja"
    assert colores[3] == "amarillo"
    assert colores[4] == "verde"
    assert colores[5] == "azul"

    slas = {item["nivel"]: item["sla_objetivo_minutos"] for item in payload}
    assert slas[1] == 0
    assert slas[2] == 10
    assert slas[3] == 30
    assert slas[4] == 120
    assert slas[5] == 240
