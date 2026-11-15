"""Read-only, TLS-verified cPanel discovery. Never prints authentication material."""
from __future__ import annotations

import base64
import concurrent.futures
import http.client
import json
from pathlib import Path
import ssl
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
HOST = "srvc77.trwww.com"
PORT = 2083


def credentials() -> tuple[str, str]:
    values = {}
    for line in (ROOT / ".env.local").read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return (
        values["nodenohome_com_tr_CPANEL_KULLANICI_ADI"],
        values["nodenohome_com_tr_CPANEL_KULLANICI_PAROLA"],
    )


def api(module: str, function: str, **params):
    """Only HTTPS UAPI requests; callers must select safe response fields."""
    user, password = credentials()
    auth = base64.b64encode((user + ":" + password).encode()).decode("ascii")
    conn = http.client.HTTPSConnection(HOST, PORT, timeout=25, context=ssl.create_default_context())
    try:
        path = "/execute/" + module + "/" + function
        if params:
            path += "?" + urllib.parse.urlencode(params)
        conn.request("GET", path, headers={"Authorization": "Basic " + auth, "Accept": "application/json"})
        response = conn.getresponse()
        payload = response.read()
        if response.status != 200:
            return {"status": 0, "http_status": response.status}
        try:
            result = json.loads(payload)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {"status": 0, "http_status": response.status, "non_json": True}
        return result.get("result", result)
    except Exception as exc:
        return {"status": 0, "exception_type": type(exc).__name__}
    finally:
        conn.close()


SAFE_DOMAIN_KEYS = {"domain", "servername", "serveralias", "documentroot", "document_root", "ip", "port", "phpversion", "php_version", "type", "redirect", "redirect_to", "redirect_www", "is_https_redirecting", "has_redirect"}


def domain_summary(value):
    if isinstance(value, list):
        return [domain_summary(x) for x in value]
    if isinstance(value, dict):
        return {k: domain_summary(v) for k, v in value.items() if k in SAFE_DOMAIN_KEYS or isinstance(v, (dict, list))}
    return value


def main():
    calls = [("DomainInfo", "list_domains", {}), ("DomainInfo", "domains_data", {"format": "hash"}), ("LangPHP", "php_get_installed_versions", {}), ("LangPHP", "php_get_vhost_versions", {}), ("Variables", "get_server_information", {})]
    def run(call):
        module, function, params = call
        result = api(module, function, **params)
        output = {"call": module + "/" + function, "status": result.get("status"), "http_status": result.get("http_status"), "exception_type": result.get("exception_type")}
        data = result.get("data")
        if module == "DomainInfo" and function == "list_domains" and isinstance(data, dict):
            output["domains"] = {k: v for k, v in data.items() if k in {"main_domain", "addon_domains", "parked_domains", "sub_domains"}}
        elif module == "DomainInfo":
            output["domains"] = domain_summary(data)
        elif module == "LangPHP" and function == "php_get_installed_versions":
            output["versions"] = data
        elif module == "LangPHP":
            output["vhosts"] = domain_summary(data)
        elif isinstance(data, dict):
            output["server"] = {k: v for k, v in data.items() if k in {"hostname", "servername", "cpanelversion", "cpanel_version", "version", "shared_ip", "ip"}}
        return output
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        for output in pool.map(run, calls):
            print(json.dumps(output, ensure_ascii=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"probe_error_type": type(exc).__name__}))
