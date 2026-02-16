def test_request_logging_adds_request_id_header(client):
    """Ensure each response has a request id for traceability across logs."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0


def test_request_logging_uses_incoming_request_id(client):
    """Preserve caller-provided request id to simplify distributed tracing."""
    response = client.get("/health", headers={"X-Request-ID": "trace-123"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "trace-123"
