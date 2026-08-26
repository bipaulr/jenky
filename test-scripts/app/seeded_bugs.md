Private notes — not linked from README. Ground truth for the "Bugs Caught"
section, so specifics stay accurate instead of reconstructed from memory.

## Bug 1: pagination drops the last item on a full page

`app/server.py`, `list_devices()`.

`end = start + per_page - 1` instead of `end = start + per_page`. Python
slicing is exclusive on the end index, so this off-by-one drops the last
item whenever a page is fully populated (e.g. `per_page=2` with exactly 2
devices returns 1).

Caught by: `tests/test_api_regression.py::test_pagination_does_not_drop_last_item_on_page`

## Bug 2: GET on a missing device returns 200 instead of 404

`app/server.py`, `get_device()`.

The `None` branch returns `jsonify({}), 200` instead of a 404. A client
can't distinguish "device with an empty body" from "device does not exist".

Caught by: `tests/test_api_regression.py::test_get_missing_device_returns_404`

## Bug 3: POST accepts a device with no ip_address

`app/server.py`, `create_device()`.

Only `name` is validated as required; `ip_address` is read with `.get()`
and silently stored as `None` if absent, so an invalid device can be
created with no way to reach it.

Caught by: `tests/test_api_regression.py::test_create_device_requires_ip_address`
