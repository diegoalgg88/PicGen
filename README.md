# PicGen
# Generador y Editor de Imágenes Avanzado

Este proyecto es una suite de herramientas de imagen potente y versátil, que ofrece dos interfaces de usuario distintas (una GUI web y una CLI de terminal) para interactuar con la API de Pollinations AI y realizar una amplia gama de ediciones de imágenes de forma local.

## ✨ Características Principales

- **Interfaz Dual**:
  - **GUI Web (Streamlit)**: Una interfaz gráfica intuitiva, interactiva y fácil de usar para una experiencia visual fluida.
  - **CLI (Terminal)**: Una interfaz de línea de comandos para usuarios que prefieren trabajar en la terminal.

- **Generación de Imágenes con IA**:
  - **Generación Única**: Crea imágenes a partir de descripciones de texto detalladas (prompts).
  - **Generación por Lote**: Procesa múltiples prompts de una vez, ya sea desde un archivo o introducidos manualmente.
  - **Generación con Plantillas**: Utiliza plantillas predefinidas para crear imágenes complejas con un estilo consistente, rellenando solo las partes variables.

- **Edición de Imágenes**:
  - **Edición con IA**: Sube una imagen y modifícala con un prompt de texto, aprovechando modelos como `flux-kontext`.
  - **Editor Local Avanzado**: Un completo set de herramientas para editar imágenes directamente en tu máquina, sin necesidad de API. Incluye:
    - **Ajustes Básicos**: Brillo, contraste, saturación, exposición, temperatura de color, recorte, rotación, redimensión.
    - **Filtros Artísticos**: Pintura al óleo, carboncillo, sepia, granulado, relieve, remolino, y más.
    - **Filtros de Tonalidad**: Duotono, tono dividido (split toning), ajuste de niveles y balance de color.
    - **Efectos Especiales**: Negativo, posterizar, solarizar, pixelado, cristalizar, y detección de bordes.

- **Creación de Collages**:
  - Crea collages de imágenes fácilmente utilizando plantillas de diseño predefinidas en un archivo JSON.

- **Sistema de Gestión**:
  - **Configuración Centralizada**: Personaliza el comportamiento de la aplicación a través del archivo `config/pollinations_config.json` y gestiona tus claves de API de forma segura con `config/.env`.
  - **Caché Inteligente**: Guarda las imágenes generadas y evita repetir llamadas a la API para los mismos prompts, ahorrando tiempo y recursos.
  - **Historial Visual**: Navega por un historial de todas las imágenes que has generado y editado.
  - **Herramientas de Diagnóstico**: Verifica la conectividad con las APIs y el estado de la configuración.

## ⚙️ Requisitos Previos

Antes de empezar, asegúrate de tener instalado lo siguiente:

