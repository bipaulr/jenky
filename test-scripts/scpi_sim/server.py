import socketserver
import threading

DEFAULT_VOLTAGE = 3.3


class Instrument:
    def __init__(self):
        self.voltage = DEFAULT_VOLTAGE
        self.error_queue = []
        self.lock = threading.Lock()

    def reset(self):
        with self.lock:
            self.voltage = DEFAULT_VOLTAGE
            self.error_queue.clear()

    def measure_voltage(self):
        return self.voltage

    def push_error(self, code, message):
        with self.lock:
            self.error_queue.append((code, message))

    def pop_error(self):
        with self.lock:
            if self.error_queue:
                return self.error_queue.pop(0)
            return (0, "No error")


def handle_command(instrument, command):
    command = command.strip()
    if not command:
        return None

    upper = command.upper()
    if upper == "*IDN?":
        return "NetTest,MockPhotonicsInstrument,SN001,FW1.0"
    if upper == "*RST":
        instrument.reset()
        return None
    if upper == "MEAS:VOLT?":
        return f"{instrument.measure_voltage():.3f}"
    if upper == "SYST:ERR?":
        code, message = instrument.pop_error()
        return f"{code},{message}"

    instrument.push_error(-113, "Undefined header")
    return None


class SCPIHandler(socketserver.StreamRequestHandler):
    def handle(self):
        instrument = self.server.instrument
        while True:
            line = self.rfile.readline()
            if not line:
                break
            response = handle_command(instrument, line.decode("ascii", errors="ignore"))
            if response is not None:
                self.wfile.write((response + "\n").encode("ascii"))


class SCPIServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, host_port):
        super().__init__(host_port, SCPIHandler)
        self.instrument = Instrument()


def create_server(host="127.0.0.1", port=0):
    return SCPIServer((host, port))


if __name__ == "__main__":
    server = create_server(port=5025)
    print(f"SCPI mock instrument listening on {server.server_address}")
    server.serve_forever()
