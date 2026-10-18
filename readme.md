# ONU Get Data

Aplicación automatizada para la extracción, monitorización y gestión de datos de dispositivos ONU, optimizada para su ejecución en clústeres ligeros de Kubernetes (K3s) sobre un entorno de desarrollo Linux/Debian.

---

## 📁 Estructura del Proyecto

El repositorio mantiene una estructura limpia y modular para organizar el código fuente, los manifiestos de Kubernetes y la automatización del despliegue:

```text
onu-get-data/
├── app/                  # Código fuente de la aplicación y Dockerfile
│   ├── Dockerfile        # Imagen base e instrucciones de construcción
│   ├── onu_get_data.py   # Script principal de extracción y monitorización
│   ├── readme.md         # Documentación del proyecto
│   └── datos_onu/        # Datos locales generados (ignorado por .gitignore)
│       ├── interface_check.png
│       └── log_onu.csv
```

---