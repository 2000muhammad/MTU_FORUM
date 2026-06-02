import hashlib
import hmac
import json
import time

import requests
from django.conf import settings

NOT_FOUND_MESSAGE = "Сервисе проблема с ПНФЛ (Не нашел сотрудника). Попробуйте позже. Или обратитесь в отдел кадров (Приказ, Перевод, и т.д.)."


class HRMClient:
    def __init__(self, base_url=None, endpoint_path=None, public_key=None, secret_type=None, secret_key=None, verify_ssl=None):
        from .models import ApiConfiguration

        config = ApiConfiguration.load()
        self.base_url = (base_url or config.hrm_base_url or settings.HRM_BASE_URL).rstrip("/")
        self.endpoint_path = endpoint_path or config.hrm_client_id or settings.HRM_ENDPOINT_PATH
        self.public_key = public_key or config.hrm_public_key or settings.HRM_PUBLIC_KEY
        self.secret_type = secret_type or config.hrm_secret_type or settings.HRM_SECRET_TYPE
        self.secret_key = secret_key or config.hrm_secret or settings.HRM_SECRET_KEY
        self.verify_ssl = config.hrm_verify_ssl if verify_ssl is None else verify_ssl

    def _signed_request(self, payload):
        body_str = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        timestamp = str(int(time.time()))
        message = timestamp + body_str
        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            msg=message.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-TIMESTAMP": timestamp,
            "X-PUBLIC-KEY": self.public_key,
            "X-SECRET-TYPE": self.secret_type,
            "X-SIGNATURE": signature,
        }
        path = self.endpoint_path if self.endpoint_path.startswith("/") else f"/{self.endpoint_path}"
        url = f"{self.base_url}{path}"
        response = requests.post(url, headers=headers, data=body_str, verify=self.verify_ssl, timeout=20)
        response.raise_for_status()
        return response.json()

    def check_worker_by_pin(self, pin: str | int):
        if not self.base_url or not self.public_key or not self.secret_type or not self.secret_key:
            return {"found": False, "message": NOT_FOUND_MESSAGE}
        return self._signed_request({"pin": str(pin)})

    def find_employee(self, pnfl: str, phone: str = ""):
        data = self.check_worker_by_pin(pnfl)
        worker = self._extract_worker(data)
        if not worker:
            return {"found": False, "message": NOT_FOUND_MESSAGE, "raw": data}
        position_data = self._current_position(worker)
        full_name = self._full_name(worker)
        last_name, first_name, middle_name = self._name_parts(worker, full_name)
        organization = self._position_company(position_data) or self._name_value(self._first(worker, "organization", "company", "org_name"))
        return {
            "found": True,
            "pnfl": self._pinfl(worker) or str(pnfl or "").strip(),
            "employee_pinfl": self._pinfl(worker) or str(pnfl or "").strip(),
            "full_name": full_name,
            "first_name": first_name,
            "last_name": last_name,
            "middle_name": middle_name,
            "birth_date": self._birth_date(worker),
            "branch": self._position_branch(position_data) or self._name_value(self._first(worker, "branch", "filial", "filial_name")),
            "organization": organization,
            "company": organization,
            "department": self._position_department(position_data),
            "position": self._position_name(position_data) or self._name_value(self._first(worker, "position", "position_name", "job", "job_title")),
            "phone": self._phone(worker) or self._first(worker, "phone", "phone_number", default=phone),
            "photo": self._photo(worker) or self._photo_value(self._first(worker, "photo", "photo_url", "avatar", "avatar_url", "image", "photo_base64", "image_base64")),
            "raw": data,
        }

    def _extract_worker(self, data):
        if not isinstance(data, dict):
            return None
        if data.get("found") is False or data.get("success") is False or data.get("error") is True:
            return None
        for key in ("data", "worker", "employee", "result"):
            value = data.get(key)
            if isinstance(value, dict):
                nested = self._extract_worker(value)
                return nested or value
        worker_keys = ("full_name", "fio", "name", "first_name", "last_name", "middle_name", "position", "positions", "organization", "company", "pin")
        return data if any(key in data for key in worker_keys) else None

    def _first(self, data, *keys, default=""):
        for key in keys:
            value = data.get(key)
            if value not in (None, ""):
                return value
        return default

    def _full_name(self, worker):
        ready_name = self._first(worker, "full_name", "fio", "employee_name")
        if ready_name:
            return str(ready_name).strip()
        parts = [self._first(worker, "last_name"), self._first(worker, "first_name"), self._first(worker, "middle_name")]
        return " ".join(str(part).strip() for part in parts if part not in (None, ""))

    def _name_parts(self, worker, full_name):
        first_name = str(self._first(worker, "first_name", "firstname", "given_name") or "").strip()
        last_name = str(self._first(worker, "last_name", "lastname", "surname") or "").strip()
        middle_name = str(self._first(worker, "middle_name", "patronymic", "father_name", "second_name") or "").strip()
        if first_name or last_name or middle_name:
            return last_name, first_name, middle_name
        parts = [part for part in str(full_name or "").split() if part]
        if len(parts) >= 3:
            return parts[0], parts[1], " ".join(parts[2:])
        if len(parts) == 2:
            return parts[0], parts[1], ""
        return "", parts[0] if parts else "", ""

    def _pinfl(self, worker):
        return str(self._first(worker, "pin", "pinfl", "pnfl", "jshshir", "jshshir_code", "personal_number") or "").strip()

    def _birth_date(self, worker):
        return str(self._first(worker, "birth_date", "birthday", "birthdate", "date_birth", "date_of_birth") or "").strip()

    def _current_position(self, worker):
        positions = worker.get("positions")
        if not isinstance(positions, list) or not positions:
            return {}
        for item in positions:
            if isinstance(item, dict) and item.get("current") is True:
                return item
        return next((item for item in positions if isinstance(item, dict)), {})

    def _position_company(self, position_data):
        organization = position_data.get("organization") if isinstance(position_data, dict) else None
        return self._name_value(organization)

    def _position_department(self, position_data):
        department = position_data.get("department") if isinstance(position_data, dict) else None
        return self._name_value(department)

    def _position_branch(self, position_data):
        if not isinstance(position_data, dict):
            return ""
        return self._name_value(position_data.get("branch")) or self._name_value(position_data.get("filial"))

    def _position_name(self, position_data):
        if not isinstance(position_data, dict):
            return ""
        return self._name_value(position_data.get("position")) or self._name_value(position_data)

    def _phone(self, worker):
        phones = worker.get("phones")
        if isinstance(phones, list) and phones:
            return self._format_uz_phone(phones[0])
        return ""

    def _photo(self, worker):
        photos = worker.get("photos")
        if not isinstance(photos, list):
            return ""
        selected = next((item for item in photos if isinstance(item, dict) and item.get("current") is True), None)
        selected = selected or next((item for item in photos if isinstance(item, dict)), None)
        return self._photo_value(selected) if selected else ""

    def _photo_value(self, value):
        if isinstance(value, dict):
            for key in ("photo", "url", "photo_url", "avatar", "avatar_url", "image", "base64", "photo_base64", "image_base64"):
                photo = self._photo_value(value.get(key))
                if photo:
                    return photo
            return ""
        photo = str(value or "").strip()
        if photo.startswith("/") and self.base_url:
            return f"{self.base_url}{photo}"
        return photo

    def _name_value(self, value):
        if isinstance(value, dict):
            return str(value.get("name") or "").strip()
        return str(value or "").strip()

    def _format_uz_phone(self, value):
        digits = "".join(ch for ch in str(value) if ch.isdigit())
        if len(digits) == 9:
            digits = f"998{digits}"
        if len(digits) == 12 and digits.startswith("998"):
            return f"+998-{digits[3:5]}-{digits[5:8]}-{digits[8:10]}-{digits[10:12]}"
        return str(value or "").strip()
