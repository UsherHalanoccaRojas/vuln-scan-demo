# vuln-scan-demo

Aplicación web Flask con vulnerabilidades intencionales, diseñada para demostrar el escaneo automatizado de seguridad en flujos CI/CD mediante herramientas oficiales del catálogo OWASP.

## Herramientas OWASP Implementadas
- **Wapiti** (DAST): Escaneo dinámico de caja negra enfocado en aplicaciones web (detección de XSS reflejado, SQL Injection, divulgación de información sensible y malas configuraciones de cabeceras HTTP).
- **Trivy**: Escáner de seguridad para imágenes de contenedores Docker y dependencias (detección de CVEs conocidos y vulnerabilidades en paquetes OS/Python).

## Estructura del Proyecto
```text
vuln-scan-demo/
├── app/
│   ├── app.py             # Código vulnerable intencional (Flask + SQLite)
│   └── requirements.txt   # Dependencias de Python
├── Dockerfile             # Definición de contenedor multi-etapa/producción
├── .github/
│   └── workflows/
│       └── pipeline.yml   # Flujo CI/CD con Trivy, Wapiti y despliegue continuo
├── .gitignore
└── README.md
```

## Ejecución Local

Para levantar la aplicación con Docker:

```bash
docker build -t demo-app .
docker run -d -p 8000:8000 --name demo-container demo-app
```

Acceder a `http://localhost:8000` en el navegador.

Para detener el contenedor:
```bash
docker stop demo-container && docker rm demo-container
```

## Pipeline CI/CD (GitHub Actions)

El flujo automatizado se ejecuta en cada `push` a la rama `main` y consta de tres fases secuenciales:
1. **scan-dependencies-and-image:** Compila la imagen Docker y ejecuta Trivy para escanear el sistema operativo base y librerías, guardando el reporte como artefacto.
2. **dast-scan:** Despliega el contenedor en el runner de GitHub Actions y ejecuta Wapiti contra los endpoints web, generando un informe completo en formato HTML.
3. **deploy:** Tras la aprobación de las etapas de análisis, activa un webhook (Deploy Hook) en Render para desplegar la última versión en la nube pública.

## Enlaces de Entrega
- **Aplicación desplegada:** `https://TU-APP.onrender.com`
- **Artículo en Medium:** `https://medium.com/@TU_USUARIO/...`
- **Video demostrativo (< 5 min):** `https://youtube.com/...`
- **Repositorio de GitHub:** `https://github.com/TU_USUARIO/vuln-scan-demo`

## Integrantes
- Nombre y Apellido

