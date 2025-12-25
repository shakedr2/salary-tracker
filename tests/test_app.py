# -*- coding: utf-8 -*-
"""
Basic API tests for Flask app.
"""
import pytest
from backend.app import app


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    """Test /api/health endpoint."""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    assert 'timestamp' in data


def test_index_page(client):
    """Test main index page."""
    response = client.get('/')
    assert response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__])
