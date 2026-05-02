# ResumeCabinet

ResumeCabinet es una aplicación de escritorio en Python con [Flet](https://flet.dev/) para crear, personalizar y exportar currículums en PDF. En su versión actual funciona en **modo portable**: los datos viven en una carpeta **`data/`** junto al ejecutable (o en el directorio del proyecto al desarrollar), de modo que puedes copiar toda la carpeta a un USB u otro PC y seguir donde lo dejaste.

## Características principales

* **Interfaz clara**: pestañas para configuración, diseño, plantillas CV, información personal, experiencia, formación, competencias, software y lenguajes.
* **Varios perfiles**: distintos CV bajo carpetas por usuario dentro de `data/users/`.
* **Librería global compartida**: Competencias, Software y Lenguajes son comunes a todos los perfiles; están en `data/global/library.json`, con logos en `data/global/software/` y `data/global/languages/`.
* **Avatares por perfil**: imágenes de perfil en `data/users/<perfil>/avatar/`.
* **Plantillas de CV** (pestaña Templates): todas las `.json` visibles están en **`data/users/<perfil>/templates/`**; pueden cargarse y **eliminarse** libremente. Los ejemplos iniciales se copian desde `data/defaults/example_templates/` cuando el usuario aún no tiene ninguna plantilla.
* **Carga inteligente de plantillas**: al aplicar una plantilla se actualizan configuración/diseño/cabecera, pero **no se borran** módulos que hayas añadido después (solo se sincroniza el activado/desactivado cuando coinciden con la plantilla).
* **PDF**: previsualización y exportación mediante ReportLab (`utils/pdf_generator.py`).

## Requisitos

* **Desarrollo**: Python 3.x y dependencias de `requirements.txt` (entre ellas `flet` y librerías de PDF).
* **Uso sólo ejecutable**: no hace falta Python en la máquina destino si repartís el paquete portable ya construido (`.exe` + `data/`).

## Instalación (desde código)

```bash
git clone https://github.com/tu-usuario/ResumeCabinet.git
cd ResumeCabinet
python -m venv venv
# Windows:
venv\Scripts\activate
pip install -r requirements.txt
```

## Uso en desarrollo

```bash
python main_flet.py
```

La primera ejecución crea **`data/`** en la raíz del proyecto copiando desde el código la estructura por defecto (incluye `defaults/example_templates/` dentro de ese árbol).

## Estructura del proyecto (referencia rápida)

| Ruta | Uso |
|------|-----|
| `main_flet.py` | Entrada de la aplicación |
| `controller/` | Coordinación vista–modelo, perfiles y persistencia |
| `model/` | CV y módulos (texto, experiencia, imágenes, etc.) |
| `view_flet/` | Interfaz Flet |
| `utils/` | PDF, rutas de medios, arranque portable |
| `defaults/example_templates/` | Plantillas `.json` de **ejemplo** en el repo; se sincronizan a `data/defaults/example_templates/` al ejecutar o al preparar el portable |
| `defaults/` *(resto)* | Seeds JSON para perfil inicial y librería (generados/usados desde `data/defaults/` en tiempo de ejecución) |
| `images/logo`, `images/profile` | PNG de referencia para rellenar `data/global/...` y avatares de ejemplo |
| `tools/prepare_distribution_data.py` | Rellena `dist/data/` tras PyInstaller para el ZIP portable |
| `ResumeCabinet.spec` | PyInstaller — un solo ejecutable |

## Modo portable: carpeta `data/`

Todo el estado de la aplicación se resuelve bajo **`RESUMECABINET_DATA_ROOT`** (normalmente **`./data`** respecto al `.exe` o al proyecto en desarrollo).

Estructura típica después de usar la app:

```text
ResumeCabinet/              (carpeta que repartís)
├── ResumeCabinet.exe       (opcional nombre según build)
├── data/
│   ├── global/
│   │   ├── library.json
│   │   ├── software/
│   │   └── languages/
│   ├── defaults/
│   │   ├── example_templates/   (.json de ejemplo; no sobrescribe al usuario)
│   │   ├── avatars/
│   │   └── … (initial_profile.json, etc.)
│   └── users/
│       └── mario_noriega/       (clave derivada del nombre de perfil)
│           ├── user_data.json
│           ├── templates/       ← plantillas cargables/borrables desde la UI
│           ├── avatar/
│           └── …
└── ...
```

Sin `data/` pregenerada al lado del ejecutable, la app creará carpetas vacías según uso; los **PNG de ejemplo** y las **plantillas de ejemplo** se vuelcan desde el proceso de desarrollo/prepare cuando corresponda (ver compilación más abajo).

## Construcción del ejecutable (Windows)

1. **`build_portable.bat`** (recomendado para un paquete listo para compartir)  
   - Ejecuta `PyInstaller --noconfirm ResumeCabinet.spec` → **`dist\ResumeCabinet.exe`**.  
   - Ejecuta **`python tools\prepare_distribution_data.py`** → crea **`dist\data\`** con `global/software`, `global/languages`, `defaults/avatars`, **`defaults/example_templates`**, etc.  
   **Reparto:** Zip con `ResumeCabinet.exe` y **`data\`** dentro del mismo nivel (el contenido típico de `dist\` después del script).

2. **`build_windows_onefile.bat`**  
   Genera un único `.exe` en `dist/` con PyInstaller desde línea de comandos. **Importante:** si quieres el mismo comportamiento portable que Arriba, tras el build copia/alinea manualmente **`data/`** usando `prepare_distribution_data.py` (apuntando a la carpeta `data` donde vaya el exe) o reutiliza el flujo del `.bat` portable.

3. **`build_windows.bat`**  
   Build en modo carpeta COLLECT (`main_flet.spec`/`dist/main_flet/` según proyecto); útil si preferís ejecutable “desempaquetado”.

*`build/` y `dist/` están en `.gitignore`: no forman parte del histórico de Git por defecto.*

## ¿Qué subir al repo y cómo distribuir “desde cero”?

### Qué suele tener sentido mantener **en Git** (código fuente)

* Todo el proyecto **excepto** artefactos de build (`build/`, `dist/`).
* `defaults/example_templates/` con tus JSON de muestra (ya versionados).
* `images/`, `requirements.txt`, `*.spec`, `build_*.bat`, `tools/prepare_distribution_data.py`.

*Opcional:* si en desarrollo usás `data/` en la raíz del repo para pruebas y no querés que esos perfiles/cachés locales entren en el commit, puedes añadir la carpeta `data/` al `.gitignore`.

Quien clone el repo puede:

```bash
pip install -r requirements.txt
build_portable.bat
```

y obtendrá en `dist/` un **`.exe`** + **`data/`** reproducibles para probar el portable localmente **sin subir binarios**.

### Opciones si quieres que “solo descargar y usar” no requiera compilar

1. **GitHub Releases (recomendado)**  
   - No subís el ejecutable dentro del mismo commit del código.  
   - En una **Release**, adjuntás un **`ResumeCabinet_portable.zip`** con `ResumeCabinet.exe` + `data/`.  
   - Ventaja: repo ligero y clonar rápido; los usuarios finales pillan el ZIP desde Releases.

2. **Subir una carpeta “portable” dentro del mismo repo**  
   - Pesada: el `.exe` y datos duplicados en cada commit.  
   - Además **`dist/`** está ignorado por `.gitignore`; tendrías que o bien **quitar esa regla** para una carpeta concreta (p. ej. `release/portable/`) usando reglas específicas, o bien hacer `git add -f release/portable/...` (funciona pero es fácil olvidarlo al actualizar).  
   - **Git LFS** ayuda si el exe supera el lím cómodo para GitHub (~100 MB típico recomendación), pero añade complejidad.  
   - Úsalos solo si tienes muy pocos usuarios técnicos y quieres un único lugar de descarga; para la mayoría, **Release + ZIP es más limpio**.

3. **Rama o repo paralelo sólo distribución**  
   - Menos habitual; mismo problema de binarios grandes en historia Git.

### Resumen práctico

| Objetivo | Acción |
|----------|--------|
| Colaboradores / código abierto | Repo con fuente + `defaults/example_templates` + README; Releases con ZIP opcional |
| Usuario final sin compilar | Subir **`ResumeCabinet.exe` + `data/`** (misma carpeta madre que el exe) vía Release o servidor |
| Mantener igualdad con lo que compilas vos | Ejecutá siempre **`build_portable.bat`** antes de crear el ZIP de distribución |

## Licencia

Este proyecto es de código abierto (ajustá aquí tu licencia concreta si usás SPDX o archivo `LICENSE`).
