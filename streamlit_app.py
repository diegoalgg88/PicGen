#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import streamlit as st
from pathlib import Path
from PIL import Image
import io
import os
import signal
import time
from datetime import datetime
import re

from utils.config_manager import ConfigManager
from core.image_tool import ImageTool
from core.image_processor import ImageProcessor
from utils.collage_templates import CollageTemplates


@st.cache_resource
def get_config_manager():
    script_dir = Path(__file__).resolve().parent
    return ConfigManager(config_path=Path("config/pollinations_config.json"), script_dir=script_dir)

@st.cache_resource
def get_image_tool(_config_manager):
    script_dir = Path(__file__).resolve().parent
    return ImageTool(config_manager=_config_manager, script_dir=script_dir)

@st.cache_resource
def get_image_processor(_config_manager):
    return ImageProcessor(output_dir=_config_manager.get('output_dir'))

@st.cache_resource
def get_collage_templates():
    script_dir = Path(__file__).resolve().parent
    return CollageTemplates(script_dir=script_dir)


# --- Function Definitions (Moved to top) ---

def view_history_section():
    st.header("Historial de Imágenes")
    output_dir = Path(config_manager.get('output_dir'))
    if not output_dir.exists():
        st.warning("El directorio de salida no existe.")
    else:
        image_files = [f for f in output_dir.iterdir() if f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']]
        if not image_files:
            st.info("No hay imágenes generadas aún.")
        else:
            image_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            for img_file in image_files:
                st.image(str(img_file), caption=f"{img_file.name} ({(img_file.stat().st_size / 1024):.2f} KB)")

def generate_image_section(params):
    st.header("Generar Imagen con IA")
    prompt = st.text_area("Ingresa el prompt para generar la imagen:", height=150)
    generate_button = st.button("Generar Imagen")

    if generate_button and prompt:
        with st.spinner('Generando imagen...'):
            generated_image_path = image_tool.generate_image(prompt, **params)
        if generated_image_path:
            st.success("¡Imagen generada con éxito!")
            st.image(generated_image_path, caption="Imagen Generada")
        else:
            st.error("Error al generar la imagen. Revisa los logs para más detalles.")


def edit_image_local_section():
    st.header("Editar Imagen (Local)")
    uploaded_file = st.file_uploader("Sube una imagen para editar", type=["png", "jpg", "jpeg", "webp"])

    if uploaded_file is not None:
        # Guardar la imagen subida en session_state
        st.session_state['original_image'] = uploaded_file.read()
        st.session_state['original_image_name'] = uploaded_file.name
        # Reset edited_image_pil when a new file is uploaded
        st.session_state['edited_image_pil'] = Image.open(io.BytesIO(st.session_state['original_image']))

    if st.session_state['original_image'] is not None:
        original_image_bytes = st.session_state['original_image']
        original_image_pil = Image.open(io.BytesIO(original_image_bytes))

        # Use edited_image_pil from session_state or initialize it
        edited_image_pil = st.session_state['edited_image_pil']


        st.sidebar.subheader("Controles de Edición")

        # Categorized Adjustments
        with st.sidebar.expander("Ajustes Básicos y Transformaciones"):
            try:
                if st.button("Convertir a Blanco y Negro", key='bn_button'):
                    edited_image_pil = image_processor.convert_to_grayscale(edited_image_pil)
                    st.session_state['edited_image_pil'] = edited_image_pil

                brightness = st.slider("Brillo", 50, 150, 100, key='brightness_slider')
                contrast = st.slider("Contraste", 0.5, 1.5, 1.0, 0.05, key='contrast_slider')
                if brightness != 100 or contrast != 1.0:
                    edited_image_pil = image_processor.adjust_brightness_contrast(edited_image_pil, brightness, contrast)
                    st.session_state['edited_image_pil'] = edited_image_pil

                saturation = st.slider("Saturación", 0, 200, 100, key='saturation_slider')
                if saturation != 100:
                    edited_image_pil = image_processor.adjust_saturation(edited_image_pil, saturation)
                    st.session_state['edited_image_pil'] = edited_image_pil

                kelvin = st.slider("Temperatura (Kelvin)", 2000, 10000, 6500, key='kelvin_slider')
                if kelvin != 6500:
                    edited_image_pil = image_processor.adjust_temperature(edited_image_pil, kelvin)
                    st.session_state['edited_image_pil'] = edited_image_pil

                exposure_amount = st.slider("Exposición", -1.0, 1.0, 0.0, 0.01, key='exposure_slider')
                if exposure_amount != 0.0:
                    edited_image_pil = image_processor.adjust_exposure(edited_image_pil, exposure_amount)
                    st.session_state['edited_image_pil'] = edited_image_pil

                vignette_radius = st.slider("Viñeteado (Radio)", 0.0, 1.0, 0.0, 0.01, key='vignette_radius_slider')
                vignette_sigma = st.slider("Viñeteado (Sigma)", 0.0, 1.0, 0.0, 0.01, key='vignette_sigma_slider')
                if vignette_radius > 0 or vignette_sigma > 0:
                    edited_image_pil = image_processor.apply_vignette(edited_image_pil, vignette_radius, vignette_sigma)
                    st.session_state['edited_image_pil'] = edited_image_pil

                st.write("Recorte:")
                crop_x = st.number_input("X", min_value=0, value=0, key='crop_x_input')
                crop_y = st.number_input("Y", min_value=0, value=0, key='crop_y_input')
                crop_width = st.number_input("Ancho", min_value=1, value=original_image_pil.width, key='crop_width_input')
                crop_height = st.number_input("Alto", min_value=1, value=original_image_pil.height, key='crop_height_input')
                if st.button("Aplicar Recorte", key='crop_button'):
                    edited_image_pil = image_processor.crop_image(edited_image_pil, crop_x, crop_y, crop_width, crop_height)
                    st.session_state['edited_image_pil'] = edited_image_pil

                degrees = st.slider("Grados de Rotación", -180, 180, 0, key='rotation_slider')
                if degrees != 0:
                    edited_image_pil = image_processor.rotate_image(edited_image_pil, degrees)
                    st.session_state['edited_image_pil'] = edited_image_pil

                direction = st.radio("Voltear Imagen", ["Ninguno", "Horizontal", "Vertical"], key='flip_flop_radio')
                if direction == "Horizontal":
                    edited_image_pil = image_processor.flip_flop_image(edited_image_pil, "flop")
                    st.session_state['edited_image_pil'] = edited_image_pil
                elif direction == "Vertical":
                    edited_image_pil = image_processor.flip_flop_image(edited_image_pil, "flip")
                    st.session_state['edited_image_pil'] = edited_image_pil

                st.write("Redimensionar:")
                new_width = st.number_input("Nuevo Ancho", min_value=1, value=original_image_pil.width, key='resize_width_input')
                new_height = st.number_input("Nuevo Alto", min_value=1, value=original_image_pil.height, key='resize_height_input')
                if new_width != original_image_pil.width or new_height != original_image_pil.height:
                    edited_image_pil = image_processor.resize_image(edited_image_pil, new_width, new_height)
                    st.session_state['edited_image_pil'] = edited_image_pil

            except Exception as e:
                st.error(f"Error en ajustes básicos y transformaciones: {e}")

        with st.sidebar.expander("Filtros Artísticos y Estilizados"):
            try:
                if st.button("Aplicar Sepia", key='sepia_button'):
                    edited_image_pil = image_processor.apply_sepia(edited_image_pil)
                    st.session_state['edited_image_pil'] = edited_image_pil

                grain_amount = st.slider("Granulado (Cantidad)", 0.0, 1.0, 0.0, 0.01, key='grain_slider')
                if grain_amount > 0:
                    edited_image_pil = image_processor.apply_grain(edited_image_pil, grain_amount)
                    st.session_state['edited_image_pil'] = edited_image_pil

                oil_paint_radius = st.slider("Pintura al Óleo (Radio)", 0.0, 10.0, 0.0, 0.1, key='oil_paint_slider')
                if oil_paint_radius > 0:
                    edited_image_pil = image_processor.apply_oil_paint(edited_image_pil, oil_paint_radius)
                    st.session_state['edited_image_pil'] = edited_image_pil

                charcoal_radius = st.slider("Carboncillo (Radio)", 0.0, 5.0, 0.0, 0.1, key='charcoal_radius_slider')
                charcoal_sigma = st.slider("Carboncillo (Sigma)", 0.0, 5.0, 0.0, 0.1, key='charcoal_sigma_slider')
                if charcoal_radius > 0 or charcoal_sigma > 0:
                    edited_image_pil = image_processor.apply_charcoal(edited_image_pil, charcoal_radius, charcoal_sigma)
                    st.session_state['edited_image_pil'] = edited_image_pil

                emboss_radius = st.slider("Relieve (Radio)", 0.0, 5.0, 0.0, 0.1, key='emboss_radius_slider')
                emboss_sigma = st.slider("Relieve (Sigma)", 0.0, 5.0, 0.0, 0.1, key='emboss_sigma_slider')
                if emboss_radius > 0 or emboss_sigma > 0:
                    edited_image_pil = image_processor.apply_emboss(edited_image_pil, emboss_radius, emboss_sigma)
                    st.session_state['edited_image_pil'] = edited_image_pil

                swirl_degrees = st.slider("Remolino (Grados)", -360, 360, 0, key='swirl_slider')
                if swirl_degrees != 0:
                    edited_image_pil = image_processor.apply_swirl(edited_image_pil, swirl_degrees)
                    st.session_state['edited_image_pil'] = edited_image_pil

                wave_amplitude = st.slider("Onda (Amplitud)", 0.0, 50.0, 0.0, 1.0, key='wave_amplitude_slider')
                wave_length = st.slider("Onda (Longitud)", 0.0, 200.0, 0.0, 1.0, key='wave_length_slider')
                if wave_amplitude > 0 or wave_length > 0:
                    edited_image_pil = image_processor.apply_wave(edited_image_pil, wave_amplitude, wave_length)
                    st.session_state['edited_image_pil'] = edited_image_pil

                if st.button("Aplicar Nitidez", key='sharpen_button'):
                    edited_image_pil = image_processor.apply_sharpen(edited_image_pil)
                    st.session_state['edited_image_pil'] = edited_image_pil

                blur_radius = st.slider("Desenfoque (Radio)", 0.0, 10.0, 0.0, 0.1, key='blur_radius_slider')
                blur_sigma = st.slider("Desenfoque (Sigma)", 0.0, 10.0, 0.0, 0.1, key='blur_sigma_slider')
                if blur_radius > 0 or blur_sigma > 0:
                    edited_image_pil = image_processor.apply_blur(edited_image_pil, blur_radius, blur_sigma)
                    st.session_state['edited_image_pil'] = edited_image_pil

                if st.button("Aplicar Negativo", key='negative_button'):
                    edited_image_pil = image_processor.apply_negative(edited_image_pil)
                    st.session_state['edited_image_pil'] = edited_image_pil

                posterize_levels = st.slider("Posterizar (Niveles)", 1, 256, 256, key='posterize_slider')
                if posterize_levels < 256:
                    edited_image_pil = image_processor.apply_posterize(edited_image_pil, posterize_levels)
                    st.session_state['edited_image_pil'] = edited_image_pil

                solarize_threshold = st.slider("Solarizar (Umbral)", 0.0, 1.0, 0.0, 0.01, key='solarize_slider')
                if solarize_threshold > 0:
                    edited_image_pil = image_processor.apply_solarize(edited_image_pil, solarize_threshold)
                    st.session_state['edited_image_pil'] = edited_image_pil

                edge_detect_radius = st.slider("Detección de Bordes (Radio)", 0.0, 5.0, 0.0, 0.1, key='edge_detect_radius_slider')
                edge_detect_sigma = st.slider("Detección de Bordes (Sigma)", 0.0, 5.0, 0.0, 0.1, key='edge_detect_sigma_slider')
                if edge_detect_radius > 0 or edge_detect_sigma > 0:
                    edited_image_pil = image_processor.apply_edge_detect(edited_image_pil, edge_detect_radius, edge_detect_sigma)
                    st.session_state['edited_image_pil'] = edited_image_pil

                pixelate_x = st.slider("Pixelado (Factor X)", 1, 50, 1, key='pixelate_x_slider')
                pixelate_y = st.slider("Pixelado (Factor Y)", 1, 50, 1, key='pixelate_y_slider')
                if pixelate_x > 1 or pixelate_y > 1:
                    edited_image_pil = image_processor.apply_pixelate(edited_image_pil, pixelate_x, pixelate_y)
                    st.session_state['edited_image_pil'] = edited_image_pil

                crystallize_radius = st.slider("Cristalizar (Radio)", 1, 20, 1, key='crystallize_slider')
                if crystallize_radius > 1:
                    edited_image_pil = image_processor.apply_crystallize(edited_image_pil, float(crystallize_radius))
                    st.session_state['edited_image_pil'] = edited_image_pil

                implode_amount = st.slider("Implosión (Cantidad)", -1.0, 1.0, 0.0, 0.01, key='implode_slider')
                if implode_amount != 0.0:
                    edited_image_pil = image_processor.apply_implode(edited_image_pil, implode_amount)
                    st.session_state['edited_image_pil'] = edited_image_pil

                explode_amount = st.slider("Explosión (Cantidad)", -1.0, 1.0, 0.0, 0.01, key='explode_slider')
                if explode_amount != 0.0:
                    edited_image_pil = image_processor.apply_explode(edited_image_pil, explode_amount)
                    st.session_state['edited_image_pil'] = edited_image_pil

            except Exception as e:
                st.error(f"Error en filtros artísticos y estilizados: {e}")

        with st.sidebar.expander("Filtros de Tonalidad Global"):
            try:
                duotone_color1 = st.color_picker("Color 1 (Duotono)", '#FF0000', key='duotone_color1')
                duotone_color2 = st.color_picker("Color 2 (Duotono)", '#0000FF', key='duotone_color2')
                if st.button("Aplicar Duotono", key='duotone_button'):
                    edited_image_pil = image_processor.apply_duotone(edited_image_pil, duotone_color1, duotone_color2)
                    st.session_state['edited_image_pil'] = edited_image_pil

                highlight_color = st.color_picker("Color Luces (Split Tone)", '#FFFF00', key='highlight_color')
                shadow_color = st.color_picker("Color Sombras (Split Tone)", '#00FFFF', key='shadow_color')
                if st.button("Aplicar Tono Dividido", key='split_tone_button'):
                    edited_image_pil = image_processor.apply_split_tone(edited_image_pil, highlight_color, shadow_color)
                    st.session_state['edited_image_pil'] = edited_image_pil

                st.write("Balance de Color (RGB):")
                red_balance = st.slider("Rojo", -1.0, 1.0, 0.0, 0.01, key='red_balance_slider')
                green_balance = st.slider("Verde", -1.0, 1.0, 0.0, 0.01, key='green_balance_slider')
                blue_balance = st.slider("Azul", -1.0, 1.0, 0.0, 0.01, key='blue_balance_slider')
                if red_balance != 0.0 or green_balance != 0.0 or blue_balance != 0.0:
                    edited_image_pil = image_processor.adjust_color_balance(edited_image_pil, red_balance, green_balance, blue_balance)
                    st.session_state['edited_image_pil'] = edited_image_pil

                st.write("Ajuste de Niveles:")
                black_point = st.slider("Punto Negro", 0.0, 1.0, 0.0, 0.01, key='black_point_slider')
                white_point = st.slider("Punto Blanco", 0.0, 1.0, 1.0, 0.01, key='white_point_slider')
                gamma = st.slider("Gamma", 0.1, 5.0, 1.0, 0.01, key='gamma_slider')
                if black_point != 0.0 or white_point != 1.0 or gamma != 1.0:
                    edited_image_pil = image_processor.adjust_levels(edited_image_pil, black_point, white_point, gamma)
                    st.session_state['edited_image_pil'] = edited_image_pil

            except Exception as e:
                st.error(f"Error en filtros de tonalidad global: {e}")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Imagen Original")
            st.image(original_image_pil, use_container_width=True)
        with col2:
            st.subheader("Imagen Editada")
            st.image(edited_image_pil, use_container_width=True, caption="Aplicando cambios...")

        # Download button
        buf = io.BytesIO()
        edited_image_pil.save(buf, format="PNG")
        byte_im = buf.getvalue()
        st.download_button(
            label="Descargar Imagen Editada",
            data=byte_im,
            file_name=f"edited_{st.session_state['original_image_name']}",
            mime="image/png"
        )

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Imagen Original")
            st.image(original_image_pil, use_container_width=True)
        with col2:
            st.subheader("Imagen Editada")
            st.image(edited_image_pil, use_container_width=True, caption="Aplicando cambios...")

        # Download button
        buf = io.BytesIO()
        edited_image_pil.save(buf, format="PNG")
        byte_im = buf.getvalue()
        st.download_button(
            label="Descargar Imagen Editada",
            data=byte_im,
            file_name=f"edited_{st.session_state['original_image_name']}",
            mime="image/png"
        )


def edit_image_ia_section(params):
    st.header("Editar Imagen (IA)")
    uploaded_file_ia = st.file_uploader("Sube una imagen para editar con IA", type=["png", "jpg", "jpeg", "webp"])

    if uploaded_file_ia is not None:
        st.session_state['original_image_ia'] = uploaded_file_ia.read()
        st.session_state['original_image_name_ia'] = uploaded_file_ia.name
        st.session_state['edited_image_ia_pil'] = None # Reset edited image when new file is uploaded

    if st.session_state['original_image_ia'] is not None:
        original_image_ia_bytes = st.session_state['original_image_ia']
        original_image_ia_pil = Image.open(io.BytesIO(original_image_ia_bytes))

        prompt_ia = st.text_area("Ingresa el prompt para la edición con IA:", height=150)
        edit_button_ia = st.button("Editar con IA")

        if edit_button_ia and prompt_ia:
            # Save original image to a temporary file for image_tool
            temp_original_path = Path(config_manager.get('output_dir')) / f"temp_original_{st.session_state['original_image_name_ia']}"
            original_image_ia_pil.save(temp_original_path)

            with st.spinner('Editando imagen con IA...'):
                edited_image_ia_path = image_tool.edit_image(prompt_ia, str(temp_original_path), **params)
            
            # Clean up temporary file
            temp_original_path.unlink(missing_ok=True)

            if edited_image_ia_path:
                st.success("¡Imagen editada con IA con éxito!")
                st.session_state['edited_image_ia_pil'] = Image.open(edited_image_ia_path)
            else:
                st.error("Error al editar la imagen con IA. Revisa los logs para más detalles.")
        
        # Display images
        col1_ia, col2_ia = st.columns(2)
        with col1_ia:
            st.subheader("Imagen Original")
            st.image(original_image_ia_pil, use_container_width=True)
        with col2_ia:
            st.subheader("Imagen Editada (IA)")
            if st.session_state['edited_image_ia_pil'] is not None:
                st.image(st.session_state['edited_image_ia_pil'], use_container_width=True)
            else:
                st.image(original_image_ia_pil, use_container_width=True, caption="Esperando edición...")

def generate_from_template_section():
    st.header("Generar con Plantilla")
    templates = image_tool.templates.TEMPLATES
    if not templates:
        st.warning("No hay plantillas. Crea 'prompt_templates.json'.")
        return

    template_names = list(templates.keys())
    selected_template_name = st.selectbox("Selecciona una plantilla:", template_names)

    if selected_template_name:
        template_info = templates[selected_template_name]
        base_prompt = template_info.get('base', '')
        st.write(f"Prompt base: `{base_prompt}`")

        placeholders = template_info.get('placeholders', {})
        template_vars = {}
        for p, p_info in placeholders.items():
            description = p_info.get('description', '')
            examples = p_info.get('examples', [])
            help_text = f"{description}\nEjemplos: {', '.join(examples)}"
            template_vars[p] = st.text_input(f"Valor para '{p}':", help=help_text)

        generate_template_button = st.button("Generar Imagen desde Plantilla")

        if generate_template_button:
            final_vars = {}
            for p, value in template_vars.items():
                if not value.strip():
                    examples = placeholders.get(p, {}).get('examples', [])
                    if examples:
                        final_vars[p] = image_tool.templates.get_random_example(p, selected_template_name)
                    else:
                        st.warning(f"El campo '{p}' está vacío y no tiene ejemplos para elegir uno aleatorio.")
                        return
                else:
                    final_vars[p] = value

            prompt, params = image_tool.templates.apply_template(selected_template_name, **final_vars)
            
            # Translate the prompt before sending it to the AI
            translated_prompt = image_tool._translate_prompt(prompt)

            with st.spinner('Generando imagen desde plantilla...'):
                generated_image_path = image_tool.generate_image(translated_prompt, **params)
            
            if generated_image_path:
                st.success("¡Imagen generada con éxito desde plantilla!")
                st.image(generated_image_path, caption="Imagen Generada")
            else:
                st.error("Error al generar la imagen desde plantilla. Revisa los logs para más detalles.")


def create_collage_section():
    st.header("Crear Collage")
    uploaded_files = st.file_uploader("Sube las imágenes para el collage", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True)

    if uploaded_files:
        images = []
        for uploaded_file in uploaded_files:
            images.append(Image.open(uploaded_file))

        st.subheader("Configuración del Collage")
        cols = st.number_input("Número de Columnas", min_value=1, value=2)
        spacing = st.slider("Espaciado entre imágenes (px)", min_value=0, max_value=50, value=10)

        if st.button("Generar Collage"):
            if len(images) > 0:
                with st.spinner("Generando collage..."):
                    # For simple collage, create a dummy layout based on cols
                    # This assumes a simple grid where each image takes one cell
                    rows = (len(images) + cols - 1) // cols
                    layout = [[i for i in range(j * cols, min((j + 1) * cols, len(images)))] for j in range(rows)]
                    
                    collage_image = image_processor.create_collage(images, layout, spacing)
                
                if collage_image:
                    st.success("¡Collage generado con éxito!")
                    st.image(collage_image, caption="Tu Collage", use_container_width=True)

                    buf = io.BytesIO()
                    collage_image.save(buf, format="PNG")
                    byte_im = buf.getvalue()
                    st.download_button(
                        label="Descargar Collage",
                        data=byte_im,
                        file_name="collage.png",
                        mime="image/png"
                    )
                else:
                    st.error("Error al generar el collage.")
            else:
                st.warning("Por favor, sube al menos una imagen para crear el collage.")

def create_collage_from_template_section():
    st.header("Crear Collage con Plantilla")
    
    templates = collage_templates.TEMPLATES
    if not templates:
        st.warning("No hay plantillas de collage. Crea 'collage_templates.json'.")
        return

    template_names = [t['name'] for t in templates.values()]
    selected_template_name = st.selectbox("Selecciona una plantilla de collage:", template_names)

    if selected_template_name:
        selected_template = None
        for key, template in templates.items():
            if template['name'] == selected_template_name:
                selected_template = template
                break

        if selected_template:
            min_images = selected_template.get('min_images', 1)
            max_images = selected_template.get('max_images', len(selected_template['layout']) * len(selected_template['layout'][0]))
            spacing = selected_template.get('spacing', 10)

            st.info(f"Esta plantilla requiere entre {min_images} y {max_images} imágenes.")
            uploaded_files = st.file_uploader(
                f"Sube {min_images} a {max_images} imágenes para el collage", 
                type=["png", "jpg", "jpeg", "webp"], 
                accept_multiple_files=True
            )

            if uploaded_files:
                if len(uploaded_files) < min_images or len(uploaded_files) > max_images:
                    st.warning(f"Por favor, sube entre {min_images} y {max_images} imágenes para esta plantilla.")
                else:
                    images = []
                    for uploaded_file in uploaded_files:
                        images.append(Image.open(uploaded_file))

                    if st.button("Generar Collage con Plantilla"):
                        with st.spinner("Generando collage con plantilla..."):
                            collage_image = image_processor.create_collage(images, selected_template['layout'], spacing)
                        
                        if collage_image:
                            st.success("¡Collage generado con éxito usando la plantilla!")
                            st.image(collage_image, caption="Tu Collage con Plantilla", use_container_width=True)

                            buf = io.BytesIO()
                            collage_image.save(buf, format="PNG")
                            byte_im = buf.getvalue()
                            st.download_button(
                                label="Descargar Collage",
                                data=byte_im,
                                file_name=f"collage_{selected_template_name.replace(' ', '_')}.png",
                                mime="image/png"
                            )
                        else:
                            st.error("Error al generar el collage con plantilla.")

def generate_batch_section(params):
    st.header("Generación por Lote")

    if 'batch_prompts' not in st.session_state:
        st.session_state.batch_prompts = ["" for _ in range(5)]

    def add_prompt():
        st.session_state.batch_prompts.append("")

    for i, prompt in enumerate(st.session_state.batch_prompts):
        st.session_state.batch_prompts[i] = st.text_input(f"Prompt #{i+1}", value=prompt, key=f"prompt_{i}")

    st.button("Agregar más prompts", on_click=add_prompt)

    generate_button = st.button("Generar Lote")

    if generate_button:
        prompt_list = [p.strip() for p in st.session_state.batch_prompts if p.strip()]
        if not prompt_list:
            st.warning("Por favor, ingresa al menos un prompt.")
            return

        st.info(f"Se generarán {len(prompt_list)} imágenes.")
        progress_bar = st.progress(0)
        generated_images = []

        for i, prompt in enumerate(prompt_list):
            with st.spinner(f"Generando imagen {i+1}/{len(prompt_list)}: '{prompt[:30]}...' "):
                translated_prompt = image_tool._translate_prompt(prompt)
                generated_image_path = image_tool.generate_image(translated_prompt, **params)
                if generated_image_path:
                    generated_images.append(generated_image_path)
                else:
                    st.error(f"Error al generar la imagen para el prompt: '{prompt}'")
            progress_bar.progress((i + 1) / len(prompt_list))

        if generated_images:
            st.success("¡Lote de imágenes generado con éxito!")
            for img_path in generated_images:
                st.image(img_path, caption=Path(img_path).name)

def sidebar_config(opcion):
    st.sidebar.header("Configuración de Herramienta")

    # --- Modelos de Generación de Imágenes (Text-to-Image) ---
    generation_models = {
        "kandinsky-2.2": "Modelo artístico avanzado para diseños detallados.",
        "stable-diffusion-xl": "Última versión de SD con mayor calidad y detalle.",
        "deepfloyd-if": "Modelo en cascada para máxima calidad de imagen.",
        "dalle-3": "Modelo de OpenAI con excelente comprensión de prompts.",
        "playground-v2.5": "Modelo optimizado para generación rápida.",
        "pixart-alpha": "Modelo rápido para generación en tiempo real.",
        "sdxs": "Stable Diffusion optimizado para velocidad."
    }

    # --- Modelos de Edición de Imágenes (Image-to-Image) ---
    editing_models = {
        "flux-kontext": "Modelo avanzado para transformación y edición de imágenes (img2img).",
        "kontext": "Modelo original para edición contextual de imágenes (requiere prompt específico).",
        "flux": "Modelo general que puede usarse para ediciones basadas en una imagen de referencia."
    }


    if opcion == "Generar Imagen" or opcion == "Generación por Lote":
        model = st.sidebar.selectbox(
            "Modelo de IA", 
            options=list(generation_models.keys()), 
            index=1,
            help="Selecciona el modelo de IA que se usará para crear la imagen."
        )
        # Mostrar la descripción del modelo seleccionado
        st.sidebar.info(generation_models[model])

        width = st.sidebar.number_input("Ancho", min_value=1, value=config_manager.get('width'))
        height = st.sidebar.number_input("Alto", min_value=1, value=config_manager.get('height'))
        seed = st.sidebar.number_input("Seed", value=config_manager.get('seed', 0))
        return {"model": model, "width": width, "height": height, "seed": seed}

    elif opcion == "Editar Imagen (IA)":
        model_edicion = st.sidebar.selectbox(
            "Modelo de Edición", 
            options=list(editing_models.keys()), 
            index=0,
            help="Selecciona el modelo de IA que se usará para editar la imagen."
        )
        # Mostrar la descripción del modelo seleccionado
        st.sidebar.info(editing_models[model_edicion])
        
        return {"model_edicion": model_edicion}
        
    return {}

config_manager = get_config_manager()
image_tool = get_image_tool(config_manager)
image_processor = get_image_processor(config_manager)
collage_templates = get_collage_templates()


# Initialize session state variables
if 'original_image' not in st.session_state:
    st.session_state['original_image'] = None
if 'original_image_name' not in st.session_state:
    st.session_state['original_image_name'] = None
if 'edited_image_pil' not in st.session_state:
    st.session_state['edited_image_pil'] = None
if 'original_image_ia' not in st.session_state:
    st.session_state['original_image_ia'] = None
if 'original_image_name_ia' not in st.session_state:
    st.session_state['original_image_name_ia'] = None
if 'edited_image_ia_pil' not in st.session_state:
    st.session_state['edited_image_ia_pil'] = None


st.title("Image Generator & Editor")
st.header("Bienvenido a la nueva interfaz gráfica.")

main_option = st.sidebar.selectbox("Selecciona una categoría", 
    ["Generar", "Editar", "Historial", "Collage"]
)

sub_option = None
params = {}

if main_option == "Generar":
    sub_option = st.sidebar.selectbox("Selecciona una opción de generación",
        ["Imagen Única", "Con Plantilla", "Por Lote"]
    )
    if sub_option == "Imagen Única" or sub_option == "Por Lote":
        params = sidebar_config("Generar Imagen") # Use existing config logic
    elif sub_option == "Con Plantilla":
        # Template generation has its own internal config, no need for sidebar_config here
        pass
elif main_option == "Editar":
    sub_option = st.sidebar.selectbox("Selecciona una opción de edición",
        ["Con IA", "Local"]
    )
    if sub_option == "Con IA":
        params = sidebar_config("Editar Imagen (IA)") # Use existing config logic
    elif sub_option == "Local":
        # Local editing has its own internal config
        pass

if main_option == "Generar":
    if sub_option == "Imagen Única":
        generate_image_section(params)
    elif sub_option == "Con Plantilla":
        generate_from_template_section()
    elif sub_option == "Por Lote":
        generate_batch_section(params)
elif main_option == "Editar":
    if sub_option == "Con IA":
        edit_image_ia_section(params)
    elif sub_option == "Local":
        edit_image_local_section()
elif main_option == "Historial":
    view_history_section()
elif main_option == "Collage":
    create_collage_from_template_section()

# Botón para cerrar la aplicación en la barra lateral
if st.sidebar.button("Cerrar Aplicación"):
    st.sidebar.warning("Cerrando la aplicación...")
    time.sleep(2)
    pid = os.getpid()
    os.kill(pid, signal.SIGTERM)
