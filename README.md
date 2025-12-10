# FastFlow - Backend Django

## Descripción
Este proyecto es el backend del sistema **FastFlow**, desarrollado en **Django**.  
Actualmente proporciona una API básica y una estructura inicial lista para futuras funcionalidades.  

---

> Nota: `node_modules/` y otros archivos temporales no se incluyen en el repositorio.

---

## Requisitos

- Python 3.10+  
- Django 4.x  
- Virtualenv recomendado  

Instalar dependencias:

```
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows
pip install -r backend/requirements.txt
```

Levantar el servidor
```
cd backend
python manage.py migrate     # Aplica migraciones
python manage.py runserver   # Levanta el servidor en localhost:8000
```

Tests
```
python manage.py test
```


[^1]: Base de datos de desarrollo: SQLite (db.sqlite3)
[^2]: No subir archivos sensibles ni dependencias (venv/, node_modules/) al repositorio.
