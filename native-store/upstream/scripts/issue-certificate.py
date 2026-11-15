"""Issue one free certificate for the shared Nodeno .com/.com.tr host and aliases.

Uses Certbot's official python-acme client. Dependencies are isolated under
artifacts/acme-runtime. Private material stays in the ignored, restricted ssl
directory. Only ACME challenge files are written to the site's document root.
"""
from __future__ import annotations

import argparse
import base64
import csv
import datetime as dt
import hashlib
import http.client
import importlib.util
import json
import logging
import os
from pathlib import Path
import re
import secrets
import socket
import ssl
import subprocess
import sys
import time
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "artifacts" / "acme-runtime"
PRIVATE = ROOT / "artifacts" / "ssl"
STATUS_FILE = ROOT / "artifacts" / "ssl-status.json"
DOMAINS = ("nodenohome.com", "www.nodenohome.com", "nodenohome.com.tr", "www.nodenohome.com.tr")
DOCUMENT_ROOT = "/home/nodenoho/public_html"
CHALLENGE_DIRECTORY = DOCUMENT_ROOT + "/.well-known/acme-challenge"
DIRECTORY_URL = "https://acme-v02.api.letsencrypt.org/directory"
CURRENT_STAGE = "initializing"
STATE = {"domains": list(DOMAINS), "ca": "Let's Encrypt", "events": []}

# Prevent any dependency's debug logging from exposing signed request bodies.
logging.disable(logging.CRITICAL)
sys.path.insert(0, str(RUNTIME))


def event(stage, **safe_values):
    global CURRENT_STAGE
    CURRENT_STAGE = stage
    entry = {"stage": stage, "at": dt.datetime.now(dt.timezone.utc).isoformat(), **safe_values}
    STATE["events"].append(entry)
    STATUS_FILE.parent.mkdir(exist_ok=True)
    STATUS_FILE.write_text(json.dumps(STATE, indent=2), encoding="utf-8")
    print(json.dumps(entry), flush=True)


def secure_private_directory():
    ignored = subprocess.run(
        ["git", "check-ignore", "--no-index", "artifacts/ssl/account-key.pem"],
        cwd=ROOT, capture_output=True, check=False,
    )
    if ignored.returncode != 0:
        raise RuntimeError("PrivateDirectoryMustBeGitIgnored")
    PRIVATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(PRIVATE, 0o700)
    if os.name == "nt":
        identity = subprocess.run(
            ["whoami", "/user", "/fo", "csv", "/nh"],
            capture_output=True, text=True, check=True,
        )
        sid = next(csv.reader(identity.stdout.strip().splitlines()))[1]
        if not re.fullmatch(r"S-1-[0-9-]+", sid):
            raise RuntimeError("UnableToRestrictPrivateDirectory")
        result = subprocess.run(
            ["icacls", str(PRIVATE), "/inheritance:r", "/grant:r",
             "*" + sid + ":(OI)(CI)F", "*S-1-5-18:(OI)(CI)F"],
            capture_output=True, check=False,
        )
        if result.returncode != 0:
            raise RuntimeError("UnableToRestrictPrivateDirectory")


def save_private(name, value):
    if Path(name).name != name:
        raise ValueError("InvalidPrivateFilename")
    path = PRIVATE / name
    data = value.encode("utf-8") if isinstance(value, str) else value
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)
    os.chmod(path, 0o600)


