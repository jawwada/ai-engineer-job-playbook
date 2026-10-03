#!/usr/bin/env python3
"""TLS 1.3 and mutual TLS over localhost with a throwaway private CA (chapter 49b.9 to 49b.11).

Creates a root CA, a server certificate for orders.internal and a client certificate with a SPIFFE-style
URI SAN in a temporary directory with the openssl command-line tool (no keys are stored in this
repository), then runs four handshakes on 127.0.0.1 and checks what each side sees:

  1. server-only TLS                         -> works; the server learns nothing about the client
  2. mTLS with a client certificate          -> works; the server reads the client's identity from its SAN
  3. mTLS without a client certificate       -> the client's handshake call returns, and the failure
                                                surfaces on the first read (TLS 1.3 sends the client
                                                certificate after the server's Finished)
  4. a client that expects another hostname  -> fails during the handshake (hostname check)

    python3 -B mtls_demo.py        (needs the openssl CLI; prints "skipped" without it)
"""
import os
import shutil
import socket
import ssl
import subprocess
import tempfile
import threading

SPIFFE_ID = "spiffe://example.org/ns/agents/sa/support-agent"


def openssl(*args, cwd):
    subprocess.run(["openssl", *args], cwd=cwd, check=True, capture_output=True)


def make_pki(d: str) -> None:
    ec = ["-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:P-256", "-nodes"]
    openssl("req", "-x509", *ec, "-keyout", "ca.key", "-out", "ca.pem", "-days", "2",
            "-subj", "/CN=Example Internal Root CA", "-addext", "basicConstraints=critical,CA:TRUE",
            "-addext", "keyUsage=critical,keyCertSign,cRLSign", cwd=d)
    leaves = {"server": ("/CN=orders.internal", "subjectAltName=DNS:orders.internal\nextendedKeyUsage=serverAuth\n"),
              "agent": ("/CN=support-agent", f"subjectAltName=URI:{SPIFFE_ID}\nextendedKeyUsage=clientAuth\n")}
    for name, (subject, extensions) in leaves.items():
        with open(os.path.join(d, f"{name}.ext"), "w") as f:
            f.write(extensions + "keyUsage=critical,digitalSignature\n")
        openssl("req", *ec, "-keyout", f"{name}.key", "-out", f"{name}.csr", "-subj", subject, cwd=d)
        openssl("x509", "-req", "-in", f"{name}.csr", "-CA", "ca.pem", "-CAkey", "ca.key", "-CAcreateserial",
                "-days", "1", "-extfile", f"{name}.ext", "-out", f"{name}.pem", cwd=d)


def handshake(d: str, *, require_client_cert: bool, client_cert: bool, hostname: str = "orders.internal") -> dict:
    """Run one connection; return what the client and the server observed."""
    server_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    server_ctx.load_cert_chain(os.path.join(d, "server.pem"), os.path.join(d, "server.key"))
    if require_client_cert:
        server_ctx.verify_mode = ssl.CERT_REQUIRED                 # demand a client certificate
        server_ctx.load_verify_locations(os.path.join(d, "ca.pem"))   # issued by our private CA
    client_ctx = ssl.create_default_context(cafile=os.path.join(d, "ca.pem"))
    if client_cert:
        client_ctx.load_cert_chain(os.path.join(d, "agent.pem"), os.path.join(d, "agent.key"))
    seen = {}
    listener = socket.create_server(("127.0.0.1", 0))

    def serve():
        conn, _ = listener.accept()
        try:
            with server_ctx.wrap_socket(conn, server_side=True) as tls:
                peer = tls.getpeercert() or {}
                seen["server_saw"] = [value for kind, value in peer.get("subjectAltName", ()) if kind == "URI"]
                tls.sendall(b"hello")
        except (ssl.SSLError, OSError) as err:
            seen["server_error"] = getattr(err, "reason", None) or type(err).__name__

    thread = threading.Thread(target=serve)
    thread.start()
    try:
        with socket.create_connection(listener.getsockname()) as raw:
            with client_ctx.wrap_socket(raw, server_hostname=hostname) as tls:
                seen["handshake"] = tls.version()
                seen["reply"] = tls.recv(16)
    except ssl.SSLCertVerificationError as err:
        seen["client_error"] = err.verify_message
    except ssl.SSLError as err:
        seen["client_error"] = err.reason
    thread.join(10)
    listener.close()
    return seen


def main() -> int:
    if shutil.which("openssl") is None:
        print("skipped: the openssl command-line tool is not installed")
        return 0
    with tempfile.TemporaryDirectory() as d:
        make_pki(d)
        one = handshake(d, require_client_cert=False, client_cert=False)
        assert one == {"handshake": "TLSv1.3", "reply": b"hello", "server_saw": []}, one
        two = handshake(d, require_client_cert=True, client_cert=True)
        assert two == {"handshake": "TLSv1.3", "reply": b"hello", "server_saw": [SPIFFE_ID]}, two
        three = handshake(d, require_client_cert=True, client_cert=False)
        assert three["handshake"] == "TLSv1.3" and "reply" not in three, three
        assert three["client_error"] == "TLSV13_ALERT_CERTIFICATE_REQUIRED", three
        assert three["server_error"] == "PEER_DID_NOT_RETURN_A_CERTIFICATE", three
        four = handshake(d, require_client_cert=False, client_cert=False, hostname="billing.internal")
        assert "handshake" not in four and "Hostname mismatch" in four["client_error"], four
        for label, result in (("server-only TLS", one), ("mTLS with a client certificate", two),
                              ("mTLS without a client certificate", three), ("wrong hostname", four)):
            print(f"{label:34} {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
