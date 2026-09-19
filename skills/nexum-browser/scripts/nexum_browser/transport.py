from __future__ import annotations

import base64
import hashlib
import json
import os
import queue
import socket
import struct
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, BinaryIO


_WEBSOCKET_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
_MAX_MESSAGE_BYTES = 16 * 1024 * 1024


class _PipeReader:
    def __init__(self, stream: BinaryIO) -> None:
        self._queue: queue.Queue[bytes | None] = queue.Queue()
        self._buffer = bytearray()

        def read_loop() -> None:
            try:
                fd = stream.fileno()
                while True:
                    chunk = os.read(fd, 65536)
                    if not chunk:
                        break
                    self._queue.put(chunk)
            except OSError:
                pass
            finally:
                self._queue.put(None)

        threading.Thread(target=read_loop, name="nexum-browser-proxy-reader", daemon=True).start()

    def _fill(self, *, size: int | None = None, marker: bytes | None = None, timeout: float) -> None:
        deadline = time.monotonic() + timeout
        while (size is not None and len(self._buffer) < size) or (
            marker is not None and marker not in self._buffer
        ):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Timed out reading Codex app-server proxy")
            try:
                chunk = self._queue.get(timeout=remaining)
            except queue.Empty as exc:
                raise TimeoutError("Timed out reading Codex app-server proxy") from exc
            if chunk is None:
                raise EOFError("Codex app-server proxy closed its output")
            self._buffer.extend(chunk)
            if len(self._buffer) > _MAX_MESSAGE_BYTES:
                raise RuntimeError("Codex app-server proxy message exceeded the supported size")

    def read_exact(self, size: int, timeout: float) -> bytes:
        self._fill(size=size, timeout=timeout)
        result = bytes(self._buffer[:size])
        del self._buffer[:size]
        return result

    def read_until(self, marker: bytes, timeout: float) -> bytes:
        self._fill(marker=marker, timeout=timeout)
        end = self._buffer.find(marker) + len(marker)
        result = bytes(self._buffer[:end])
        del self._buffer[:end]
        return result


