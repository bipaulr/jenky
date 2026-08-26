import threading

from flask import Flask, jsonify, request


class DeviceStore:
    def __init__(self):
        self._devices = {}
        self._next_id = 1
        self._lock = threading.Lock()

    def create(self, name, ip_address, device_type):
        with self._lock:
            device_id = self._next_id
            self._next_id += 1
            device = {
                "id": device_id,
                "name": name,
                "ip_address": ip_address,
                "device_type": device_type,
            }
            self._devices[device_id] = device
            return device

    def get(self, device_id):
        return self._devices.get(device_id)

    def list_all(self):
        return [self._devices[key] for key in sorted(self._devices)]

    def update(self, device_id, **fields):
        with self._lock:
            device = self._devices.get(device_id)
            if device is None:
                return None
            device.update(fields)
            return device

    def delete(self, device_id):
        with self._lock:
            return self._devices.pop(device_id, None) is not None


def create_app():
    app = Flask(__name__)
    app.device_store = DeviceStore()
    register_routes(app)
    return app


def register_routes(app):
    store = app.device_store

    @app.get("/devices")
    def list_devices():
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
        devices = store.list_all()
        start = (page - 1) * per_page
        end = start + per_page
        return jsonify(devices[start:end])

    @app.get("/devices/<int:device_id>")
    def get_device(device_id):
        device = store.get(device_id)
        if device is None:
            return jsonify({"error": "device not found"}), 404
        return jsonify(device), 200

    @app.post("/devices")
    def create_device():
        data = request.get_json(silent=True) or {}
        name = data.get("name")
        ip_address = data.get("ip_address")
        if not name:
            return jsonify({"error": "name is required"}), 400
        if not ip_address:
            return jsonify({"error": "ip_address is required"}), 400
        device_type = data.get("device_type", "unknown")
        device = store.create(name, ip_address, device_type)
        return jsonify(device), 201

    @app.put("/devices/<int:device_id>")
    def update_device(device_id):
        data = request.get_json(silent=True) or {}
        allowed = {"name", "ip_address", "device_type"}
        fields = {key: value for key, value in data.items() if key in allowed}
        device = store.update(device_id, **fields)
        if device is None:
            return jsonify({"error": "device not found"}), 404
        return jsonify(device), 200

    @app.delete("/devices/<int:device_id>")
    def delete_device(device_id):
        deleted = store.delete(device_id)
        if not deleted:
            return jsonify({"error": "device not found"}), 404
        return "", 204


if __name__ == "__main__":
    create_app().run(port=5000)
