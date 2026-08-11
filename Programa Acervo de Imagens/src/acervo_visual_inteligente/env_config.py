"""Carregamento leve de variaveis locais de ambiente.

Evita depender de python-dotenv no executavel. O arquivo preferencial e
`.env.local`, localizado ao lado do EXE ou na pasta do pacote/projeto.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


DEFAULT_FIREBASE_ENV = {
    "FIREBASE_API_KEY": "AIzaSyBD6TkUg5F_j9C2_VK6pWf-z34Iyszp0LE",
    "FIREBASE_AUTH_DOMAIN": "uniasselvi-digital.firebaseapp.com",
    "FIREBASE_DATABASE_URL": "https://uniasselvi-digital.firebaseio.com",
    "FIREBASE_PROJECT_ID": "uniasselvi-digital",
    "FIREBASE_STORAGE_BUCKET": "uniasselvi-digital.appspot.com",
    "FIREBASE_MESSAGING_SENDER_ID": "540573107988",
    "FIREBASE_APP_ID": "1:540573107988:web:59af50ad04f91284fb2401",
    "FIREBASE_MEASUREMENT_ID": "G-BYSN6ETYMV",
}


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def candidate_env_paths() -> list[Path]:
    base = app_dir()
    paths = [
        base / ".env.local",
        base.parent / ".env.local",
        Path.cwd() / ".env.local",
    ]

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        paths.insert(0, Path(meipass) / ".env.local")

    unique: list[Path] = []
    seen = set()
    for path in paths:
        key = str(path).lower()
        if key not in seen:
            unique.append(path)
            seen.add(key)
    return unique


def load_env_file(path: Path) -> bool:
    if not path.exists():
        return False

    try:
        lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    except OSError:
        return False

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and value and not os.getenv(key):
            os.environ[key] = value
    return True


def load_local_env() -> None:
    for path in candidate_env_paths():
        if load_env_file(path):
            break

    for key, value in DEFAULT_FIREBASE_ENV.items():
        if not os.getenv(key):
            os.environ[key] = value
