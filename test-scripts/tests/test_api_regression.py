import pytest
import requests


@pytest.mark.regression
def test_pagination_does_not_drop_last_item_on_page(api_base_url):
    for index in range(2):
        requests.post(
            f"{api_base_url}/devices",
            json={"name": f"dev-{index}", "ip_address": f"10.0.0.{index}", "device_type": "router"},
        )
    response = requests.get(f"{api_base_url}/devices", params={"page": 1, "per_page": 2})
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.regression
def test_get_missing_device_returns_404(api_base_url):
    response = requests.get(f"{api_base_url}/devices/9999")
    assert response.status_code == 404


@pytest.mark.regression
def test_create_device_requires_ip_address(api_base_url):
    response = requests.post(
        f"{api_base_url}/devices",
        json={"name": "no-ip-device"},
    )
    assert response.status_code == 400
