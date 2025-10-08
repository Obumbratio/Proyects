# Antivirus Inteligente

## Aviso de seguridad

Este proyecto implementa un **antivirus educativo** orientado al análisis y a
la remediación segura dentro del propio equipo. No elimina nada de manera
permanente sin confirmación del usuario. No envía información a la red y está
pensado para ejecutarse con transparencia y en modo "simulación" si así se
requiere.

## Características principales

- **Escaneo modular** de archivos, procesos, procesos GPU y archivos
  duplicados.
- **Reportes detallados** por tipo de escaneo y reporte maestro del escaneo
  completo en formato JSON (o texto si se configura).
- **Modo simulación (`--dry-run`)** para revisar qué acciones se realizarían sin
  modificar el sistema.
- **Cuarentena y remediación segura** con registro de todas las acciones.
- **Búsqueda de duplicados** mediante hash incremental para optimizar el uso de
  disco.
- **Detección heurística** con reglas simples y base de firmas extensible.
- **Limpieza de cachés y recomendaciones de optimización** no destructivas.
- **Interfaz por consola** con menú interactivo y comandos directos.
- **Registro rotativo** y configuración externa mediante `config/default_config.json`.
- **Pruebas unitarias** para los componentes críticos (`files`, `dupes`,
  `heuristics`, `report`).

## Requisitos

- Python 3.9 o superior.
- Dependencias estándar de la biblioteca estándar. El uso de `psutil` es
  opcional; si no está disponible, se usan rutas alternativas seguras.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install --upgrade pip
```

No se requieren paquetes adicionales para ejecutar las funcionalidades básicas.

## Uso

Ejecute el menú interactivo:

```bash
python main.py
```

Comandos directos disponibles:

```bash
python main.py full-scan --dry-run
python main.py scan-files --path "C:/Usuarios/Nombre/Downloads"
python main.py scan-processes
python main.py scan-gpu
python main.py find-dupes --paths "C:/Usuarios/Nombre/Documents" "D:/Media"
python main.py reports --last --format json
python main.py remediate --from-report reports/20240101T000000Z_escaneo_archivos.json
python main.py optimize
```

### Modo simulación

Agregue `--dry-run` para que el antivirus muestre todas las acciones que
realizaría sin aplicarlas. Esto es especialmente útil antes de ejecutar
limpiezas o enviar elementos a cuarentena.

### Configuración

El archivo `config/default_config.json` define opciones seguras por defecto: 
carpeta de reportes, directorio de cuarentena, tamaño de bloque de lectura,
registro, etc. Puede copiar este archivo a
`~/.intelligent_antivirus/config.json` para personalizar su instalación local.

### Reportes

Cada escaneo genera un archivo JSON en la carpeta `reports/`. El menú y el
comando `python main.py reports` permiten consultar los reportes más recientes
en formato legible o en JSON para su integración con otras herramientas.

### Remediación

Después de cualquier escaneo el menú ofrece:

1. **Eliminar/Enviar a cuarentena** – mueve los elementos sospechosos a la
   cuarentena (opción predeterminada) o elimina permanentemente tras
   confirmación explícita.
2. **Finalizar procesos sospechosos** – guía para realizar la acción de forma
   manual y segura.
3. **Limpiar caché** – detecta directorios temporales y ofrece limpiarlos de
   forma segura (respeta el modo simulación).
4. **Optimizar el sistema** – presenta recomendaciones no destructivas.

Todas las acciones generan un reporte post-acción en consola y se registran en
el archivo de log.

## Desarrollo y pruebas

Ejecute las pruebas automatizadas con:

```bash
python -m unittest discover -s tests
```

Los módulos están organizados en:

- `core/` – lógica de escaneo, reportes, heurísticas, remediación, etc.
- `ui/` – interfaz de usuario.
- `tests/` – pruebas unitarias.

## Licencia

Este proyecto se distribuye bajo la licencia MIT (consulte el archivo
`LICENSE`). Se proporciona **sin garantía**; utilícelo con precaución y revíse
los reportes antes de tomar acciones permanentes.
