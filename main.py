#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Asegurarse de que las dependencias necesarias están instaladas
try:
    import colorama
    import dotenv
    import PIL
    import requests
    import tqdm
    import wand
except ImportError as e:
    print(f"Falta una dependencia crítica: {e.name}. Por favor, instálala con 'pip install {e.name}'.")
    sys.exit(1)

# Cargar variables de entorno al inicio
dotenv.load_dotenv(dotenv_path=Path(__file__).resolve().parent / "config" / ".env")

from utils.logger_config import logger
from utils.config_manager import ConfigManager
from core.image_tool import ImageTool
from core.image_processor import ImageProcessor
from ui.cli import (
    print_banner,
    show_main_menu,
    handle_generate,
    handle_batch_generation,
    handle_edit,
    handle_template_generation,
    show_statistics,
    show_history,
    show_tools_menu,
)

def main():
    """
    Función principal de la aplicación Image Generator CLI.
    Inicializa los componentes necesarios y ejecuta el bucle principal de la interfaz de usuario.
    """
    SCRIPT_DIR = Path(__file__).resolve().parent
    
    try:
        config_manager = ConfigManager(config_path=Path("config/pollinations_config.json"), script_dir=SCRIPT_DIR)
        image_tool = ImageTool(config_manager=config_manager, script_dir=SCRIPT_DIR)
        image_processor = ImageProcessor(output_dir=config_manager.get('output_dir'))

        print_banner()

        actions = {
            "1": lambda: handle_generate(image_tool),
            "2": lambda: handle_batch_generation(image_tool),
            "3": lambda: handle_edit(image_tool, image_processor, SCRIPT_DIR),
            "4": lambda: handle_template_generation(image_tool),
            "5": lambda: show_statistics(image_tool),
            "6": lambda: show_history(image_tool),
            "7": lambda: show_tools_menu(image_tool),
        }

        while True:
            show_main_menu()
            choice = input(f"{colorama.Fore.CYAN}>> Selecciona una opción: {colorama.Style.RESET_ALL}").strip()

            if choice == '0':
                print("¡Hasta luego!")
                break
            
            action = actions.get(choice)
            if action:
                action()
            else:
                logger.error("Opción no válida. Por favor, intenta de nuevo.")
            
            input(f"\n--- Presiona Enter para continuar ---")

    except KeyboardInterrupt:
        print("\nInterrupción por usuario. Saliendo...")
    except Exception as e:
        logger.critical(f"Error crítico en la aplicación: {e}", exc_info=True)

if __name__ == "__main__":
    main()
