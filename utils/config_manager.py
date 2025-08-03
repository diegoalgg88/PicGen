import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

from .logger_config import logger



class ConfigManager:
    """
    Gestiona la carga y acceso a la configuración de la aplicación.

    Carga la configuración desde un archivo JSON y permite sobrescribir
    valores con variables de entorno.
    """
    def __init__(self, config_path: Path, script_dir: Path):
        """
        Inicializa el gestor de configuración.

        Args:
            config_path (Path): Ruta al archivo de configuración JSON.
            script_dir (Path): Directorio base del script para rutas relativas.
        """
        self.config_path = config_path
        self.script_dir = script_dir
        self.config = self._load_config()
        self._log_credential_status()

    def _load_config(self) -> Dict:
        """
        Carga la configuración desde un archivo JSON y establece valores por defecto.

        Returns:
            Dict: Diccionario con la configuración cargada y/o por defecto.
        """
        dotenv_path = self.script_dir / "config" / ".env"
        if load_dotenv(dotenv_path=dotenv_path):
            logger.info(f"Variables de entorno cargadas exitosamente desde: {dotenv_path}")
        else:
            logger.warning(f"No se encontró el archivo .env en: {dotenv_path}. Las credenciales deben estar en el entorno del sistema.")

        default_config = {
            'width': 1024, 'height': 768, 'model': 'flux', 'max_retries': 3, 
            'timeout': 120, 'output_dir': './generated_images', 'image_format': 'PNG',
            'enable_cache': True, 'batch_size': 5, 'model_edicion': 'kontext'
        }
        
        full_config_path = self.script_dir / self.config_path

        if full_config_path.exists():
            try:
                with open(full_config_path, 'r', encoding='utf-8') as f:
                    logger.info(f"Cargando configuración desde {full_config_path}")
                    user_config = json.load(f)
                    default_config.update(user_config)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error al cargar {full_config_path}: {e}. Usando configuración por defecto.")
        else:
            logger.warning(f"No se encontró {full_config_path}. Usando configuración por defecto.")
        
        # Sobrescribir con variables de entorno si existen
        default_config['POLLINATIONS_API_KEY'] = self._get_env_key('POLLINATIONS_API_KEY', default_config.get('api_token'))
        default_config['GOFILE_API_TOKEN'] = self._get_env_key('GOFILE_API_TOKEN', default_config.get('gofile_api_token'))
        default_config['GOFILE_FOLDER_ID'] = self._get_env_key('GOFILE_FOLDER_ID', default_config.get('gofile_folder_id'))

        return default_config

    def _get_env_key(self, env_var: str, default_value: Optional[str] = None) -> Optional[str]:
        """
        Obtiene una clave de las variables de entorno.

        Args:
            env_var (str): Nombre de la variable de entorno.
            default_value (Optional[str]): Valor por defecto si la variable de entorno no está presente.

        Returns:
            Optional[str]: El valor de la variable de entorno o el valor por defecto.
        """
        return os.getenv(env_var, default_value)

    def _log_credential_status(self):
        """
        Muestra el estado de las credenciales cargadas en el log.
        """
        api_token = self.get('POLLINATIONS_API_KEY')
        gofile_token = self.get('GOFILE_API_TOKEN')
        gofile_folder = self.get('GOFILE_FOLDER_ID')

        if api_token:
            logger.info(f"Token API de Pollinations: {api_token[:6]}...")
        else:
            logger.warning("Token API de Pollinations no configurado.")
            
        if gofile_token and gofile_folder:
            logger.info("Credenciales de GoFile configuradas para edición de imágenes.")
        else:
            logger.warning("Credenciales de GoFile no configuradas. La edición de imágenes podría fallar.")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración por clave.

        Args:
            key (str): La clave de configuración.
            default (Any): Valor por defecto si la clave no existe.

        Returns:
            Any: El valor de configuración o el valor por defecto.
        """
        return self.config.get(key, default)

    def save_config(self, new_settings: Dict):
        """
        Guarda la configuración actualizada en el archivo JSON.

        Args:
            new_settings (Dict): Un diccionario con los nuevos valores de configuración a guardar.
        """
        full_config_path = self.script_dir / self.config_path
        try:
            # Update only the keys provided in new_settings
            for key, value in new_settings.items():
                self.config[key] = value

            with open(full_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuración guardada en: {full_config_path}")
        except Exception as e:
            logger.error(f"Error al guardar la configuración en {full_config_path}: {e}")
