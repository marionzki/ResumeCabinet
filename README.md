# ResumeCabinet

ResumeCabinet es una aplicación de escritorio desarrollada en Python utilizando [Flet](https://flet.dev/). Su propósito es facilitar la creación, personalización y exportación de currículums (CVs) en formato PDF. 

## Características Principales

* **Interfaz Gráfica Intuitiva**: Interfaz construida con Flet para gestionar tus datos personales y profesionales fácilmente.
* **Previsualización en Tiempo Real**: Observa los cambios que realizas en el diseño y contenido de tu currículum de manera inmediata.
* **Personalización del Diseño**: Ajusta colores (fondo, cabecera, barra lateral), tipografías, y tamaños a través de un panel de configuración detallado.
* **Sistema de Plantillas**: Guarda y carga diferentes configuraciones y perfiles mediante plantillas.
* **Exportación a PDF**: Genera tu CV en un archivo PDF de alta calidad, listo para enviar. Soporte robusto para documentos de múltiples páginas con ajuste automático de espacios y saltos de página limpios.
* **Gestión de Múltiples Secciones**: Añade y organiza secciones de Experiencia, Educación, Certificaciones, Idiomas y Tecnologías (con soporte visual para logos de software).

## Requisitos

* Python 3.x
* Paquetes listados en `requirements.txt` (incluyendo `flet`, librerías para generación de PDF, etc.)

## Instalación

1. Clona el repositorio:
   ```bash
   git clone https://github.com/tu-usuario/ResumeCabinet.git
   ```
2. Navega al directorio del proyecto:
   ```bash
   cd ResumeCabinet
   ```
3. (Opcional pero recomendado) Crea un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```
4. Instala las dependencias necesarias:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

Para arrancar la aplicación en modo desarrollo, simplemente ejecuta el archivo principal:

```bash
python main_flet.py
```

## Estructura Principal del Proyecto

* `main_flet.py`: Punto de entrada de la aplicación.
* `controller/`: Lógica que conecta la interfaz gráfica (vista) con los datos (modelo).
* `model/`: Estructuras de datos para el CV y manejo de configuraciones.
* `view_flet/`: Componentes modulares de la interfaz de usuario en Flet.
* `utils/`: Utilidades del sistema, incluyendo el motor de renderizado PDF.
* `templates/`: Plantillas preconfiguradas y guardadas por el usuario.
* `images/`: Recursos gráficos, incluyendo logos de herramientas y fotos de perfil de ejemplo.

## Construcción de Ejecutable (Windows)

El proyecto incluye scripts `.bat` para generar un ejecutable utilizando PyInstaller:
* `build_windows.bat`: Construye la aplicación en formato de directorio.
* `build_windows_onefile.bat`: Construye la aplicación empaquetada en un único archivo `.exe`.

## Licencia

Este proyecto es de código abierto.
