# FastFlow - Deploy sin Docker (hosting de pago)

Esta guía asume un hosting típico tipo VPS / servidor (Linux) donde puedes ejecutar un proceso WSGI (Gunicorn) y servir estáticos.

## Backend (Django) con Gunicorn

### 1) Requisitos del servidor

- Python 3.12
- MySQL 8 (local o gestionado)
- (Opcional) Nginx como reverse proxy

### 2) Instalar dependencias

Desde la carpeta `backend/`:

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3) Variables de entorno

Crea `backend/.env` en el servidor (no lo subas a git) basándote en `backend/.env.example`.

Imprescindibles para producción:

- `DEBUG=False`
- `SECRET_KEY=<una clave larga y secreta>`
- `ALLOWED_HOSTS=<tu-dominio.com,tu-ip>`
- `CSRF_TRUSTED_ORIGINS=https://tu-dominio.com`
- `CORS_ALLOWED_ORIGINS=https://tu-frontend.com` (si aplica)
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`

### 4) Migraciones + seed (opcional)

```bash
python manage.py migrate
python manage.py seed_fastflow  # opcional (ojo: hace flush)
```

### 5) Estáticos

Con `whitenoise` configurado, genera estáticos versionados:

```bash
python manage.py collectstatic --noinput
```

### 6) Ejecutar Gunicorn

Desde `backend/`:

```bash
gunicorn fastflow_backend.wsgi:application --bind 0.0.0.0:8000
```

Recomendación: ejecutar Gunicorn con systemd (servicio) y poner Nginx delante.

## Frontend (React)

### Opción A: servirlo como estático

Desde `frontend/`:

```bash
npm ci
npm run build
```

Publica el contenido de `frontend/build/` en tu hosting (Nginx/Apache/hosting estático).

### Variables de entorno del frontend

- `REACT_APP_API_BASE_URL`: debe apuntar al backend publicado, por ejemplo `https://api.tu-dominio.com/restaurante`

