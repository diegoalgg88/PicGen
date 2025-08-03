from pathlib import Path
from typing import Optional
import io

from wand.image import Image as WandImage
from PIL import Image as PILImage

from utils.logger_config import logger

class ImageProcessor:
    """
    Clase para el procesamiento local de imágenes utilizando la librería Wand (ImageMagick).

    Proporciona métodos para aplicar diversas transformaciones y filtros a imágenes
    de forma local, sin depender de APIs externas para estas operaciones.
    """
    def __init__(self, output_dir: str = './generated_images'):
        """
        Inicializa el procesador de imágenes.

        Args:
            output_dir (str): Directorio donde se guardarán las imágenes procesadas.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def _pil_to_wand(self, pil_image: PILImage.Image) -> WandImage:
        """Convierte una imagen PIL a una imagen Wand."""
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format=pil_image.format or 'PNG')
        img_byte_arr.seek(0)
        return WandImage(file=img_byte_arr)

    def _wand_to_pil(self, wand_image: WandImage) -> PILImage.Image:
        """Convierte una imagen Wand a una imagen PIL."""
        return PILImage.open(io.BytesIO(wand_image.make_blob(format='PNG')))

    def _save_pil_image(self, pil_image: PILImage.Image, original_name: str, suffix: str) -> Optional[str]:
        """
        Guarda una imagen PIL en el directorio de salida.

        Args:
            pil_image (PILImage.Image): Objeto PIL Image a guardar.
            original_name (str): Nombre original del archivo, usado para generar el nombre del archivo.
            suffix (str): Sufijo a añadir al nombre del archivo para indicar la transformación aplicada.

        Returns:
            Optional[str]: La ruta absoluta del archivo guardado si tiene éxito, None en caso de error.
        """
        output_filename = f"{Path(original_name).stem}_{suffix}.png"
        output_path = self.output_dir / output_filename
        try:
            pil_image.save(output_path)
            logger.info(f"Imagen guardada en: {output_path.resolve()}")
            return str(output_path.resolve())
        except Exception as e:
            logger.error(f"Error al guardar la imagen: {e}")
            return None

    def convert_to_grayscale(self, pil_image: PILImage.Image) -> Optional[PILImage.Image]:
        """
        Convierte una imagen a escala de grises.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.

        Returns:
            Optional[PILImage.Image]: Imagen PIL en escala de grises, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.type = 'grayscale'
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error al convertir la imagen a escala de grises: {e}")
            logger.warning("Asegúrate de que ImageMagick esté instalado y en tu PATH.")
            return None

    def adjust_brightness_contrast(self, pil_image: PILImage.Image, brightness: float, contrast: float) -> Optional[PILImage.Image]:
        """
        Ajusta el brillo y contraste de una imagen.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.
            brightness (float): Nivel de brillo (ej. 120 para más brillo, 80 para menos).
            contrast (float): Nivel de contraste (ej. 1.5 para más contraste, 0.5 para menos).

        Returns:
            Optional[PILImage.Image]: Imagen PIL ajustada, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.modulate(brightness=brightness, saturation=100, hue=100)
                img.sigmoidal_contrast(True, contrast)
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error ajustando brillo/contraste: {e}")
            return None

    def adjust_saturation(self, pil_image: PILImage.Image, saturation: float) -> Optional[PILImage.Image]:
        """
        Ajusta la saturación de una imagen.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.
            saturation (float): Nivel de saturación (ej. 150 para más, 50 para menos).

        Returns:
            Optional[PILImage.Image]: Imagen PIL ajustada, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.modulate(brightness=100, saturation=saturation, hue=100)
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error ajustando saturación: {e}")
            return None

    def rotate_image(self, pil_image: PILImage.Image, degrees: float) -> Optional[PILImage.Image]:
        """
        Rota una imagen por un número de grados.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.
            degrees (float): Grados de rotación.

        Returns:
            Optional[PILImage.Image]: Imagen PIL rotada, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.rotate(degrees)
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error rotando imagen: {e}")
            return None

    def flip_flop_image(self, pil_image: PILImage.Image, direction: str) -> Optional[PILImage.Image]:
        """
        Voltea o espeja una imagen.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.
            direction (str): 'flip' para voltear verticalmente, 'flop' para horizontalmente.

        Returns:
            Optional[PILImage.Image]: Imagen PIL volteada, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                if direction == "flip": img.flip()
                elif direction == "flop": img.flop()
                else: raise ValueError("Dirección inválida. Usa 'flip' o 'flop'.")
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error volteando imagen: {e}")
            return None

    def resize_image(self, pil_image: PILImage.Image, width: int, height: int) -> Optional[PILImage.Image]:
        """
        Redimensiona una imagen a las dimensiones especificadas.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.
            width (int): Nuevo ancho.
            height (int): Nuevo alto.

        Returns:
            Optional[PILImage.Image]: Imagen PIL redimensionada, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.resize(width, height)
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error redimensionando imagen: {e}")
            return None

    def apply_sepia(self, pil_image: PILImage.Image) -> Optional[PILImage.Image]:
        """
        Aplica un filtro sepia a la imagen.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.

        Returns:
            Optional[PILImage.Image]: Imagen PIL con filtro sepia, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.sepia_tone(threshold=0.8 * img.quantum_range)
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error aplicando sepia: {e}")
            return None

    def apply_oil_paint(self, pil_image: PILImage.Image, radius: float) -> Optional[PILImage.Image]:
        """
        Aplica un efecto de pintura al óleo a la imagen.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.
            radius (float): Radio del efecto.

        Returns:
            Optional[PILImage.Image]: Imagen PIL con efecto de pintura al óleo, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.oil_paint(radius=radius)
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error aplicando pintura al óleo: {e}")
            return None

    def apply_sharpen(self, pil_image: PILImage.Image) -> Optional[PILImage.Image]:
        """
        Aplica un filtro de nitidez a la imagen.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.

        Returns:
            Optional[PILImage.Image]: Imagen PIL con nitidez, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.sharpen(radius=0, sigma=1.0)
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error aplicando nitidez: {e}")
            return None

    def apply_blur(self, pil_image: PILImage.Image, radius: float, sigma: float) -> Optional[PILImage.Image]:
        """
        Aplica un efecto de desenfoque (blur) a la imagen.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.
            radius (float): Radio del desenfoque.
            sigma (float): Sigma del desenfoque.

        Returns:
            Optional[PILImage.Image]: Imagen PIL con desenfoque, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.blur(radius=radius, sigma=sigma)
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error aplicando desenfoque: {e}")
            return None

    def adjust_temperature(self, pil_image: PILImage.Image, kelvin: int) -> Optional[PILImage.Image]:
        """
        Ajusta la temperatura de color de la imagen (simulado).

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.
            kelvin (int): Temperatura en Kelvin (ej. 4000 para cálido, 7000 para frío).

        Returns:
            Optional[PILImage.Image]: Imagen PIL con temperatura ajustada, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.white_balance()
                if kelvin > 6500:
                    img.blue_shift(0.1)
                elif kelvin < 5000:
                    img.red_shift(0.1)
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error ajustando temperatura: {e}")
            return None

    def adjust_exposure(self, pil_image: PILImage.Image, amount: float) -> Optional[PILImage.Image]:
        """
        Ajusta la exposición de la imagen.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.
            amount (float): Cantidad de ajuste de exposición (positivo para más luz, negativo para menos).

        Returns:
            Optional[PILImage.Image]: Imagen PIL con exposición ajustada, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.evaluate(operator='add', value=amount * img.quantum_range, channel='all_channels')
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error ajustando exposición: {e}")
            return None

    def apply_vignette(self, pil_image: PILImage.Image, radius: float, sigma: float) -> Optional[PILImage.Image]:
        """
        Aplica un efecto de viñeteado a la imagen.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.
            radius (float): Radio del viñeteado.
            sigma (float): Sigma del viñeteado.

        Returns:
            Optional[PILImage.Image]: Imagen PIL con viñeteado, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.vignette(x=radius, y=sigma)
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error aplicando viñeteado: {e}")
            return None

    def crop_image(self, pil_image: PILImage.Image, x: int, y: int, width: int, height: int) -> Optional[PILImage.Image]:
        """
        Recorta una sección de la imagen.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.
            x (int): Coordenada X de inicio del recorte.
            y (int): Coordenada Y de inicio del recorte.
            width (int): Ancho del recorte.
            height (int): Alto del recorte.

        Returns:
            Optional[PILImage.Image]: Imagen PIL recortada, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.crop(x=x, y=y, width=width, height=height)
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error recortando imagen: {e}")
            return None

    def apply_grain(self, pil_image: PILImage.Image, amount: float) -> Optional[PILImage.Image]:
        """
        Aplica un efecto de granulado/ruido a la imagen.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.
            amount (float): Cantidad de granulado.

        Returns:
            Optional[PILImage.Image]: Imagen PIL con granulado, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.noise("gaussian", amount)
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error aplicando granulado: {e}")
            return None

    def apply_charcoal(self, pil_image: PILImage.Image, radius: float, sigma: float) -> Optional[PILImage.Image]:
        """
        Aplica un efecto de carboncillo a la imagen.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.
            radius (float): Radio del efecto.
            sigma (float): Sigma del efecto.

        Returns:
            Optional[PILImage.Image]: Imagen PIL con efecto carboncillo, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.charcoal(radius=radius, sigma=sigma)
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error aplicando carboncillo: {e}")
            return None

    def apply_emboss(self, pil_image: PILImage.Image, radius: float, sigma: float) -> Optional[PILImage.Image]:
        """
        Aplica un efecto de relieve a la imagen.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.
            radius (float): Radio del efecto.
            sigma (float): Sigma del efecto.

        Returns:
            Optional[PILImage.Image]: Imagen PIL con efecto relieve, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.emboss(radius=radius, sigma=sigma)
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error aplicando relieve: {e}")
            return None

    def apply_swirl(self, pil_image: PILImage.Image, degrees: float) -> Optional[PILImage.Image]:
        """
        Aplica un efecto de remolino a la imagen.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.
            degrees (float): Grados de remolino.

        Returns:
            Optional[PILImage.Image]: Imagen PIL con efecto remolino, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.swirl(degrees=degrees)
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error aplicando remolino: {e}")
            return None

    def apply_wave(self, pil_image: PILImage.Image, amplitude: float, length: float) -> Optional[PILImage.Image]:
        """
        Aplica un efecto de onda a la imagen.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.
            amplitude (float): Amplitud de la onda.
            length (float): Longitud de la onda.

        Returns:
            Optional[PILImage.Image]: Imagen PIL con efecto onda, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.wave(amplitude=amplitude, length=length)
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error aplicando onda: {e}")
            return None

    def apply_duotone(self, pil_image: PILImage.Image, color1: str, color2: str) -> Optional[PILImage.Image]:
        """
        Aplica un efecto duotono a la imagen.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.
            color1 (str): Primer color (ej. 'red' o '#FF0000').
            color2 (str): Segundo color (ej. 'blue' o '#0000FF').

        Returns:
            Optional[PILImage.Image]: Imagen PIL con efecto duotono, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.type = 'grayscale'
                img.colorize(color=color1, alpha='rgb(100%,0%,0%)')
                img.colorize(color=color2, alpha='rgb(0%,100%,100%)')
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error aplicando duotono: {e}")
            return None

    def apply_split_tone(self, pil_image: PILImage.Image, highlight_color: str, shadow_color: str) -> Optional[PILImage.Image]:
        """
        Aplica un efecto de tono dividido (split toning) a la imagen.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.
            highlight_color (str): Color para las luces.
            shadow_color (str): Color para las sombras.

        Returns:
            Optional[PILImage.Image]: Imagen PIL con efecto de tono dividido, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.modulate(brightness=100, saturation=0, hue=100)
                img.colorize(color=highlight_color, alpha='rgb(0%,0%,100%)')
                img.colorize(color=shadow_color, alpha='rgb(100%,0%,0%)')
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error aplicando tono dividido: {e}")
            return None

    def apply_negative(self, pil_image: PILImage.Image) -> Optional[PILImage.Image]:
        """
        Aplica un efecto negativo a la imagen.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.

        Returns:
            Optional[PILImage.Image]: Imagen PIL con efecto negativo, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.negate(grayscale=False)
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error aplicando negativo: {e}")
            return None

    def apply_posterize(self, pil_image: PILImage.Image, levels: int) -> Optional[PILImage.Image]:
        """
        Aplica un efecto de posterización a la imagen.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.
            levels (int): Número de niveles de color a reducir.

        Returns:
            Optional[PILImage.Image]: Imagen PIL posterizada, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.posterize(levels)
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error aplicando posterización: {e}")
            return None

    def apply_solarize(self, pil_image: PILImage.Image, threshold: float) -> Optional[PILImage.Image]:
        """
        Aplica un efecto de solarización a la imagen.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.
            threshold (float): Umbral de solarización (0.0 a 1.0).

        Returns:
            Optional[PILImage.Image]: Imagen PIL solarizada, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.solarize(threshold * img.quantum_range)
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error aplicando solarización: {e}")
            return None

    def apply_edge_detect(self, pil_image: PILImage.Image, radius: float = 0.0, sigma: float = 1.0) -> Optional[PILImage.Image]:
        """
        Aplica un filtro de detección de bordes a la imagen.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.
            radius (float): Radio del filtro.
            sigma (float): Sigma del filtro.

        Returns:
            Optional[PILImage.Image]: Imagen PIL con bordes detectados, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.edge(radius=radius, sigma=sigma)
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error aplicando detección de bordes: {e}")
            return None

    def apply_pixelate(self, pil_image: PILImage.Image, x_factor: int, y_factor: int) -> Optional[PILImage.Image]:
        """
        Aplica un efecto de pixelado a la imagen.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.
            x_factor (int): Factor de pixelado en el eje X.
            y_factor (int): Factor de pixelado en el eje Y.

        Returns:
            Optional[PILImage.Image]: Imagen PIL pixelada, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.sample(int(img.width / x_factor), int(img.height / y_factor))
                img.resize(img.width, img.height)
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error aplicando pixelado: {e}")
            return None

    def apply_crystallize(self, pil_image: PILImage.Image, radius: float) -> Optional[PILImage.Image]:
        """
        Aplica un efecto de cristalización a la imagen.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.
            radius (float): Radio del efecto de cristalización.

        Returns:
            Optional[PILImage.Image]: Imagen PIL cristalizada, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.statistic('median', width=int(radius), height=int(radius))
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error aplicando cristalización: {e}")
            return None

    def apply_implode(self, pil_image: PILImage.Image, amount: float) -> Optional[PILImage.Image]:
        """
        Aplica un efecto de implosión a la imagen.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.
            amount (float): Cantidad de implosión (positivo para implosión, negativo para explosión).

        Returns:
            Optional[PILImage.Image]: Imagen PIL con efecto de implosión, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.implode(amount)
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error aplicando implosión: {e}")
            return None

    def apply_explode(self, pil_image: PILImage.Image, amount: float) -> Optional[PILImage.Image]:
        """
        Aplica un efecto de explosión a la imagen.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.
            amount (float): Cantidad de explosión (positivo para explosión, negativo para implosión).

        Returns:
            Optional[PILImage.Image]: Imagen PIL con efecto de explosión, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.implode(-amount) # Implode con valor negativo para efecto de explosión
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error aplicando explosión: {e}")
            return None

    def adjust_color_balance(self, pil_image: PILImage.Image, red: float = 0.0, green: float = 0.0, blue: float = 0.0) -> Optional[PILImage.Image]:
        """
        Ajusta el balance de color de la imagen.

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.
            red (float): Ajuste para el canal rojo (-1.0 a 1.0).
            green (float): Ajuste para el canal verde (-1.0 a 1.0).
            blue (float): Ajuste para el canal azul (-1.0 a 1.0).

        Returns:
            Optional[PILImage.Image]: Imagen PIL con balance de color ajustado, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                # Wand's color_matrix or similar might be more precise, but for simple adjustments:
                if red != 0:
                    img.evaluate(operator='add', value=red * img.quantum_range, channel='red')
                if green != 0:
                    img.evaluate(operator='add', value=green * img.quantum_range, channel='green')
                if blue != 0:
                    img.evaluate(operator='add', value=blue * img.quantum_range, channel='blue')
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error ajustando balance de color: {e}")
            return None

    def adjust_levels(self, pil_image: PILImage.Image, black_point: float = 0.0, white_point: float = 1.0, gamma: float = 1.0) -> Optional[PILImage.Image]:
        """
        Ajusta los niveles de la imagen (puntos blanco y negro, gamma).

        Args:
            pil_image (PILImage.Image): Imagen PIL a procesar.
            black_point (float): Punto negro (0.0 a 1.0).
            white_point (float): Punto blanco (0.0 a 1.0).
            gamma (float): Corrección gamma.

        Returns:
            Optional[PILImage.Image]: Imagen PIL con niveles ajustados, o None si falla.
        """
        try:
            with self._pil_to_wand(pil_image) as img:
                img.level(black=black_point * img.quantum_range, white=white_point * img.quantum_range, gamma=gamma)
                return self._wand_to_pil(img)
        except Exception as e:
            logger.error(f"Error ajustando niveles: {e}")
            return None

    def create_collage(self, images: list[PILImage.Image], layout: list[list[int]], spacing: int) -> Optional[PILImage.Image]:
        """
        Crea un collage a partir de una lista de imágenes PIL utilizando un diseño de plantilla.

        Args:
            images (list[PILImage.Image]): Lista de imágenes PIL para el collage.
            layout (list[list[int]]): Una lista de listas que representa el diseño de la cuadrícula.
                                      Cada número en la cuadrícula representa el índice de la imagen.
            spacing (int): Espaciado en píxeles entre las imágenes.

        Returns:
            Optional[PILImage.Image]: La imagen del collage, o None si falla.
        """
        if not images or not layout:
            return None

        # Calculate cell dimensions based on the layout and a target collage width
        # This is a simplified approach; a more robust solution might involve
        # analyzing aspect ratios of input images or user-defined collage dimensions.
        max_collage_width = 1200
        num_cols = len(layout[0])
        num_rows = len(layout)

        # Calculate max cell width and height based on the layout and spacing
        cell_width = (max_collage_width - (num_cols - 1) * spacing) // num_cols
        cell_height = cell_width # For simplicity, assuming square cells or adjusting later

        # Resize images to fit into cells
        resized_images = []
        for img in images:
            img_copy = img.copy()
            img_copy.thumbnail((cell_width, cell_height), PILImage.LANCZOS)
            resized_images.append(img_copy)

        # Calculate overall collage dimensions
        collage_width = num_cols * cell_width + (num_cols - 1) * spacing
        collage_height = num_rows * cell_height + (num_rows - 1) * spacing

        collage = PILImage.new('RGB', (collage_width, collage_height), (255, 255, 255)) # White background

        # Paste images into the collage based on the layout
        for r_idx, row in enumerate(layout):
            for c_idx, img_idx in enumerate(row):
                if img_idx is not None and img_idx < len(resized_images):
                    img_to_paste = resized_images[img_idx]
                    x_offset = c_idx * (cell_width + spacing)
                    y_offset = r_idx * (cell_height + spacing)
                    collage.paste(img_to_paste, (x_offset, y_offset))
        
        return collage