1.  **Python 3.8+**.
2.  **ImageMagick**: Esta es una dependencia **crucial** para que el editor de imágenes local funcione.
    - Visita [ImageMagick.org](https://imagemagick.org/script/download.php) para descargar e instalarlo.
    - **Importante**: Durante la instalación, asegúrate de marcar la casilla que dice **"Install legacy utilities (e.g., convert)"** o **"Add application directory to your system path"**.
3.  **Librerías de Python**: Se instalarán en el siguiente paso.

## 🚀 Instalación y Configuración

1. **Clona o descarga este repositorio.**

2. **Instala las dependencias de Python**:
   Navega al directorio del proyecto (`app_3`) en tu terminal y ejecuta:

   ```bash
   pip install -r requirements.txt
   ```

3. **Configura tus credenciales**:

   - En la carpeta `config/`, renombra el archivo `.env.example` a `.env`.

   - Abre el archivo `.env` y añade tus claves de API:

     ```env
     POLLINATIONS_API_KEY="tu_api_key_de_pollinations"
     GOFILE_API_TOKEN="tu_api_token_de_gofile"
     GOFILE_FOLDER_ID="tu_id_de_carpeta_en_gofile"
     ```

   - **Nota**: La `GOFILE_API_TOKEN` y `GOFILE_FOLDER_ID` son necesarias **únicamente** para la función de "Editar con IA". Las demás funciones no las requieren.

4. **(Opcional) Personaliza la configuración general**:
   Abre `config/pollinations_config.json` para ajustar parámetros por defecto como las dimensiones de las imágenes, el modelo de IA preferido, etc.

## ▶️ Cómo Ejecutar la Aplicación

Puedes elegir entre la interfaz gráfica (recomendada) o la de línea de comandos.

### Interfaz Gráfica de Usuario (GUI con Streamlit)

Es la forma más sencilla e interactiva de usar la aplicación.

1. Abre una terminal en el directorio `app_3`.

2. Ejecuta el siguiente comando:

   ```bash
   streamlit run streamlit_app.py
   ```

3. La aplicación se abrirá automáticamente en tu navegador web.

### Interfaz de Línea de Comandos (CLI)

Para usuarios que prefieren la terminal.

1. Abre una terminal en el directorio `app_3`.

2. Ejecuta el siguiente comando:

   ```bash
   python main.py
   ```

3. Sigue las instrucciones que aparecerán en el menú interactivo.

## 📖 Guía Detallada de Funcionalidades (GUI)

La interfaz de Streamlit se organiza en categorías en la barra lateral.

### Generar

- **Imagen Única**: Escribe un prompt, ajusta los parámetros en la barra lateral (modelo, dimensiones) y haz clic en "Generar Imagen".
- **Con Plantilla**: Selecciona una plantilla (ej. "Retrato"), rellena los campos variables (ej. sujeto, estilo) y la aplicación construirá un prompt detallado por ti.
- **Por Lote**: Añade varios prompts en los campos de texto. La aplicación los procesará uno por uno, mostrando una barra de progreso.

### Editar

- **Con IA**: Sube una imagen, escribe un prompt describiendo la modificación (ej. "cambia el fondo a una playa tropical") y la IA transformará tu imagen.
- **Local**: Sube una imagen y usa la gran variedad de controles en la barra lateral para aplicar ajustes en tiempo real. Los controles están agrupados en:
  - **Ajustes Básicos**: Brillo, contraste, recorte, etc.
  - **Filtros Artísticos**: Sepia, carboncillo, pintura al óleo, etc.
  - **Filtros de Tonalidad**: Duotono, tono dividido, etc.

### Historial

- Muestra una galería con todas las imágenes que has creado, ordenadas de la más reciente a la más antigua.

### Collage

- Selecciona una plantilla de collage (ej. "Cuadrícula 2x2"), sube el número requerido de imágenes y la aplicación las combinará en un único archivo de imagen.

### Cerrar Aplicación

- En la parte inferior de la barra lateral, encontrarás un botón para detener el servidor de Streamlit y cerrar la aplicación de forma segura.

## 🔧 Estructura del Proyecto

```
app_3/
├── config/                 # Archivos de configuración (JSON, .env)
├── core/                   # Lógica principal de la aplicación
│   ├── image_processor.py  # Funciones de edición local de imágenes (con Wand)
│   └── image_tool.py       # Lógica para interactuar con la API de Pollinations
├── DOCS/                   # Documentación adicional
├── generated_images/       # Directorio de salida para las imágenes creadas
├── input/                  # Coloca aquí las imágenes que quieras editar
├── logs/                   # Archivos de log diarios
├── ui/                     # Lógica para la interfaz de línea de comandos (CLI)
│   └── cli.py
├── utils/                  # Módulos de utilidad (gestor de config, caché, etc.)
├── .env.example            # Plantilla para las variables de entorno
├── main.py                 # Punto de entrada para la CLI
├── requirements.txt        # Dependencias de Python
└── streamlit_app.py        # Punto de entrada para la GUI de Streamlit
```

## 🎨 Personalización

Puedes extender fácilmente la aplicación:

- **Añadir Plantillas de Prompt**: Edita `config/prompt_templates.json` para añadir tus propias estructuras de prompts.
- **Añadir Plantillas de Collage**: Edita `config/collage_templates.json` para definir nuevos diseños de collage.
