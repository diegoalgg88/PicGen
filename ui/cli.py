import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

from colorama import Fore, Style
from tqdm import tqdm
import re
from datetime import datetime

from app_3.utils.logger_config import logger
from app_3.core.image_tool import ImageTool
from app_3.core.image_processor import ImageProcessor

def print_banner():
    """
    Imprime un banner atractivo para la aplicación.
    """
    print(f"{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}   GENERADOR Y EDITOR DE IMÁGENES CON POLLINATIONS AI - v5.0 (Integrado){Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")

def show_main_menu():
    """
    Muestra el menú principal de opciones.
    """
    print(f"\n{Fore.YELLOW}--- MENÚ PRINCIPAL ---{Style.RESET_ALL}")
    menu = {
        "1": "Generar imagen individual",
        "2": "Generar múltiples imágenes (lote)",
        "3": "Editar imagen",
        "4": "Usar plantilla predefinida",
        "5": "Ver estadísticas de sesión",
        "6": "Ver historial de imágenes",
        "7": "Herramientas y utilidades",
        "0": "Salir"
    }
    for key, value in menu.items():
        print(f"  {key}. {value}")
    print(f"{Fore.YELLOW}{'-'*22}{Style.RESET_ALL}")

def handle_generate(image_tool: ImageTool):
    """
    Maneja la lógica para generar una imagen individual.
    """
    try:
        prompt = input(f"{Fore.CYAN}>> Ingresa el prompt para generar la imagen: {Style.RESET_ALL}").strip()
        if prompt:
            image_tool.generate_image(prompt)
        else:
            logger.warning("El prompt no puede estar vacío.")
    except Exception as e:
        logger.error(f"Ocurrió un error durante la generación: {e}")

def handle_batch_generation(image_tool: ImageTool):
    """
    Maneja la lógica para generar múltiples imágenes en lote.
    """
    print(f"\n{Fore.CYAN}GENERACIÓN EN LOTE{Style.RESET_ALL}")
    prompts = []
    file_path = input(f"{Fore.CYAN}>> Ruta de archivo de prompts (o enter para manual): {Style.RESET_ALL}").strip()
    if file_path:
        try:
            with open(file_path, 'r', encoding='utf-8') as f: prompts = [line.strip() for line in f if line.strip()]
            logger.info(f"Cargados {len(prompts)} prompts desde '{file_path}'.")
        except FileNotFoundError:
            logger.error(f"Archivo no encontrado: {file_path}"); return
    else:
        print(f"{Fore.YELLOW}Ingresa prompts (deja en blanco para terminar):{Style.RESET_ALL}")
        while True:
            prompt = input(f"   Prompt {len(prompts) + 1}: ").strip()
            if not prompt: break
            prompts.append(prompt)
    if prompts:
        with ThreadPoolExecutor(max_workers=image_tool.config_manager.get('batch_size', 5)) as exec:
            list(tqdm(exec.map(image_tool.generate_image, prompts), total=len(prompts), desc="Procesando lote"))

def handle_edit(image_tool: ImageTool, image_processor: ImageProcessor, script_dir: Path):
    """
    Maneja la lógica para editar una imagen, ofreciendo opciones con y sin IA.
    """
    while True:
        print(f"\n{Fore.YELLOW}--- MENÚ DE EDICIÓN ---{Style.RESET_ALL}")
        edit_menu = {
            "1": "Edición con IA (transformaciones complejas)",
            "2": "Edición sin IA (ajustes básicos y filtros)",
            "0": "Volver al menú principal"
        }
        for key, value in edit_menu.items():
            print(f"  {key}. {value}")
        print(f"{Fore.YELLOW}{'-'*22}{Style.RESET_ALL}")

        edit_choice = input(f"{Fore.CYAN}>> Selecciona una opción de edición: {Style.RESET_ALL}").strip()

        if edit_choice == '0':
            break

        image_path = select_image_from_input_folder(script_dir)
        if not image_path:
            continue

        if edit_choice == '1':
            prompt = input(f"{Fore.CYAN}>> Ingresa el prompt para la edición con IA: {Style.RESET_ALL}").strip()
            if prompt:
                image_tool.edit_image(prompt, str(image_path))
            else:
                logger.warning("El prompt de edición no puede estar vacío.")
        elif edit_choice == '2':
            handle_non_ai_edit(image_processor, image_path)
        else:
            logger.error("Opción no válida. Por favor, intenta de nuevo.")
        
        input(f"\n--- Presiona Enter para continuar ---")

