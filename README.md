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

El proyecto incluye dos scripts `.bat` que automatizan la instalación de dependencias y la generación de un ejecutable nativo para Windows utilizando **PyInstaller**. Los ejecutables generados se guardarán automáticamente en la carpeta `dist/`.

Opciones de compilación:

1. **Un solo archivo (Recomendado)**:
   Ejecuta `build_windows_onefile.bat`. Este script empaquetará toda la aplicación y sus recursos en un único archivo ejecutable (`dist\ResumeCabinet.exe`), lo que facilita mucho compartir el programa.

2. **Formato directorio**:
   Ejecuta `build_windows.bat`. Este script generará una carpeta en `dist\main_flet\` con el ejecutable y todas sus dependencias desempaquetadas. Es útil si el modo de "un solo archivo" tarda mucho en arrancar o tiene problemas de rendimiento.

*Nota: Asegúrate de ejecutar estos scripts desde la raíz del proyecto. Los scripts instalarán las dependencias necesarias de forma automática antes de compilar.*

## Licencia

Este proyecto es de código abierto.
