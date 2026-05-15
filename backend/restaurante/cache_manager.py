"""
Cache Manager para FastFlow
Gestiona caché de Redis para queries y resultados de agentes
"""

import json
from typing import Any, Optional, Union
from functools import wraps

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from django.core.cache import cache
from django.conf import settings


class CacheManager:
    """Gestor centralizado de caché con Redis/Django cache"""
    
    # TTL (Time To Live) en segundos
    TTL_CONFIG = {
        'recomendaciones': 300,           # 5 minutos
        'analisis_ingredientes': 600,     # 10 minutos
        'sentimiento': 1800,              # 30 minutos
        'sugerencia_mesa': 600,           # 10 minutos
        'tendencias': 3600,               # 1 hora
        'predicciones': 1800,             # 30 minutos
        'mercado': 7200,                  # 2 horas
        'optimizacion': 3600,             # 1 hora
        'default': 300                    # 5 minutos por defecto
    }
    
    def __init__(self):
        """Inicializar cache manager"""
        self.redis_client = None
        if REDIS_AVAILABLE:
            try:
                redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
            except Exception:
                self.redis_client = None
    
    def get_key(self, prefix: str, **kwargs) -> str:
        """Generar clave de caché"""
        key_parts = [prefix]
        for k, v in sorted(kwargs.items()):
            if v is not None:
                key_parts.append(f"{k}:{v}")
        return "|".join(key_parts)
    
    def get(self, prefix: str, **kwargs) -> Optional[Any]:
        """Obtener valor del caché"""
        key = self.get_key(prefix, **kwargs)
        
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception:
                pass
        
        # Fallback a Django cache
        return cache.get(key)
    
    def set(self, prefix: str, value: Any, ttl: Optional[int] = None, **kwargs) -> bool:
        """Guardar valor en caché"""
        key = self.get_key(prefix, **kwargs)
        
        # Usar TTL configurado o default
        if ttl is None:
            ttl = self.TTL_CONFIG.get(prefix, self.TTL_CONFIG['default'])
        
        try:
            if self.redis_client:
                try:
                    self.redis_client.setex(key, ttl, json.dumps(value))
                    return True
                except Exception:
                    pass
            
            # Fallback a Django cache
            cache.set(key, value, ttl)
            return True
        except Exception:
            return False
    
    def delete(self, prefix: str, **kwargs) -> bool:
        """Eliminar valor del caché"""
        key = self.get_key(prefix, **kwargs)
        
        try:
            if self.redis_client:
                try:
                    self.redis_client.delete(key)
                    return True
                except Exception:
                    pass
            
            # Fallback a Django cache
            cache.delete(key)
            return True
        except Exception:
            return False
    
    def clear_prefix(self, prefix: str) -> bool:
        """Limpiar todas las claves con un prefijo"""
        try:
            if self.redis_client:
                try:
                    pattern = f"{prefix}|*"
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        self.redis_client.delete(*keys)
                    return True
                except Exception:
                    pass
            
            # Django cache no soporta clear por patrón eficientemente
            return True
        except Exception:
            return False
    
    def invalidate_agent_cache(self, agent_name: str) -> bool:
        """Invalidar caché de un agente específico"""
        return self.clear_prefix(f"agent_{agent_name}")
    
    def cache_decorator(self, prefix: str, ttl: Optional[int] = None):
        """Decorador para cachear resultados de funciones"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Crear clave basada en argumentos
                cache_key = self.get_key(
                    f"func_{prefix}_{func.__name__}",
                    args=str(args),
                    kwargs=str(sorted(kwargs.items()))
                )
                
                # Intentar obtener del caché
                cached = self.get(cache_key)
                if cached is not None:
                    return cached
                
                # Ejecutar función
                result = func(*args, **kwargs)
                
                # Guardar en caché
                self.set(cache_key, result, ttl)
                
                return result
            return wrapper
        return decorator


# Instancia global del cache manager
cache_manager = CacheManager()


def get_cache_stats() -> dict:
    """Obtener estadísticas del caché"""
    stats = {
        'redis_available': cache_manager.redis_client is not None,
        'ttl_config': cache_manager.TTL_CONFIG
    }
    
    if cache_manager.redis_client:
        try:
            info = cache_manager.redis_client.info()
            stats['redis_memory_used'] = info.get('used_memory_human', 'N/A')
            stats['redis_connected_clients'] = info.get('connected_clients', 0)
        except Exception:
            pass
    
    return stats
