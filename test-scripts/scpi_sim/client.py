import socket


class SCPIClient:
    def __init__(self, host, port, timeout=2.0):
        self._sock = socket.create_connection((host, port), timeout=timeout)
        self._reader = self._sock.makefile("r", encoding="ascii", newline="\n")

    def send_command(self, command):
        self._sock.sendall((command.strip() + "\n").encode("ascii"))

    def query(self, command):
        self.send_command(command)
        return self._reader.readline().strip()

    def close(self):
        self._reader.close()
        self._sock.close()
