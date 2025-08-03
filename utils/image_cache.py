import hashlib
import json
import sqlite3
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional

from .logger_config import logger

class ImageCache:
    """
    Gestiona el caché de imágenes generadas y editadas.

    Almacena metadatos de imágenes (hash del prompt, ruta del archivo) en una base de datos SQLite
    para evitar regeneraciones o re-ediciones redundantes. Incluye funcionalidad de limpieza
    para eliminar entradas antiguas o archivos inexistentes.
    """
    def __init__(self, cache_dir: str = "./cache", max_age_days: int = 30):
        """
        Inicializa la caché de imágenes.

        Args:
            cache_dir (str): Directorio donde se almacenará la base de datos SQLite y, opcionalmente,
                             las imágenes cacheadas. Por defecto es './cache'.
            max_age_days (int): Número máximo de días que una entrada de caché se considera válida.
                                Después de este tiempo, se eliminará en la limpieza. Por defecto es 30.
        """
        self.db_path = Path(cache_dir) / "image_cache.db"
        self.db_path.parent.mkdir(exist_ok=True)
        self.max_age_days = max_age_days
        self._init_database()
        self.clean_cache(max_age_days)

    def _init_database(self):
        """
        Inicializa la tabla 'image_cache' en la base de datos SQLite si no existe.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS image_cache (prompt_hash TEXT PRIMARY KEY, filepath TEXT NOT NULL, last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")

    def _get_hash(self, prompt: str, parameters: Dict) -> str:
        """
        Genera un hash MD5 único para un prompt y sus parámetros.

        Este hash se utiliza como clave primaria en la caché para identificar de forma única
        una combinación de prompt y parámetros de generación/edición.

        Args:
            prompt (str): El prompt de texto utilizado para la generación o edición.
            parameters (Dict): Un diccionario de parámetros asociados (ej. width, height, model).

        Returns:
            str: El hash MD5 generado.
        """
        content = f"{prompt}_{json.dumps(parameters, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, prompt: str, parameters: Dict) -> Optional[str]:
        """
        Intenta recuperar una ruta de archivo de imagen de la caché.

        Si se encuentra una entrada válida para el prompt y los parámetros dados,
        y el archivo asociado aún existe, se actualiza su fecha de último acceso
        y se devuelve la ruta del archivo. De lo contrario, devuelve None.

        Args:
            prompt (str): El prompt de texto.
            parameters (Dict): Los parámetros asociados.

        Returns:
            Optional[str]: La ruta del archivo de imagen si se encuentra en caché y es válido, de lo contrario None.
        """
        prompt_hash = self._get_hash(prompt, parameters)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT filepath FROM image_cache WHERE prompt_hash = ?", (prompt_hash,))
            result = cursor.fetchone()
            if result and Path(result[0]).exists():
                cursor.execute("UPDATE image_cache SET last_accessed = CURRENT_TIMESTAMP WHERE prompt_hash = ?", (prompt_hash,))
                logger.info(f"Hit de caché encontrado.")
                return result[0]
        return None

    def store(self, prompt: str, parameters: Dict, filepath: str):
        """
        Almacena una nueva entrada en la caché de imágenes.

        Si ya existe una entrada para el mismo prompt y parámetros, se actualizará.

        Args:
            prompt (str): El prompt de texto.
            parameters (Dict): Los parámetros asociados.
            filepath (str): La ruta del archivo de imagen a almacenar.
        """
        prompt_hash = self._get_hash(prompt, parameters)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO image_cache (prompt_hash, filepath, last_accessed) VALUES (?, ?, CURRENT_TIMESTAMP)", (prompt_hash, filepath))
        logger.info(f"Imagen y prompt guardados en caché.")

    def clean_cache(self, days: int = 0):
        """
        Limpia la caché eliminando entradas antiguas o archivos inexistentes.

        Args:
            days (int): Si es mayor que 0, se usa como el límite de edad para la limpieza.
                        Si es 0, se usa el `max_age_days` configurado en la inicialización.
        """
        age_limit = days if days > 0 else self.max_age_days
        logger.info(f"Limpiando caché (entradas de más de {age_limit} días)...")
        deleted_count = 0
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cutoff_date = datetime.now() - timedelta(days=age_limit)
            
            # Eliminar entradas antiguas
            cursor.execute("SELECT prompt_hash, filepath FROM image_cache WHERE last_accessed < ?", (cutoff_date,))
            for prompt_hash, filepath in cursor.fetchall():
                if Path(filepath).exists():
                    try: 
                        os.remove(filepath)
                        logger.debug(f"Archivo cacheado eliminado: {filepath}")
                    except OSError as e:
                        logger.warning(f"No se pudo eliminar el archivo cacheado {filepath}: {e}")
                cursor.execute("DELETE FROM image_cache WHERE prompt_hash = ?", (prompt_hash,))
                deleted_count += 1
            
            # Eliminar entradas con archivos que ya no existen
            cursor.execute("SELECT prompt_hash, filepath FROM image_cache")
            for prompt_hash, filepath in cursor.fetchall():
                if not Path(filepath).exists():
                    cursor.execute("DELETE FROM image_cache WHERE prompt_hash = ?", (prompt_hash,))
                    deleted_count += 1
            conn.commit()
        if deleted_count > 0:
            logger.info(f"Limpieza de caché completada. {deleted_count} entradas eliminadas.")
        else:
            logger.info("No se encontraron entradas para limpiar en la caché.")
