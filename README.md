# FastFlow - Quickstart Docker

Este proyecto incluye frontend (React), backend (Django) y base de datos MySQL en contenedores.

## Comienzo rapido (Docker)

Desde la raiz del proyecto:

```bash
docker compose up --build -d
```

El backend ejecuta automaticamente en cada arranque:
- `python manage.py migrate`
- `python manage.py seed_fastflow`

## URLs

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- MySQL: localhost:3306

## Ver logs

```bash
docker compose logs -f backend frontend db
```

Borrar contenedores:

```bash
docker compose down -v
```


## Credenciales demo

- Admin: `admin` / `admin1234`
- Empleado: `empleado1` / `empleado1234`
- Empleado: `empleado2` / `empleado1234`
- Cliente: `cliente1` / `cliente1234`
- Cliente: `cliente2` / `cliente1234`
- Sembrados datos inventados en la base de datos.

## Documentacion adicional

- Ejecucion sin Docker: [docs/README.md](docs/README.md)
- Deploy sin Docker (hosting): [docs/DEPLOY.md](docs/DEPLOY.md)
- Documentacion tecnica: carpeta `docs/`