class ProxyWebSocket:
    """WebSocket client transported through the Codex app-server proxy stdio tunnel."""

    def __init__(self, codex: Path, *, stderr: Any, timeout: float = 15) -> None:
        self.proc = subprocess.Popen(
            [str(codex), "app-server", "proxy"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=stderr,
            cwd=str(Path(__file__).resolve().parents[2]),
        )
        if self.proc.stdin is None or self.proc.stdout is None:
            raise RuntimeError("Codex app-server proxy stdio is unavailable")
        self._stdin = self.proc.stdin
        self._reader = _PipeReader(self.proc.stdout)
        self._closed = False
        self._cleanup_done = False
        self._handshake(timeout)

    def _handshake(self, timeout: float) -> None:
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            "GET /rpc HTTP/1.1\r\n"
            "Host: localhost\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        ).encode("ascii")
        self._stdin.write(request)
        self._stdin.flush()
        header = self._reader.read_until(b"\r\n\r\n", timeout).decode("latin-1")
        status = header.split("\r\n", 1)[0]
        if " 101 " not in status:
            raise RuntimeError(f"Codex app-server proxy WebSocket upgrade failed: {status}")
        headers: dict[str, str] = {}
        for line in header.split("\r\n")[1:]:
            if ":" not in line:
                continue
            name, value = line.split(":", 1)
            headers[name.strip().lower()] = value.strip()
        expected = base64.b64encode(
            hashlib.sha1((key + _WEBSOCKET_GUID).encode("ascii")).digest()
        ).decode("ascii")
        if headers.get("sec-websocket-accept") != expected:
            raise RuntimeError("Codex app-server proxy returned an invalid WebSocket accept header")

    def _send_frame(self, opcode: int, payload: bytes = b"") -> None:
        if self._closed:
            raise RuntimeError("Codex app-server proxy connection is closed")
        mask = os.urandom(4)
        size = len(payload)
        header = bytearray([0x80 | (opcode & 0x0F)])
        if size < 126:
            header.append(0x80 | size)
        elif size < 65536:
            header.extend((0x80 | 126,))
            header.extend(struct.pack("!H", size))
        else:
            header.extend((0x80 | 127,))
            header.extend(struct.pack("!Q", size))
        header.extend(mask)
        masked = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
        self._stdin.write(bytes(header) + masked)
        self._stdin.flush()

    def send_json(self, payload: dict[str, Any]) -> None:
        self._send_frame(
            0x1,
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
        )

    def _recv_frame(self, timeout: float) -> tuple[bool, int, bytes]:
        first, second = self._reader.read_exact(2, timeout)
        if first & 0x70:
            raise RuntimeError("Codex app-server proxy used unsupported WebSocket RSV bits")
        final = bool(first & 0x80)
        opcode = first & 0x0F
        masked = bool(second & 0x80)
        size = second & 0x7F
        if size == 126:
            size = struct.unpack("!H", self._reader.read_exact(2, timeout))[0]
        elif size == 127:
            size = struct.unpack("!Q", self._reader.read_exact(8, timeout))[0]
        if size > _MAX_MESSAGE_BYTES:
            raise RuntimeError("Codex app-server proxy WebSocket frame exceeded the supported size")
        mask = self._reader.read_exact(4, timeout) if masked else None
        payload = self._reader.read_exact(size, timeout) if size else b""
        if mask is not None:
            payload = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
        return final, opcode, payload

    def recv_json(self, timeout: float) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        fragments = bytearray()
        message_opcode: int | None = None
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Timed out waiting for Codex app-server response")
            final, opcode, payload = self._recv_frame(remaining)
            if opcode == 0x9:
                self._send_frame(0xA, payload)
                continue
            if opcode == 0xA:
                continue
            if opcode == 0x8:
                self._closed = True
                raise EOFError("Codex app-server proxy closed the WebSocket")
            if opcode in (0x1, 0x2):
                if message_opcode is not None:
                    raise RuntimeError("Codex app-server proxy started a new fragmented WebSocket message")
                message_opcode = opcode
                fragments.extend(payload)
            elif opcode == 0x0:
                if message_opcode is None:
                    raise RuntimeError("Codex app-server proxy returned an unexpected continuation frame")
                fragments.extend(payload)
            else:
                continue
            if len(fragments) > _MAX_MESSAGE_BYTES:
                raise RuntimeError("Codex app-server proxy WebSocket message exceeded the supported size")
            if not final:
                continue
            if message_opcode != 0x1:
                fragments.clear()
                message_opcode = None
                continue
            try:
                value = json.loads(bytes(fragments).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise RuntimeError("Codex app-server proxy returned invalid JSON") from exc
            if not isinstance(value, dict):
                raise RuntimeError("Codex app-server proxy returned a non-object JSON message")
            return value

    def close(self) -> None:
        if self._cleanup_done:
            return
        self._cleanup_done = True
        if not self._closed:
            try:
                self._send_frame(0x8)
            except Exception:
                pass
        self._closed = True
        try:
            self._stdin.close()
        except Exception:
            pass
        try:
            self.proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=2)


class _SocketReader:
    def __init__(self, conn: socket.socket) -> None:
        self._conn = conn
        self._buffer = bytearray()

    def _fill(self, *, size: int | None = None, marker: bytes | None = None, timeout: float) -> None:
        deadline = time.monotonic() + timeout
        while (size is not None and len(self._buffer) < size) or (
            marker is not None and marker not in self._buffer
        ):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Timed out reading local Codex app-server")
            self._conn.settimeout(remaining)
            try:
                chunk = self._conn.recv(65536)
            except socket.timeout as exc:
                raise TimeoutError("Timed out reading local Codex app-server") from exc
            if not chunk:
                raise EOFError("Local Codex app-server closed the WebSocket")
            self._buffer.extend(chunk)
            if len(self._buffer) > _MAX_MESSAGE_BYTES:
                raise RuntimeError("Local Codex app-server message exceeded the supported size")

    def read_exact(self, size: int, timeout: float) -> bytes:
        self._fill(size=size, timeout=timeout)
        result = bytes(self._buffer[:size])
        del self._buffer[:size]
        return result

    def read_until(self, marker: bytes, timeout: float) -> bytes:
        self._fill(marker=marker, timeout=timeout)
        end = self._buffer.find(marker) + len(marker)
        result = bytes(self._buffer[:end])
        del self._buffer[:end]
        return result


class SocketWebSocket:
    """Authenticated loopback WebSocket client for a Skill-owned app-server."""

    def __init__(self, host: str, port: int, token: str, *, timeout: float = 15) -> None:
        self._host = host
        self._port = port
        self._conn = socket.create_connection((host, port), timeout=timeout)
        self._reader = _SocketReader(self._conn)
        self._closed = False
        self._cleanup_done = False
        self._handshake(token, timeout)

    def _handshake(self, token: str, timeout: float) -> None:
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            "GET /rpc HTTP/1.1\r\n"
            f"Host: {self._host}:{self._port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            f"Authorization: Bearer {token}\r\n"
            "\r\n"
        ).encode("ascii")
        self._conn.sendall(request)
        header = self._reader.read_until(b"\r\n\r\n", timeout).decode("latin-1")
        status = header.split("\r\n", 1)[0]
        if " 101 " not in status:
            raise RuntimeError(f"Local Codex app-server WebSocket upgrade failed: {status}")
        headers: dict[str, str] = {}
        for line in header.split("\r\n")[1:]:
            if ":" not in line:
                continue
            name, value = line.split(":", 1)
            headers[name.strip().lower()] = value.strip()
        expected = base64.b64encode(
            hashlib.sha1((key + _WEBSOCKET_GUID).encode("ascii")).digest()
        ).decode("ascii")
        if headers.get("sec-websocket-accept") != expected:
            raise RuntimeError("Local Codex app-server returned an invalid WebSocket accept header")

    def _send_frame(self, opcode: int, payload: bytes = b"") -> None:
        if self._closed:
            raise RuntimeError("Local Codex app-server connection is closed")
        mask = os.urandom(4)
        size = len(payload)
        header = bytearray([0x80 | (opcode & 0x0F)])
        if size < 126:
            header.append(0x80 | size)
        elif size < 65536:
            header.extend((0x80 | 126,))
            header.extend(struct.pack("!H", size))
        else:
            header.extend((0x80 | 127,))
            header.extend(struct.pack("!Q", size))
        header.extend(mask)
        masked = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
        self._conn.sendall(bytes(header) + masked)

    def send_json(self, payload: dict[str, Any]) -> None:
        self._send_frame(
            0x1,
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
        )

    def _recv_frame(self, timeout: float) -> tuple[bool, int, bytes]:
        first, second = self._reader.read_exact(2, timeout)
        if first & 0x70:
            raise RuntimeError("Local Codex app-server used unsupported WebSocket RSV bits")
        final = bool(first & 0x80)
        opcode = first & 0x0F
        masked = bool(second & 0x80)
        size = second & 0x7F
        if size == 126:
            size = struct.unpack("!H", self._reader.read_exact(2, timeout))[0]
        elif size == 127:
            size = struct.unpack("!Q", self._reader.read_exact(8, timeout))[0]
        if size > _MAX_MESSAGE_BYTES:
            raise RuntimeError("Local Codex app-server WebSocket frame exceeded the supported size")
        mask = self._reader.read_exact(4, timeout) if masked else None
        payload = self._reader.read_exact(size, timeout) if size else b""
        if mask is not None:
            payload = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
        return final, opcode, payload

    def recv_json(self, timeout: float) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        fragments = bytearray()
        message_opcode: int | None = None
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Timed out waiting for local Codex app-server response")
            final, opcode, payload = self._recv_frame(remaining)
            if opcode == 0x9:
                self._send_frame(0xA, payload)
                continue
            if opcode == 0xA:
                continue
            if opcode == 0x8:
                self._closed = True
                raise EOFError("Local Codex app-server closed the WebSocket")
            if opcode in (0x1, 0x2):
                if message_opcode is not None:
                    raise RuntimeError("Local Codex app-server started a new fragmented WebSocket message")
                message_opcode = opcode
                fragments.extend(payload)
            elif opcode == 0x0:
                if message_opcode is None:
                    raise RuntimeError("Local Codex app-server returned an unexpected continuation frame")
                fragments.extend(payload)
            else:
                continue
            if len(fragments) > _MAX_MESSAGE_BYTES:
                raise RuntimeError("Local Codex app-server WebSocket message exceeded the supported size")
            if not final:
                continue
            if message_opcode != 0x1:
                fragments.clear()
                message_opcode = None
                continue
            try:
                value = json.loads(bytes(fragments).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise RuntimeError("Local Codex app-server returned invalid JSON") from exc
            if not isinstance(value, dict):
                raise RuntimeError("Local Codex app-server returned a non-object JSON message")
            return value

    def close(self) -> None:
        if self._cleanup_done:
            return
        self._cleanup_done = True
        if not self._closed:
            try:
                self._send_frame(0x8)
            except Exception:
                pass
        self._closed = True
        try:
            self._conn.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self._conn.close()
