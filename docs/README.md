# FastFlow - Ejecucion sin Docker

Esta guia explica como iniciar FastFlow localmente sin contenedores.

## Requisitos

- Python 3.12.x
- Node.js 20+
- MySQL 8.x local

## 1) Base de datos MySQL

Crea base de datos y usuario (ejemplo):

```sql
DROP DATABASE IF EXISTS fastflow;
CREATE DATABASE fastflow CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'fastflow'@'localhost' IDENTIFIED BY 'fastflow123';
GRANT ALL PRIVILEGES ON fastflow.* TO 'fastflow'@'localhost';
FLUSH PRIVILEGES;
```

Alternativa (solo desarrollo): si quieres arrancar sin instalar MySQL, puedes usar SQLite
poniendo `DB_ENGINE=sqlite` en `backend/.env`. (Para producción se recomienda MySQL.)

## 2) Backend (Django)

Desde la raiz del proyecto:

```bash
cd backend
python3.12 -m venv ../venv
source ../venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

En Windows (PowerShell), el equivalente suele ser:

```powershell
cd backend
py -3.12 -m venv ..\\venv
..\\venv\\Scripts\\Activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Configura variables de entorno en `backend/.env` (recomendado: copiar `backend/.env.example` y ajustar):

```env
DEBUG=True
SECRET_KEY=dev-secret-key
DB_NAME=fastflow
DB_USER=fastflow
DB_PASSWORD=fastflow123
DB_HOST=127.0.0.1
DB_PORT=3306
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Ejecuta migraciones, seed y servidor:

```bash
python manage.py makemigrations
python manage.py makemigrations restaurante
python manage.py migrate
python manage.py seed_fastflow
python manage.py runserver
```

Backend en: http://127.0.0.1:8000

Nota: `seed_fastflow` ejecuta un `flush` (borra datos) antes de sembrar.

## 3) Frontend (React)

En otra terminal, desde la raiz del proyecto:

```bash
cd frontend
npm install
npm start
```

Frontend en: http://localhost:3000

## 4) Verificacion rapida

- Abre http://localhost:3000
- Comprueba que el frontend carga
- Comprueba backend en http://127.0.0.1:8000

## Credenciales demo

- Admin: `admin` / `admin1234`
- Empleado: `empleado1` / `empleado1234`
- Empleado: `empleado2` / `empleado1234`
- Cliente: `cliente1` / `cliente1234`
- Cliente: `cliente2` / `cliente1234`
- Sembrados datos inventados en la base de datos.

## Problemas comunes

- Error de conexion a MySQL: revisa `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`.
- Puerto ocupado en backend: cambia puerto con `python manage.py runserver 8001`.
- Puerto ocupado en frontend: React pedira usar otro puerto automaticamente.
- `django.db.utils.ProgrammingError: (1146, \"Table 'fastflow.perfiles_usuarios' doesn't exist\")` al ejecutar `python manage.py seed_fastflow`:
  - Causa tipica: migraciones de `restaurante` no aplicadas (por ejemplo `python manage.py showmigrations restaurante` muestra `(no migrations)` o no aparece `0001_initial`).
  - Solucion:
    - Asegura que existen `backend/restaurante/__init__.py` y `backend/restaurante/migrations/__init__.py`.
    - Ejecuta `python manage.py migrate` y vuelve a lanzar `python manage.py seed_fastflow`.
  - Si alternas entre Docker y local: asegúrate de ejecutar `migrate` en el mismo entorno/BD donde corres el seed.
