import pytest
import requests


@pytest.mark.functional
def test_create_device_returns_201(api_base_url):
    response = requests.post(
        f"{api_base_url}/devices",
        json={"name": "sw-core-01", "ip_address": "10.0.0.1", "device_type": "switch"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "sw-core-01"
    assert body["ip_address"] == "10.0.0.1"
    assert "id" in body


@pytest.mark.functional
def test_get_device_returns_created_device(api_base_url):
    created = requests.post(
        f"{api_base_url}/devices",
        json={"name": "sw-core-02", "ip_address": "10.0.0.2", "device_type": "switch"},
    ).json()
    response = requests.get(f"{api_base_url}/devices/{created['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "sw-core-02"


@pytest.mark.functional
def test_update_device_changes_fields(api_base_url):
    created = requests.post(
        f"{api_base_url}/devices",
        json={"name": "sw-core-03", "ip_address": "10.0.0.3", "device_type": "switch"},
    ).json()
    response = requests.put(
        f"{api_base_url}/devices/{created['id']}",
        json={"name": "sw-core-03-renamed"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "sw-core-03-renamed"


@pytest.mark.functional
def test_delete_device_returns_204(api_base_url):
    created = requests.post(
        f"{api_base_url}/devices",
        json={"name": "sw-core-04", "ip_address": "10.0.0.4", "device_type": "switch"},
    ).json()
    response = requests.delete(f"{api_base_url}/devices/{created['id']}")
    assert response.status_code == 204


@pytest.mark.functional
def test_list_devices_returns_created_device(api_base_url):
    requests.post(
        f"{api_base_url}/devices",
        json={"name": "sw-core-05", "ip_address": "10.0.0.5", "device_type": "switch"},
    )
    response = requests.get(f"{api_base_url}/devices")
    assert response.status_code == 200
    names = [device["name"] for device in response.json()]
    assert "sw-core-05" in names


@pytest.mark.functional
def test_delete_missing_device_returns_404(api_base_url):
    response = requests.delete(f"{api_base_url}/devices/999999")
    assert response.status_code == 404


@pytest.mark.functional
def test_update_missing_device_returns_404(api_base_url):
    response = requests.put(
        f"{api_base_url}/devices/999999",
        json={"name": "does-not-exist"},
    )
    assert response.status_code == 404