def select_image_from_input_folder(script_dir: Path) -> Optional[Path]:
    """
    Permite al usuario seleccionar una imagen del folder input o ingresar una ruta.
    """
    input_dir = script_dir / 'input'
    image_files = [f for f in input_dir.iterdir() if f.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp')]

    selected_image_path = None

    if image_files:
        print(f"\n{Fore.YELLOW}--- IMÁGENES DISPONIBLES EN '{input_dir}' ---{Style.RESET_ALL}")
        for i, f in enumerate(image_files, 1):
            print(f"  {i}. {f.name}")
        print(f"{Fore.YELLOW}{'-'*40}{Style.RESET_ALL}")
        
        choice = input(f"{Fore.CYAN}>> Selecciona el número de la imagen a editar (o presiona Enter para ingresar una ruta): {Style.RESET_ALL}").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(image_files):
            selected_image_path = image_files[int(choice) - 1]
        else:
            manual_path = input(f"{Fore.CYAN}>> Ingresa la ruta de la imagen a editar: {Style.RESET_ALL}").strip()
            if manual_path:
                selected_image_path = Path(manual_path)
    else:
        logger.info(f"No se encontraron imágenes en el directorio '{input_dir}'.")
        manual_path = input(f"{Fore.CYAN}>> Ingresa la ruta de la imagen a editar: {Style.RESET_ALL}").strip()
        if manual_path:
            selected_image_path = Path(manual_path)

    if selected_image_path and not selected_image_path.exists():
        logger.error(f"La ruta de la imagen no es válida o el archivo no existe: {selected_image_path}")
        return None
    
    return selected_image_path

def handle_template_generation(image_tool: ImageTool):
    """
    Maneja la lógica para generar imágenes usando plantillas predefinidas.
    """
    templates = image_tool.templates.list_templates()
    if not templates: logger.warning("No hay plantillas. Crea 'prompt_templates.json'."); return
    print(f"\n{Fore.YELLOW}GENERAR DESDE PLANTILLA{Style.RESET_ALL}")
    template_list = list(templates.items())
    for i, (name, base) in enumerate(template_list, 1): print(f"  {i}. {Fore.CYAN}{name}{Style.RESET_ALL} - {base[:60]}...")
    try:
        choice = int(input(f"\n{Fore.CYAN}>> Selecciona plantilla: {Style.RESET_ALL}").strip())
        name, base = template_list[choice - 1]
        placeholders = re.findall(r'\{(\w+)\}', base)
        template_vars = {p: input(f"   Valor para '{p}': ").strip() for p in placeholders}
        prompt, params = image_tool.templates.apply_template(name, **template_vars)
        image_tool.generate_image(prompt, **params)
    except (ValueError, IndexError): logger.error("Selección inválida.")

def show_statistics(image_tool: ImageTool):
    """
    Muestra las estadísticas de uso de la sesión actual.
    """
    print(f"\n{Fore.CYAN}{'='*60}\n{Fore.YELLOW}ESTADÍSTICAS DE SESIÓN\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    stats = image_tool.get_statistics()
    for label, value in stats.items(): print(f"{label.replace('_', ' ').title()}: {Fore.WHITE}{value}{Style.RESET_ALL}")

def show_history(image_tool: ImageTool):
    """
    Muestra el historial de imágenes generadas y permite abrir el directorio de salida.
    """
    print(f"\n{Fore.CYAN}{'='*60}\n{Fore.YELLOW}HISTORIAL DE IMÁGENES\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    out_dir = Path(image_tool.config_manager.get('output_dir'))
    if not out_dir.exists(): logger.warning("El directorio de salida no existe."); return
    img_files = [f for f in out_dir.iterdir() if f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']]
    if not img_files: print(f"{Fore.YELLOW}No hay imágenes generadas.{Style.RESET_ALL}"); return
    img_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for i, p in enumerate(img_files[:15]):
        st = p.stat()
        print(f"{i+1:2d}. {Fore.CYAN}{p.name}{Style.RESET_ALL}\n    📅 {datetime.fromtimestamp(st.st_mtime):%Y-%m-%d %H:%M} | 💾 {st.st_size/1024:.1f} KB")
    if input(f"\n{Fore.CYAN}>> ¿Abrir directorio? (s/n): {Style.RESET_ALL}").lower() == 's':
        try: webbrowser.open(out_dir.resolve().as_uri())
        except Exception as e: logger.error(f"No se pudo abrir directorio: {e}")

def show_tools_menu(image_tool: ImageTool):
    """
    Muestra el menú de herramientas y utilidades completo.
    """
    tool_actions = {
        "1": lambda t: t.run_diagnostics(),
        "2": lambda t: t.cache.clean_cache(0) if t.cache else logger.warning("El caché está deshabilitado."),
    }
    while True:
        print(f"\n{Fore.CYAN}{'='*60}\n{Fore.YELLOW}HERRAMIENTAS Y UTILIDADES\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        tools = {"1": "Ejecutar diagnóstico", "2": "Limpiar caché", "0": "Volver al menú principal"}
        for k, v in tools.items(): print(f"  {k}. {v}")
        
        choice = input(f"\n{Fore.CYAN}>> Selecciona herramienta: {Style.RESET_ALL}").strip()
        if choice == '0': break
        
        action = tool_actions.get(choice)
        if action:
            action(image_tool)
        else: logger.error("Opción no válida.")
        if choice != '0': input(f"\n--- Presiona Enter para continuar ---")

def show_non_ai_edit_menu():
    """
    Muestra el submenú de opciones de edición sin IA.
    """
    print(f"\n{Fore.YELLOW}--- EDICIÓN SIN IA ---{Style.RESET_ALL}")
    non_ai_menu = {
        "1": "Ajustes Básicos y Mejoras",
        "2": "Filtros Artísticos y Estilizados",
        "3": "Filtros de Tonalidad Global (LUT)",
        "0": "Volver al menú de Edición"
    }
    for key, value in non_ai_menu.items():
        print(f"  {key}. {value}")
    print(f"{Fore.YELLOW}{'-'*22}{Style.RESET_ALL}")

def handle_non_ai_edit(image_processor: ImageProcessor, image_path: Path):
    """
    Maneja la lógica para las opciones de edición sin IA.
    """
    while True:
        show_non_ai_edit_menu()
        non_ai_choice = input(f"{Fore.CYAN}>> Selecciona una categoría de edición sin IA: {Style.RESET_ALL}").strip()

        if non_ai_choice == '0':
            break

        try:
            if non_ai_choice == '1':
                handle_basic_adjustments(image_processor, image_path)
            elif non_ai_choice == '2':
                handle_artistic_filters(image_processor, image_path)
            elif non_ai_choice == '3':
                handle_tonal_filters(image_processor, image_path)
            else:
                logger.error("Opción no válida. Por favor, intenta de nuevo.")
        except Exception as e:
            logger.error(f"Ocurrió un error en la categoría de edición sin IA: {e}")
        
        if non_ai_choice != '0':
            input(f"\n--- Presiona Enter para continuar ---")

def show_basic_adjustments_menu():
    """
    Muestra el submenú de ajustes básicos y mejoras.
    """
    print(f"\n{Fore.YELLOW}--- AJUSTES BÁSICOS Y MEJORAS ---{Style.RESET_ALL}")
    menu = {
        "1": "Convertir a Blanco y Negro",
        "2": "Ajustar Brillo y Contraste",
        "3": "Ajustar Saturación",
        "4": "Ajustar Temperatura (Kelvin)",
        "5": "Ajustar Exposición",
        "6": "Aplicar Viñeteado",
        "7": "Recortar Imagen",
        "8": "Rotar Imagen",
        "9": "Voltear/Espejo Imagen",
        "10": "Redimensionar Imagen",
        "0": "Volver a Edición sin IA"
    }
    for key, value in menu.items():
        print(f"  {key}. {value}")
    print(f"{Fore.YELLOW}{'-'*22}{Style.RESET_ALL}")

def handle_basic_adjustments(image_processor: ImageProcessor, image_path: Path):
    """
    Maneja la lógica para los ajustes básicos de imagen.
    """
    while True:
        show_basic_adjustments_menu()
        choice = input(f"{Fore.CYAN}>> Selecciona un ajuste básico: {Style.RESET_ALL}").strip()
        if choice == '0':
            break
        try:
            if choice == '1':
                image_processor.convert_to_grayscale(str(image_path))
            elif choice == '2':
                brightness = float(input(f"{Fore.CYAN}>> Ingresa el brillo (ej. 120 para más brillo, 80 para menos): {Style.RESET_ALL}").strip())
                contrast = float(input(f"{Fore.CYAN}>> Ingresa el contraste (ej. 1.5 para más contraste, 0.5 para menos): {Style.RESET_ALL}").strip())
                image_processor.adjust_brightness_contrast(str(image_path), brightness, contrast)
            elif choice == '3':
                saturation = float(input(f"{Fore.CYAN}>> Ingresa la saturación (ej. 150 para más, 50 para menos): {Style.RESET_ALL}").strip())
                image_processor.adjust_saturation(str(image_path), saturation)
            elif choice == '4':
                kelvin = int(input(f"{Fore.CYAN}>> Ingresa la temperatura en Kelvin (ej. 4000 para cálido, 7000 para frío): {Style.RESET_ALL}").strip())
                image_processor.adjust_temperature(str(image_path), kelvin)
            elif choice == '5':
                amount = float(input(f"{Fore.CYAN}>> Ingresa la cantidad de exposición (ej. 0.1 para más luz, -0.1 para menos): {Style.RESET_ALL}").strip())
                image_processor.adjust_exposure(str(image_path), amount)
            elif choice == '6':
                radius = float(input(f"{Fore.CYAN}>> Ingresa el radio del viñeteado (ej. 0.5): {Style.RESET_ALL}").strip())
                sigma = float(input(f"{Fore.CYAN}>> Ingresa el sigma del viñeteado (ej. 0.2): {Style.RESET_ALL}").strip())
                image_processor.apply_vignette(str(image_path), radius, sigma)
            elif choice == '7':
                x = int(input(f"{Fore.CYAN}>> Ingresa la coordenada X de inicio del recorte: {Style.RESET_ALL}").strip())
                y = int(input(f"{Fore.CYAN}>> Ingresa la coordenada Y de inicio del recorte: {Style.RESET_ALL}").strip())
                width = int(input(f"{Fore.CYAN}>> Ingresa el ancho del recorte: {Style.RESET_ALL}").strip())
                height = int(input(f"{Fore.CYAN}>> Ingresa el alto del recorte: {Style.RESET_ALL}").strip())
                image_processor.crop_image(str(image_path), x, y, width, height)
            elif choice == '8':
                degrees = float(input(f"{Fore.CYAN}>> Ingresa los grados de rotación: {Style.RESET_ALL}").strip())
                image_processor.rotate_image(str(image_path), degrees)
            elif choice == '9':
                direction = input(f"{Fore.CYAN}>> Ingresa la dirección (flip para vertical, flop para horizontal): {Style.RESET_ALL}").strip()
                image_processor.flip_flop_image(str(image_path), direction)
            elif choice == '10':
                width = int(input(f"{Fore.CYAN}>> Ingresa el nuevo ancho: {Style.RESET_ALL}").strip())
                height = int(input(f"{Fore.CYAN}>> Ingresa el nuevo alto: {Style.RESET_ALL}").strip())
                image_processor.resize_image(str(image_path), width, height)
            else:
                logger.error("Opción no válida. Por favor, intenta de nuevo.")
        except ValueError:
            logger.error("Entrada inválida. Por favor, ingresa un número o valor correcto.")
        except Exception as e:
            logger.error(f"Ocurrió un error durante el ajuste básico: {e}")
        
        if choice != '0':
            input(f"\n--- Presiona Enter para continuar ---")

def show_artistic_filters_menu():
    """
    Muestra el submenú de filtros artísticos y estilizados.
    """
    print(f"\n{Fore.YELLOW}--- FILTROS ARTÍSTICOS Y ESTILIZADOS ---{Style.RESET_ALL}")
    menu = {
        "1": "Aplicar Sepia",
        "2": "Aplicar Granulado/Ruido",
        "3": "Aplicar Pintura al Óleo",
        "4": "Aplicar Carboncillo",
        "5": "Aplicar Relieve",
        "6": "Aplicar Remolino",
        "7": "Aplicar Onda",
        "0": "Volver a Edición sin IA"
    }
    for key, value in menu.items():
        print(f"  {key}. {value}")
    print(f"{Fore.YELLOW}{'-'*22}{Style.RESET_ALL}")

def handle_artistic_filters(image_processor: ImageProcessor, image_path: Path):
    """
    Maneja la lógica para los filtros artísticos de imagen.
    """
    while True:
        show_artistic_filters_menu()
        choice = input(f"{Fore.CYAN}>> Selecciona un filtro artístico: {Style.RESET_ALL}").strip()
        if choice == '0':
            break
        try:
            if choice == '1':
                image_processor.apply_sepia(str(image_path))
            elif choice == '2':
                amount = float(input(f"{Fore.CYAN}>> Ingresa la cantidad de granulado (ej. 0.5): {Style.RESET_ALL}").strip())
                image_processor.apply_grain(str(image_path), amount)
            elif choice == '3':
                radius = float(input(f"{Fore.CYAN}>> Ingresa el radio para pintura al óleo (ej. 2): {Style.RESET_ALL}").strip())
                image_processor.apply_oil_paint(str(image_path), radius)
            elif choice == '4':
                radius = float(input(f"{Fore.CYAN}>> Ingresa el radio para carboncillo (ej. 1): {Style.RESET_ALL}").strip())
                sigma = float(input(f"{Fore.CYAN}>> Ingresa el sigma para carboncillo (ej. 0.5): {Style.RESET_ALL}").strip())
                image_processor.apply_charcoal(str(image_path), radius, sigma)
            elif choice == '5':
                radius = float(input(f"{Fore.CYAN}>> Ingresa el radio para relieve (ej. 1): {Style.RESET_ALL}").strip())
                sigma = float(input(f"{Fore.CYAN}>> Ingresa el sigma para relieve (ej. 0.5): {Style.RESET_ALL}").strip())
                image_processor.apply_emboss(str(image_path), radius, sigma)
            elif choice == '6':
                degrees = float(input(f"{Fore.CYAN}>> Ingresa los grados de remolino (ej. 90): {Style.RESET_ALL}").strip())
                image_processor.apply_swirl(str(image_path), degrees)
            elif choice == '7':
                amplitude = float(input(f"{Fore.CYAN}>> Ingresa la amplitud de la onda (ej. 20): {Style.RESET_ALL}").strip())
                length = float(input(f"{Fore.CYAN}>> Ingresa la longitud de la onda (ej. 120): {Style.RESET_ALL}").strip())
                image_processor.apply_wave(str(image_path), amplitude, length)
            else:
                logger.error("Opción no válida. Por favor, intenta de nuevo.")
        except ValueError:
            logger.error("Entrada inválida. Por favor, ingresa un número o valor correcto.")
        except Exception as e:
            logger.error(f"Ocurrió un error durante el filtro artístico: {e}")
        
        if choice != '0':
            input(f"\n--- Presiona Enter para continuar ---")

def show_tonal_filters_menu():
    """
    Muestra el submenú de filtros de tonalidad global (LUT).
    """
    print(f"\n{Fore.YELLOW}--- FILTROS DE TONALIDAD GLOBAL (LUT) ---{Style.RESET_ALL}")
    menu = {
        "1": "Aplicar Duotono",
        "2": "Aplicar Tono Dividido (Split Toning)",
        "0": "Volver a Edición sin IA"
    }
    for key, value in menu.items():
        print(f"  {key}. {value}")
    print(f"{Fore.YELLOW}{'-'*22}{Style.RESET_ALL}")

def handle_tonal_filters(image_processor: ImageProcessor, image_path: Path):
    """
    Maneja la lógica para los filtros de tonalidad de imagen.
    """
    while True:
        show_tonal_filters_menu()
        choice = input(f"{Fore.CYAN}>> Selecciona un filtro de tonalidad: {Style.RESET_ALL}").strip()
        if choice == '0':
            break
        try:
            if choice == '1':
                color1 = input(f"{Fore.CYAN}>> Ingresa el primer color (ej. 'red' o '#FF0000'): {Style.RESET_ALL}").strip()
                color2 = input(f"{Fore.CYAN}>> Ingresa el segundo color (ej. 'blue' o '#0000FF'): {Style.RESET_ALL}").strip()
                image_processor.apply_duotone(str(image_path), color1, color2)
            elif choice == '2':
                highlight_color = input(f"{Fore.CYAN}>> Ingresa el color para las luces (ej. 'yellow' o '#FFFF00'): {Style.RESET_ALL}").strip()
                shadow_color = input(f"{Fore.CYAN}>> Ingresa el color para las sombras (ej. 'cyan' o '#00FFFF'): {Style.RESET_ALL}").strip()
                image_processor.apply_split_tone(str(image_path), highlight_color, shadow_color)
            else:
                logger.error("Opción no válida. Por favor, intenta de nuevo.")
        except ValueError:
            logger.error("Entrada inválida. Por favor, ingresa un número o valor correcto.")
        except Exception as e:
            logger.error(f"Ocurrió un error durante el filtro de tonalidad: {e}")
        
        if choice != '0':            input(f"\n--- Presiona Enter para continuar ---")