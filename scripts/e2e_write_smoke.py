#!/usr/bin/env python3
"""
Smoke de escritura contra la API (producción/staging).
Uso: BASE_URL=http://146.190.37.214/api/ ADMIN_PASS=admin123 python scripts/e2e_write_smoke.py
"""
import base64
import io
import os
import sys

import requests

BASE = os.environ.get("BASE_URL", "http://146.190.37.214/api/").rstrip("/") + "/"
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin123")
CARNET = os.environ.get("TEST_CARNET", "101260001")


def main() -> int:
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})

    r = s.post(BASE + "auth/login/", json={"username": ADMIN_USER, "password": ADMIN_PASS}, timeout=30)
    if r.status_code != 200:
        print("FAIL login", r.status_code, r.text[:300])
        return 1
    token = r.json()["access"]
    s.headers["Authorization"] = f"Bearer {token}"
    print("OK login")

    r = s.get(BASE + "students/students/", params={"search": CARNET}, timeout=30)
    r.raise_for_status()
    results = r.json().get("results", [])
    if not results:
        print("FAIL no estudiante carnet", CARNET)
        return 1
    student = results[0]
    sid = student["id"]
    print("OK estudiante", CARNET, sid)

    # 1) PATCH estudiante (dirección)
    new_addr = "Av. Reforma 222, Col. Centro, CDMX (verificado QA " + sid[:8] + ")"
    r = s.patch(BASE + f"students/students/{sid}/", json={"address": new_addr}, timeout=30)
    ok = r.status_code == 200 and r.json().get("address") == new_addr
    print(("OK" if ok else "FAIL"), "PATCH estudiante.address", r.status_code, r.text[:200] if not ok else "")

    # 2) Documento: subir PNG mínimo + aprobar (primer documento aún no aprobado)
    r = s.get(BASE + "students/documents/", params={"student": sid}, timeout=30)
    r.raise_for_status()
    docs = r.json().get("results", [])
    pending = [d for d in docs if d.get("status") != "APROBADO"]
    if not pending:
        print("SKIP documento upload (todos los documentos ya están aprobados)")
    else:
        doc_id = pending[0]["id"]
        dtype = pending[0].get("document_type", "doc")
        png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        files = {"file": (f"qa_{dtype}.png", io.BytesIO(base64.b64decode(png_b64)), "image/png")}
        r = s.post(BASE + f"students/documents/{doc_id}/upload_file/", files=files, timeout=60)
        print(
            ("OK" if r.status_code == 200 else "FAIL"),
            f"POST upload_file {dtype}",
            r.status_code,
            r.text[:250] if r.status_code != 200 else "",
        )

        if r.status_code == 200:
            r2 = s.patch(
                BASE + f"students/documents/{doc_id}/update_status/",
                json={"status": "APROBADO", "notes": "OK revisión QA automatizada"},
                timeout=30,
            )
            print(
                ("OK" if r2.status_code == 200 else "FAIL"),
                "PATCH update_status APROBADO",
                r2.status_code,
                r2.text[:250] if r2.status_code != 200 else "",
            )

    # 3) Pago en efectivo (tipo con código numérico simple)
    r = s.get(BASE + "payments/payment-types/", timeout=30)
    r.raise_for_status()
    types = r.json().get("results", r.json() if isinstance(r.json(), list) else [])
    # Preferir colegiatura 102 (evita 010/011 que exigen semestre en reglas de negocio)
    pt = next((t for t in types if str(t.get("code", "")) == "102"), None)
    if not pt:
        pt = next((t for t in types if str(t.get("code", "")) == "101"), None)
    if not pt:
        pt = types[0] if types else None
    if not pt:
        print("FAIL sin tipos de pago")
        return 1
    pay_body = {
        "student": sid,
        "payment_type": str(pt["id"]),
        "payment_method": "EFECTIVO",
        "amount": "150.00",
        "year": 2026,
        "month": 4,
        "notes": "Pago QA escritura",
    }
    r = s.post(BASE + "payments/payments/", json=pay_body, timeout=60)
    print(("OK" if r.status_code in (200, 201) else "FAIL"), "POST pago", r.status_code, r.text[:400] if r.status_code not in (200, 201) else f"id={r.json().get('id')}")

    # 4) Inscripción: PATCH notas u observación si existe campo notes en enrollment
    r = s.get(BASE + "students/enrollments/", params={"student": sid}, timeout=30)
    r.raise_for_status()
    enrs = r.json().get("results", [])
    if enrs:
        eid = enrs[0]["id"]
        r = s.patch(BASE + f"students/enrollments/{eid}/", json={"institutional_id": CARNET}, timeout=30)
        print(("OK" if r.status_code == 200 else "FAIL"), "PATCH enrollment.institutional_id", r.status_code, r.text[:200] if r.status_code != 200 else "")

    # 5) Exportación Moodle (POST; puede quedar solo cabecera si no hay credenciales Moodle)
    r = s.post(BASE + "exports/exports/export_students/", json={"student_ids": [sid]}, timeout=60)
    ok_csv = r.status_code == 200 and "text/csv" in (r.headers.get("Content-Type") or "")
    print(("OK" if ok_csv else "FAIL"), "POST export_students CSV", r.status_code, r.headers.get("Content-Type", "")[:60])

    print("\nListo. Revisa en el panel: estudiante", CARNET, ", documentos, pagos y exportación.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
