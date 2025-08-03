import json
from pathlib import Path
from typing import Dict, Any, Optional

from .logger_config import logger

class CollageTemplates:
    """
    Gestiona la carga y acceso a plantillas de collage desde un archivo JSON.
    """
    def __init__(self, script_dir: Path, template_file: str = "collage_templates.json"):
        self.template_file_path = script_dir / "config" / template_file
        self.TEMPLATES = self._load_templates()

    def _load_templates(self) -> Dict:
        if self.template_file_path.exists():
            try:
                with open(self.template_file_path, 'r', encoding='utf-8') as f:
                    logger.info(f"Cargando plantillas de collage desde {self.template_file_path}")
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error al cargar plantillas de collage desde {self.template_file_path}: {e}")
                return {}
        logger.warning(f"Archivo de plantillas de collage no encontrado: {self.template_file_path}")
        return {}

    def get_template(self, template_name: str) -> Optional[Dict]:
        return self.TEMPLATES.get(template_name)
