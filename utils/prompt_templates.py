import json
from pathlib import Path
from typing import Dict, Tuple

from .logger_config import logger

class PromptTemplates:
    """
    Gestiona la carga y aplicación de plantillas de prompts desde un archivo JSON.

    Permite definir prompts preconfigurados con placeholders y parámetros asociados,
    facilitando la reutilización y consistencia en la generación de imágenes.
    """
    def __init__(self, script_dir: Path, template_file: str = "prompt_templates.json"):
        """
        Inicializa el gestor de plantillas de prompts.

        Args:
            script_dir (Path): El directorio base del script para resolver la ruta del archivo de plantillas.
            template_file (str): El nombre del archivo JSON que contiene las plantillas.
                                 Por defecto es 'prompt_templates.json'.
        """
        self.template_file_path = script_dir / "config" / template_file
        self.TEMPLATES = self._load_templates()

    def _load_templates(self) -> Dict:
        """
        Carga las plantillas de prompts desde el archivo JSON especificado.

        Si el archivo no existe o hay un error de lectura/parseo, devuelve un diccionario vacío.

        Returns:
            Dict: Un diccionario donde las claves son los nombres de las plantillas
                  y los valores son sus definiciones (prompt base y parámetros).
        """
        if self.template_file_path.exists():
            try:
                with open(self.template_file_path, 'r', encoding='utf-8') as f:
                    logger.info(f"Cargando plantillas desde {self.template_file_path}")
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error al cargar plantillas desde {self.template_file_path}: {e}")
                return {}
        logger.warning(f"Archivo de plantillas no encontrado: {self.template_file_path}")
        return {}

    def list_templates(self) -> Dict[str, str]:
        """
        Devuelve un diccionario con los nombres de las plantillas y una breve descripción
        de su prompt base.

        Returns:
            Dict[str, str]: Un diccionario con nombres de plantilla y sus prompts base.
        """
        return {name: template.get('base', 'Plantilla sin base') for name, template in self.TEMPLATES.items()}

    def get_random_example(self, placeholder: str, template_name: str) -> str:
        """
        Obtiene un ejemplo aleatorio para un placeholder de una plantilla específica.

        Args:
            placeholder (str): El nombre del placeholder.
            template_name (str): El nombre de la plantilla.

        Returns:
            str: Un ejemplo aleatorio o una cadena vacía si no hay ejemplos.
        """
        import random
        try:
            examples = self.TEMPLATES[template_name]['placeholders'][placeholder]['examples']
            return random.choice(examples)
        except (KeyError, IndexError):
            return ""

    def apply_template(self, template_name: str, **kwargs) -> Tuple[str, Dict]:
        """
        Aplica una plantilla de prompt, formateando el prompt base con los argumentos
        proporcionados y devolviendo los parámetros asociados.

        Args:
            template_name (str): El nombre de la plantilla a aplicar.
            **kwargs: Argumentos de palabra clave que se usarán para formatear el prompt base.
                      Estos corresponden a los placeholders en la cadena 'base' de la plantilla.

        Returns:
            Tuple[str, Dict]: Una tupla que contiene el prompt formateado y un diccionario
                              de parámetros adicionales definidos en la plantilla.

        Raises:
            ValueError: Si la plantilla especificada no se encuentra.
        """
        template = self.TEMPLATES.get(template_name)
        if not template:
            raise ValueError(f"Plantilla '{template_name}' no encontrada")
        
        prompt = template.get('base', '').format(**kwargs)
        params = template.get('params', {}).copy()
        
        return prompt, params
