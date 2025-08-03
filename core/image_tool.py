import json
import random
import re
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import quote_plus

import requests
from datetime import datetime

from utils.logger_config import logger
from utils.config_manager import ConfigManager
from utils.image_cache import ImageCache
from utils.prompt_templates import PromptTemplates

class ImageTool:
    """
    Clase principal para interactuar con la API de Pollinations AI para generación y edición de imágenes.

    Gestiona la configuración, autenticación, solicitudes a la API, guardado de imágenes,
    traducción de prompts y subida a servicios temporales como GoFile.
    """
    BASE_URL = "https://image.pollinations.ai/prompt/"

    def __init__(self, config_manager: ConfigManager, script_dir: Path):
        """
        Inicializa la herramienta de imagen.

        Args:
            config_manager (ConfigManager): Instancia del gestor de configuración.
            script_dir (Path): Directorio base del script para resolver rutas relativas.
        """
        self.config_manager = config_manager
        self.script_dir = script_dir

        self.api_token = self.config_manager.get('POLLINATIONS_API_KEY')
        self.gofile_token = self.config_manager.get('GOFILE_API_TOKEN')
        self.gofile_folder = self.config_manager.get('GOFILE_FOLDER_ID')

        self.cache = ImageCache() if self.config_manager.get('enable_cache') else None
        self.templates = PromptTemplates(script_dir)
        self.stats = {'images_generated': 0, 'cache_hits': 0, 'total_generation_time': 0, 'errors': 0}

        self._setup_directories()

        logger.info(f"Herramienta de Imagen inicializada. API Token: {self.api_token[:6]}..." if self.api_token else "Herramienta de Imagen inicializada. API Token no configurado.")

    def _setup_directories(self):
        """
        Asegura que los directorios necesarios para la salida y caché existan.
        """
        Path(self.config_manager.get('output_dir', 'generated_images')).mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        Path("cache").mkdir(exist_ok=True)

    def _make_request(self, url: str, params: Dict, headers: Dict) -> requests.Response:
        """
        Realiza una petición GET a la API con manejo de reintentos y errores.

        Args:
            url (str): La URL a la que se realizará la petición.
            params (Dict): Parámetros de la URL.
            headers (Dict): Cabeceras de la petición.

        Returns:
            requests.Response: El objeto de respuesta de la petición exitosa.

        Raises:
            ConnectionError: Si la petición falla después de múltiples reintentos.
            ValueError: Si la respuesta de la API no es una imagen válida.
        """
        max_retries = self.config_manager.get('max_retries', 3)
        timeout = self.config_manager.get('timeout', 120)

        for attempt in range(max_retries):
            try:
                logger.debug(f"Intento {attempt + 1}: GET {url}")
                logger.debug(f"Params: {params}")
                logger.debug(f"Headers: {headers}")

                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=timeout,
                    stream=True
                )

                response.raise_for_status()

                content_type = response.headers.get('content-type', '')
                if 'image' not in content_type and 'octet-stream' not in content_type:
                    raise ValueError(f"La respuesta no es una imagen válida. Content-Type: {content_type}")

                return response

            except requests.exceptions.HTTPError as e:
                logger.error(f"Error HTTP: {e.response.status_code} - {e.response.text[:200]}")
                if e.response.status_code < 500:
                    break
            except requests.exceptions.RequestException as e:
                logger.warning(f"Intento {attempt + 1} fallido: {e}")

            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

        raise ConnectionError("Falló la petición después de múltiples intentos.")

    def _save_image(self, response: requests.Response, filename: str) -> str:
        """
        Guarda la respuesta de la imagen en un archivo local.

        Args:
            response (requests.Response): Objeto de respuesta que contiene los datos de la imagen.
            filename (str): Nombre del archivo para guardar la imagen.

        Returns:
            str: La ruta absoluta del archivo guardado.

        Raises:
            IOError: Si ocurre un error al guardar el archivo.
        """
        output_dir = Path(self.config_manager.get('output_dir', 'generated_images'))
        output_path = output_dir / filename

        try:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"Imagen guardada en: {output_path.resolve()}")
            return str(output_path)
        except IOError as e:
            logger.error(f"No se pudo guardar la imagen en {output_path}: {e}")
            raise

    def _generate_filename(self, prompt: str) -> str:
        """
        Genera un nombre de archivo único y limpio basado en el prompt y la fecha/hora actual.

        Args:
            prompt (str): El prompt original de la imagen.

        Returns:
            str: El nombre de archivo generado.
        """
        clean_prompt = re.sub(r'[^\w\s-]', '', prompt.lower()).strip().replace(' ', '_')[:50]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{clean_prompt}_{timestamp}.{self.config_manager.get('image_format', 'png').lower()}"

    def _translate_prompt(self, text: str) -> str:
        """
        Traduce un prompt de texto a inglés si contiene caracteres no ASCII (asumiendo español).

        Args:
            text (str): El texto del prompt a traducir.

        Returns:
            str: El texto traducido o el original si no se necesita traducción o falla.
        """
        # Truncate the text to a maximum of 490 characters to avoid API errors
        text = text[:490]

        # Check if the text contains non-ASCII characters, which suggests it might not be in English
        if not all(ord(c) < 128 for c in text):
            logger.info(f"Traduciendo prompt: '{text}'")
            try:
                url = "https://api.mymemory.translated.net/get"
                params = {'q': text, 'langpair': 'es|en'}
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                translated = data['responseData']['translatedText']
                logger.info(f"Traducido a: '{translated}'")
                return translated
            except Exception as e:
                logger.error(f"Falló la traducción: {e}. Usando prompt original.")
        return text

    def _upload_to_gofile(self, image_path: str) -> Optional[str]:
        """
        Sube una imagen a GoFile y devuelve su URL pública.

        Requiere que GOFILE_API_TOKEN y GOFILE_FOLDER_ID estén configurados.

        Args:
            image_path (str): Ruta local de la imagen a subir.

        Returns:
            Optional[str]: URL pública de la imagen en GoFile, o None si falla.
        """
        if not self.gofile_token or not self.gofile_folder:
            logger.error("Credenciales de GoFile no configuradas. La subida fallará.")
            return None

        logger.info(f"Subiendo {image_path} a GoFile...")
        headers = {'Authorization': f'Bearer {self.gofile_token}'}

        try:
            server_resp = requests.get("https://api.gofile.io/servers", headers=headers, timeout=15).json()
            if server_resp['status'] != 'ok':
                raise ConnectionError("No se pudo obtener un servidor de GoFile.")
            server = server_resp['data']['servers'][0]['name']

            with open(image_path, 'rb') as f:
                files = {'file': (Path(image_path).name, f)}
                data = {'folderId': self.gofile_folder}
                upload_resp = requests.post(f"https://{server}.gofile.io/uploadFile", files=files, data=data, headers=headers, timeout=60).json()

            if upload_resp['status'] == 'ok':
                content_id = upload_resp['data']['id']
                file_name = upload_resp['data']['name']
                direct_link = f"https://{server}.gofile.io/download/{content_id}/{quote_plus(file_name)}"
                logger.info(f"Subida exitosa. Enlace directo: {direct_link}")
                return direct_link
            else:
                raise ConnectionError(f"Error en la subida a GoFile: {upload_resp}")
        except Exception as e:
            logger.error(f"Falló la subida a GoFile: {e}")
            return None

    def generate_image(self, prompt: str, **kwargs) -> Optional[str]:
        """
        Genera una imagen utilizando la API de Pollinations AI.

        Args:
            prompt (str): El prompt de texto para la generación de la imagen.
            **kwargs: Parámetros adicionales para la generación (ej. width, height, model, seed).

        Returns:
            Optional[str]: La ruta absoluta del archivo guardado si la generación fue exitosa, None en caso contrario.
        """
        start_time = time.time()
        params = {
            "width": kwargs.get('width', self.config_manager.get('width')),
            "height": kwargs.get('height', self.config_manager.get('height')),
            "model": kwargs.get('model', self.config_manager.get('model')),
            "seed": kwargs.get('seed', random.randint(0, 1_000_000_000)),
            "nologo": not self.config_manager.get('add_logo', True) # Use nologo parameter, default to False if not specified in config
        }

        if self.cache and (cached_path := self.cache.get(prompt, params)):
            self.stats['cache_hits'] += 1
            logger.info(f"Imagen cargada desde caché: {cached_path}")
            return cached_path

        logger.info(f"Generando imagen para el prompt: '{prompt}'")
        translated_prompt = self._translate_prompt(prompt)
        encoded_prompt = quote_plus(translated_prompt)

        url = f"{self.BASE_URL}{encoded_prompt}"

        headers = {}
        if self.api_token:
            headers['Authorization'] = f'Bearer {self.api_token}'

        try:
            response = self._make_request(url, params, headers)
            filename = self._generate_filename(translated_prompt)
            if saved_path := self._save_image(response, filename):
                if self.cache: self.cache.store(prompt, params, saved_path)
                duration = time.time() - start_time
                self.stats['images_generated'] += 1
                self.stats['total_generation_time'] += duration
                logger.info(f"Imagen generada en {duration:.2f} segundos!")
                return saved_path
        except (ConnectionError, ValueError, IOError) as e:
            self.stats['errors'] += 1
            logger.error(f"La generación de la imagen falló: {e}")
        return None

    def edit_image(self, prompt: str, image_path: str, **kwargs) -> Optional[str]:
        """
        Edita una imagen existente utilizando la API de Pollinations AI.

        Sube la imagen a GoFile para obtener una URL pública y luego usa esa URL
        con el prompt de edición. Intenta con modelos de edición en un orden preferencial.

        Args:
            prompt (str): El prompt de texto para la edición de la imagen.
            image_path (str): Ruta local de la imagen a editar.
            **kwargs: Parámetros adicionales para la edición (ej. width, height, model, seed).

        Returns:
            Optional[str]: La ruta absoluta del archivo guardado si la edición fue exitosa, None en caso contrario.
        """
        logger.info(f"Editando imagen '{image_path}' con el prompt: '{prompt}'")

        if not Path(image_path).exists():
            logger.error(f"El archivo de imagen no existe: {image_path}")
            return None

        public_url = self._upload_to_gofile(image_path)
        if not public_url:
            logger.error("No se pudo subir la imagen para editar. Abortando.")
            return None

        translated_prompt = self._translate_prompt(prompt)

        preferred_model = self.config_manager.get('model_edicion', 'kontext')

        model_params = {
            'kontext': {'param': 'image', 'prompt_prefix': ''},
            'flux': {'param': 'reference', 'prompt_prefix': 'based on reference image, '},
            'flux-kontext': {'param': 'image', 'prompt_prefix': ''}
        }

        methods_to_try = [preferred_model] + [m for m in model_params if m != preferred_model]

        methods = []
        for model_name in methods_to_try:
            if model_name in model_params:
                methods.append({
                    'model': model_name,
                    'param': model_params[model_name]['param'],
                    'prompt_prefix': model_params[model_name]['prompt_prefix']
                })

        for method in methods:
            try:
                logger.info(f"Intentando edición con el modelo '{method['model']}'...")

                final_prompt = f"{method['prompt_prefix']}{translated_prompt}"
                encoded_prompt = quote_plus(final_prompt)

                url = f"{self.BASE_URL}{encoded_prompt}"

                params = {
                    "model": method['model'],
                    method['param']: public_url,
                    "seed": kwargs.get('seed', random.randint(0, 1_000_000_000)),
                    "width": kwargs.get('width', self.config_manager.get('width')),
                    "height": kwargs.get('height', self.config_manager.get('height')),
                    "nologo": not self.config_manager.get('add_logo', True)
                }

                headers = {}
                if self.api_token:
                    headers['Authorization'] = f'Bearer {self.api_token}'

                response = self._make_request(url, params, headers)
                filename = self._generate_filename(f"edit_{method['model']}_{translated_prompt}")
                saved_path = self._save_image(response, filename)

                logger.info(f"Edición exitosa con el modelo '{method['model']}'.")
                return saved_path

            except (ConnectionError, ValueError, IOError) as e:
                logger.warning(f"El método con '{method['model']}' falló: {e}")

        self.stats['errors'] += 1
        logger.error("Todos los métodos de edición fallaron.")
        return None

    def run_diagnostics(self) -> None:
        """
        Ejecuta una serie de pruebas para diagnosticar la configuración y conectividad
        con las APIs de Pollinations y GoFile.
        """
        logger.info("="*60)
        logger.info("INICIANDO DIAGNÓSTICO DEL SISTEMA")
        logger.info("="*60)

        logger.info("\n1. Probando conectividad con la API de Pollinations...")
        try:
            response = requests.get(f"{self.BASE_URL.replace('/prompt/', '')}/models", timeout=15)
            if response.status_code == 200:
                models = response.json()
                logger.info(f"   API de Pollinations accesible. {len(models)} modelos encontrados.")
                if 'flux' in models and 'kontext' in models:
                    logger.info("   Modelos 'flux' y 'kontext' están disponibles.")
                else:
                    logger.warning("   Faltan modelos clave ('flux' o 'kontext').")
            else:
                logger.error(f"   Error de conectividad: HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"   Falló la conexión con la API: {e}")

        logger.info("\n2. Probando credenciales de GoFile...")
        if not self.gofile_token or not self.gofile_folder:
            logger.error("   No configuradas. La edición de imágenes no funcionará.")
        else:
            try:
                headers = {'Authorization': f'Bearer {self.gofile_token}'}

                id_response = requests.get("https://api.gofile.io/accounts/getid", headers=headers, timeout=15)
                id_response.raise_for_status()
                account_id = id_response.json().get('data', {}).get('id')

                if not account_id:
                    logger.error("   No se pudo obtener el ID de la cuenta de GoFile.")
                    return

                details_response = requests.get(f"https://api.gofile.io/accounts/{account_id}", headers=headers, timeout=15)
                details_response.raise_for_status()
                data = details_response.json()

                if data.get('status') == 'ok':
                    logger.info(f"   Token de GoFile válido para la cuenta: {data['data']['email']}")
                else:
                    logger.error(f"   Token de GoFile inválido: {data.get('status')}")
            except requests.exceptions.HTTPError as e:
                logger.error(f"   Error HTTP conectando con GoFile: {e.response.status_code}")
            except requests.exceptions.RequestException as e:
                logger.error(f"   Falló la conexión de red con GoFile: {e}")
            except json.JSONDecodeError:
                logger.error(f"   La respuesta de GoFile no es un JSON válido.")

        logger.info("\n" + "="*60)
        logger.info("DIAGNÓSTICO COMPLETADO")
        logger.info("="*60)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Devuelve las estadísticas de uso de la herramienta durante la sesión actual.

        Returns:
            Dict[str, Any]: Un diccionario con métricas como imágenes generadas,
                            aciertos de caché, tiempo de generación, y errores.
        """
        total_reqs = self.stats['images_generated'] + self.stats['cache_hits']
        avg_time = self.stats['total_generation_time'] / max(1, self.stats['images_generated'])
        return {
            'images_generated': self.stats['images_generated'],
            'cache_hits': self.stats['cache_hits'],
            'cache_hit_rate': f"{(self.stats['cache_hits'] / max(1, total_reqs)) * 100:.1f}%",
            'average_generation_time': f"{avg_time:.2f}s",
            'errors': self.stats['errors']
        }
