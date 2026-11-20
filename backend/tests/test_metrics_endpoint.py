from app.api.metrics import Metrics


def test_metrics_render_histogram():
    m = Metrics()
    m.observe("GET", "/health", 200, 0.003)
    m.observe("GET", "/health", 200, 0.2)
    text = m.render({"documents": 2})
    assert 'ragforge_http_requests_total{method="GET",route="/health",status="200"} 2' in text
    assert 'ragforge_http_request_seconds_bucket{route="/health",le="0.005"} 1' in text
    assert 'ragforge_http_request_seconds_bucket{route="/health",le="+Inf"} 2' in text
    assert "ragforge_documents 2" in text


def test_metrics_endpoint_uses_route_templates(client, admin_headers):
    client.get("/documents/abcdef0123456789", headers=admin_headers)
    body = client.get("/metrics").text
    assert 'route="/documents/{doc_id}"' in body
    assert "abcdef0123456789" not in body
    assert "ragforge_users 1" in body