def probe_module():
    spec = importlib.util.spec_from_file_location("hosting_probe", ROOT / "scripts" / "hosting-probe.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def panel_post(path, fields=None, multipart=None):
    """Authentication and certificate material never enter URLs or process arguments."""
    allowed = {"/json-api/cpanel", "/execute/Fileman/upload_files", "/execute/SSL/install_ssl"}
    if path not in allowed or "?" in path:
        raise ValueError("UnexpectedPanelEndpoint")
    probe = probe_module()
    user, password = probe.credentials()
    auth = base64.b64encode((user + ":" + password).encode()).decode("ascii")
    headers = {"Authorization": "Basic " + auth, "Accept": "application/json"}
    if multipart:
        body, content_type = multipart
    else:
        body = urllib.parse.urlencode(fields or {}).encode("utf-8")
        content_type = "application/x-www-form-urlencoded"
    headers["Content-Type"] = content_type
    connection = http.client.HTTPSConnection(probe.HOST, probe.PORT, timeout=45, context=ssl.create_default_context())
    try:
        connection.request("POST", path, body=body, headers=headers)
        response = connection.getresponse()
        payload = response.read()
        if response.status != 200:
            raise RuntimeError("PanelHTTPFailure")
        result = json.loads(payload)
        return result.get("result", result)
    finally:
        connection.close()


def ensure_challenge_directories():
    probe = probe_module()
    parent = DOCUMENT_ROOT
    for name in (".well-known", "acme-challenge"):
        target = parent + "/" + name
        listing = probe.api("Fileman", "list_files", dir=target, show_hidden=1)
        if listing.get("status") != 1:
            result = panel_post("/json-api/cpanel", {
                "cpanel_jsonapi_apiversion": 2,
                "cpanel_jsonapi_module": "Fileman",
                "cpanel_jsonapi_func": "mkdir",
                "path": parent,
                "name": name,
                "permissions": "0755",
            })
            api_result = result.get("cpanelresult", {})
            if api_result.get("event", {}).get("result") != 1:
                raise RuntimeError("ChallengeDirectoryCreationFailed")
            listing = probe.api("Fileman", "list_files", dir=target, show_hidden=1)
            if listing.get("status") != 1:
                raise RuntimeError("ChallengeDirectoryNotReadable")
        parent = target


def upload_challenge(token, validation):
    if not re.fullmatch(r"[A-Za-z0-9_-]{16,256}", token):
        raise ValueError("UnsafeChallengeFilename")
    boundary = "nodeno-acme-" + secrets.token_hex(16)
    chunks = []
    for name, value in (("dir", CHALLENGE_DIRECTORY), ("overwrite", "0")):
        chunks.append(("--" + boundary + "\r\nContent-Disposition: form-data; name=\"" + name + "\"\r\n\r\n" + value + "\r\n").encode())
    chunks.append(("--" + boundary + "\r\nContent-Disposition: form-data; name=\"file-1\"; filename=\"" + token + "\"\r\nContent-Type: text/plain\r\n\r\n").encode())
    chunks.append(validation.encode("ascii"))
    chunks.append(("\r\n--" + boundary + "--\r\n").encode())
    result = panel_post("/execute/Fileman/upload_files", multipart=(b"".join(chunks), "multipart/form-data; boundary=" + boundary))
    if result.get("status") != 1:
        raise RuntimeError("ChallengeUploadFailed")


def verify_challenge_publicly(token, validation):
    results = []
    expected = validation.encode("ascii")
    for domain in DOMAINS:
        connection = http.client.HTTPConnection(domain, 80, timeout=15)
        try:
            connection.request("GET", "/.well-known/acme-challenge/" + token, headers={"Cache-Control": "no-cache"})
            response = connection.getresponse()
            actual = response.read(8192)
            passed = response.status == 200 and actual == expected
            results.append({"domain": domain, "http_status": response.status, "body_matches": passed})
            if not passed:
                raise RuntimeError("PublicChallengeDidNotMatch")
        finally:
            connection.close()
    event("public_challenge_verified", checks=results)


def certificate_metadata(fullchain, key_pem):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    certificates = x509.load_pem_x509_certificates(fullchain.encode())
    if len(certificates) < 2:
        raise RuntimeError("CertificateChainMissing")
    leaf = certificates[0]
    names = set(leaf.extensions.get_extension_for_class(x509.SubjectAlternativeName).value.get_values_for_type(x509.DNSName))
    if names != set(DOMAINS):
        raise RuntimeError("CertificateNamesMismatch")
    now = dt.datetime.now(dt.timezone.utc)
    if not leaf.not_valid_before_utc <= now < leaf.not_valid_after_utc:
        raise RuntimeError("CertificateNotCurrentlyValid")
    key = serialization.load_pem_private_key(key_pem, password=None)
    if leaf.public_key().public_numbers() != key.public_key().public_numbers():
        raise RuntimeError("CertificateKeyMismatch")
    for subject, issuer in zip(certificates, certificates[1:]):
        subject.verify_directly_issued_by(issuer)
    # Verify the issued chain against the platform trust roots before installation.
    from cryptography.x509.verification import PolicyBuilder, Store
    roots = [x509.load_der_x509_certificate(raw) for raw in ssl.create_default_context().get_ca_certs(binary_form=True)]
    verifier = PolicyBuilder().store(Store(roots)).time(now).build_server_verifier(x509.DNSName(DOMAINS[0]))
    verifier.verify(leaf, certificates[1:])
    metadata = {
        "domains": sorted(names),
        "issuer": leaf.issuer.rfc4514_string(),
        "not_before": leaf.not_valid_before_utc.isoformat(),
        "expires": leaf.not_valid_after_utc.isoformat(),
        "sha256": leaf.fingerprint(hashes.SHA256()).hex(),
        "chain_signatures_valid": True,
        "chain_trusted_before_install": True,
    }
    leaf_pem = leaf.public_bytes(serialization.Encoding.PEM).decode()
    chain_pem = "".join(cert.public_bytes(serialization.Encoding.PEM).decode() for cert in certificates[1:])
    return metadata, leaf_pem, chain_pem


def issue():
    import josepy
    from acme import challenges, client, crypto_util, messages
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    secure_private_directory()
    key_path = PRIVATE / "account-key.pem"
    if key_path.exists():
        account_private = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
    else:
        account_private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        save_private("account-key.pem", account_private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    network = client.ClientNetwork(josepy.JWKRSA(key=account_private), user_agent="NodenoCertificate/1.0", timeout=30)
    directory = client.ClientV2.get_directory(DIRECTORY_URL, network)
    acme = client.ClientV2(directory, net=network)
    account_path = PRIVATE / "account.json"
    if account_path.exists():
        account = messages.RegistrationResource.from_json(json.loads(account_path.read_text()))
        network.account = account
        acme.query_registration(account)
    else:
        # Contact is intentionally omitted; no unverified email is registered.
        account = acme.new_account(messages.NewRegistration.from_data(terms_of_service_agreed=True))
        network.account = account
        save_private("account.json", json.dumps(account.to_json()))
    event("acme_account_ready", contact_email_registered=False)
    cert_key_path = PRIVATE / "certificate-key.pem"
    if cert_key_path.exists():
        key_pem = cert_key_path.read_bytes()
    else:
        cert_private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        key_pem = cert_private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
        save_private("certificate-key.pem", key_pem)
    fullchain_path = PRIVATE / "fullchain.pem"
    if fullchain_path.exists():
        fullchain = fullchain_path.read_text()
        try:
            metadata, _, _ = certificate_metadata(fullchain, key_pem)
        except RuntimeError as error:
            if str(error) not in {"CertificateNamesMismatch", "CertificateNotCurrentlyValid"}:
                raise
            metadata = None
            event("existing_certificate_needs_replacement", reason=str(error))
        if metadata is not None and dt.datetime.fromisoformat(metadata["expires"]) > dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=30):
            event("existing_valid_certificate_reused", certificate=metadata)
            return fullchain, key_pem
    order = acme.new_order(crypto_util.make_csr(key_pem, list(DOMAINS)))
    event("acme_order_created", domain_count=len(order.authorizations))
    ensure_challenge_directories()
    pending = []
    manifest = []
    for authorization in order.authorizations:
        if authorization.body.status == messages.STATUS_VALID:
            continue
        challenge = next((c for c in authorization.body.challenges if isinstance(c.chall, challenges.HTTP01)), None)
        if challenge is None:
            raise RuntimeError("HTTP01NotOffered")
        response, validation = challenge.response_and_validation(network.key)
        token = challenge.chall.encode("token")
        upload_challenge(token, validation)
        verify_challenge_publicly(token, validation)
        manifest.append({"domain": authorization.body.identifier.value, "filename": token})
        pending.append((challenge, response))
    save_private("challenge-files.json", json.dumps(manifest, indent=2))
    for challenge, response in pending:
        acme.answer_challenge(challenge, response)
    event("acme_validation_started", challenge_count=len(pending))
    finalized = acme.poll_and_finalize(order, deadline=dt.datetime.now() + dt.timedelta(seconds=180))
    fullchain = finalized.fullchain_pem
    metadata, leaf_pem, chain_pem = certificate_metadata(fullchain, key_pem)
    save_private("fullchain.pem", fullchain)
    save_private("certificate.pem", leaf_pem)
    save_private("chain.pem", chain_pem)
    event("certificate_issued", certificate=metadata)
    return fullchain, key_pem


def install(fullchain, key_pem):
    probe = probe_module()
    before = probe.api("SSL", "installed_hosts")
    references = []
    for host in before.get("data") or []:
        if host.get("docroot") != DOCUMENT_ROOT:
            continue
        cert = host.get("certificate") or {}
        references.append({"servername": host.get("servername"), "domains": host.get("domains"), "certificate": {k: cert.get(k) for k in ("id", "is_self_signed", "not_after", "not_before", "domains", "issuer.commonName", "issuer.organizationName")}})
    save_private("before-installed-certificate.json", json.dumps(references, indent=2))
    metadata, leaf_pem, chain_pem = certificate_metadata(fullchain, key_pem)
    event("installing_certificate", prior_certificate_count=len(references), certificate=metadata)
    result = panel_post("/execute/SSL/install_ssl", {
        "domain": DOMAINS[0], "cert": leaf_pem,
        "key": key_pem.decode(), "cabundle": chain_pem,
    })
    if result.get("status") != 1:
        event("certificate_install_failed", status=result.get("status"), error_category="provider_rejected")
        raise RuntimeError("CertificateInstallFailed")
    data = result.get("data") or {}
    event("certificate_installed", status=1, action=data.get("action"), domain=data.get("domain"), ip=data.get("ip"))
    return metadata


def verify_trust(expected_fingerprint=None):
    checks = []
    for domain in DOMAINS:
        passed = None
        for attempt in range(15):
            connection = http.client.HTTPSConnection(domain, 443, timeout=12, context=ssl.create_default_context())
            try:
                connection.connect()
                fingerprint = hashlib.sha256(connection.sock.getpeercert(binary_form=True)).hexdigest()
                if expected_fingerprint and fingerprint != expected_fingerprint:
                    raise RuntimeError("OldCertificateStillActive")
                connection.request("GET", "/")
                response = connection.getresponse()
                response.read(8192)
                cross_domain_redirect = ".com.tr" in (response.getheader("Location") or "")
                if cross_domain_redirect:
                    raise RuntimeError("UnexpectedComTrRedirect")
                passed = {"domain": domain, "trusted_tls": True, "http_status": response.status, "redirect_to_com_tr": False, "sha256": fingerprint}
                break
            except (OSError, ssl.SSLError, RuntimeError):
                if attempt == 14:
                    raise
                time.sleep(2)
            finally:
                connection.close()
        checks.append(passed)
    event("public_https_verified", checks=checks)
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Issue and install the free certificate")
    parser.add_argument("--verify-only", action="store_true", help="Only verify public HTTPS")
    args = parser.parse_args()
    if args.verify_only:
        verify_trust()
    elif args.apply:
        event("starting", domains=list(DOMAINS))
        fullchain, key_pem = issue()
        metadata = install(fullchain, key_pem)
        verify_trust(metadata["sha256"])
        event("complete", trusted_https=True, challenge_files_retained=True)
    else:
        print(json.dumps({"mode": "plan", "domains": list(DOMAINS), "writes": ["unique HTTP-01 challenge files", "ACME account without contact email", "free certificate installation"], "private_directory_gitignored": True}))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Never stringify API/library exceptions: they can include request bodies.
        event("failed", phase=CURRENT_STAGE, error_type=type(exc).__name__)
        raise SystemExit(1)
