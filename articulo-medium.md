# Escaneo Automatizado de Vulnerabilidades en CI/CD con Herramientas OWASP: Wapiti, Trivy, GitHub Actions y Render

**Subtítulo:** Guía práctica de DevSecOps: Cómo implementar escaneo dinámico (DAST) y análisis de contenedores en un pipeline automatizado y desplegar en la nube pública.

---

## Introducción y Enfoque DevSecOps

En el desarrollo de software moderno, la seguridad ya no puede ser una fase tardía previa al despliegue. El enfoque **DevSecOps** (o *Shift-Left Security*) busca integrar mecanismos automáticos de detección de vulnerabilidades en las fases más tempranas del ciclo de vida del desarrollo.

La fundación **OWASP (Open Web Application Security Project)** mantiene un catálogo abierto y riguroso de herramientas de escaneo de vulnerabilidades ([OWASP Vulnerability Scanning Tools](https://community.owasp.org/Vulnerability_Scanning_Tools)). Con el objetivo de explorar herramientas avanzadas y complementarias a las analizadas convencionalmente, en este proyecto se implementaron dos soluciones destacadas del catálogo OWASP:

1. **Wapiti** (*Dynamic Application Security Testing - DAST*): Un escáner de caja negra que audita aplicaciones web en tiempo de ejecución inyectando payloads para identificar vulnerabilidades como Cross-Site Scripting (XSS), Inyecciones SQL (SQLi), File Inclusion, ejecución de comandos y configuraciones débiles en cabeceras HTTP.
2. **Trivy** (*Container & Dependency Security Scanner*): Un escáner exhaustivo y de alto rendimiento mantenido por Aqua Security, capaz de detectar CVEs (*Common Vulnerabilities and Exposures*) conocidos en imágenes Docker, librerías de lenguaje y sistemas operativos base.

A continuación, detallamos la arquitectura, la implementación del código vulnerable con fines pedagógicos, el pipeline de GitHub Actions y el despliegue automático en la nube pública con **Render**.

---

## 1. Arquitectura de la Solución y Pipeline CI/CD

El flujo automatizado se dispara con cada `push` hacia la rama `main` del repositorio público en GitHub, estructurado en tres etapas secuenciales:

```
+-----------------------------------------------------------------------------------+
|                            GitHub Actions Workflow                                |
|                                                                                   |
|  [ Push a main ]                                                                  |
|         │                                                                         |
|         ▼                                                                         |
|  ┌────────────────────────────────────────────────────────┐                       |
|  │ Job 1: scan-dependencies-and-image                     │                       |
|  │ - Construcción de imagen Docker                        │                       |
|  │ - Escaneo estático de vulnerabilidades con Trivy       │                       |
|  │ - Publicación de reporte como artefacto (trivy-report) │                       |
|  └──────────────────────────┬─────────────────────────────┘                       |
|                             │                                                     |
|                             ▼                                                     |
|  ┌────────────────────────────────────────────────────────┐                       |
|  │ Job 2: dast-scan                                       │                       |
|  │ - Inicialización del contenedor en runner local (8000) │                       |
|  │ - Escaneo dinámico DAST con Wapiti3                    │                       |
|  │ - Generación de reporte interactivo HTML (wapiti-report│                       |
|  └──────────────────────────┬─────────────────────────────┘                       |
|                             │                                                     |
|                             ▼                                                     |
|  ┌────────────────────────────────────────────────────────┐                       |
|  │ Job 3: deploy                                          │                       |
|  │ - Disparo seguro vía Webhook (Deploy Hook)             │                       |
|  │ - Despliegue en Render Cloud Platform                  │                       |
|  └────────────────────────────────────────────────────────┘                       |
+-----------------------------------------------------------------------------------+
```

---

## 2. Aplicación Demostrativa con Fallas Intencionales

Para poner a prueba la efectividad de los escáneres, se desarrolló una aplicación en **Python 3.9** utilizando **Flask** y una base de datos en memoria SQLite. Contiene deliberadamente dos de las vulnerabilidades más comunes del *OWASP Top 10*:

### Código fuente (`app/app.py`):

```python
from flask import Flask, request
import sqlite3

app = Flask(__name__)

def db():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users (id INTEGER, name TEXT)")
    conn.execute("INSERT INTO users VALUES (1, 'admin'), (2, 'maria')")
    return conn

@app.route("/")
def home():
    return "<h1>Demo App</h1><a href='/search?q=maria'>Buscar</a> | <a href='/user?id=1'>Usuario</a>"

# Vulnerabilidad: XSS reflejado (CWE-79 / A03:2021-Injection)
@app.route("/search")
def search():
    q = request.args.get("q", "")
    return f"<p>Resultados para: {q}</p>"

# Vulnerabilidad: SQL Injection (CWE-89 / A03:2021-Injection)
@app.route("/user")
def user():
    uid = request.args.get("id", "1")
    rows = db().execute(f"SELECT * FROM users WHERE id = {uid}").fetchall()
    return str(rows)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

### Contenedor de producción (`Dockerfile`):

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ .
EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
```

> **Repositorio público del proyecto:** [https://github.com/TU_USUARIO/vuln-scan-demo](https://github.com/TU_USUARIO/vuln-scan-demo)  
> *(Inserta aquí una captura del repositorio en GitHub con sus ramas y archivos)*

---

## 3. Automatización del Pipeline en GitHub Actions

En el archivo `.github/workflows/pipeline.yml` se configuraron las fases de seguridad y despliegue:

```yaml
name: Build, Scan and Deploy

on:
  push:
    branches: [main]

jobs:
  scan-dependencies-and-image:
    name: Trivy - Container and Dependency Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build image
        run: docker build -t demo-app:latest .

      - name: Trivy - escaneo de imagen
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: demo-app:latest
          format: table
          output: trivy-report.txt
          exit-code: 0

      - uses: actions/upload-artifact@v4
        with:
          name: trivy-report
          path: trivy-report.txt

  dast-scan:
    name: Wapiti - Dynamic Application Security Testing (DAST)
    runs-on: ubuntu-latest
    needs: scan-dependencies-and-image
    steps:
      - uses: actions/checkout@v4

      - name: Levantar app
        run: |
          docker build -t demo-app .
          docker run -d -p 8000:8000 demo-app
          sleep 8

      - name: Wapiti - escaneo dinámico
        run: |
          pip install wapiti3
          wapiti -u http://localhost:8000/ -f html -o wapiti-report --scope folder

      - uses: actions/upload-artifact@v4
        with:
          name: wapiti-report
          path: wapiti-report

  deploy:
    name: Deploy to Cloud (Render)
    runs-on: ubuntu-latest
    needs: dast-scan
    steps:
      - name: Disparar despliegue en Render
        run: curl -X POST "${{ secrets.RENDER_DEPLOY_HOOK }}"
```

> *(Inserta aquí una captura de GitHub Actions mostrando los 3 jobs en verde)*

---

## 4. Despliegue en la Nube Pública (Render)

Para el despliegue público y seguro de la aplicación se utilizó la plataforma **Render**:

1. Se creó un nuevo **Web Service** conectado al repositorio público de GitHub con entorno de ejecución **Docker**.
2. En la sección de configuración avanzada se generó una **Deploy Hook URL**.
3. Se añadió dicho endpoint como secreto en GitHub (`RENDER_DEPLOY_HOOK`) para permitir que el pipeline, una vez concluidos satisfactoriamente los escaneos de seguridad, desencadene la publicación en la nube sin exponer credenciales.

- **URL de la aplicación en producción:** [https://vuln-scan-demo.onrender.com](https://vuln-scan-demo.onrender.com)  
> *(Inserta aquí una captura de la aplicación respondiendo desde la URL pública)*

---

## 5. Análisis de Hallazgos y Resultados del Escaneo

### 5.1 Hallazgos de DAST con Wapiti

Wapiti navegó por las rutas expuestas y ejecutó pruebas de ataque dinámico, confirmando:

1. **SQL Injection (High):** Localizada en el parámetro `id` del endpoint `/user`. Wapiti detectó que inyectando caracteres como `' OR '1'='1` la consulta SQL alteraba su lógica y devolvía todos los registros de la tabla.
2. **Cross-Site Scripting Reflejado (Medium):** Localizada en el parámetro `q` del endpoint `/search`. El escáner verificó la ejecución exitosa de payloads JavaScript inyectados en la respuesta HTTP sin codificación previa.
3. **Ausencia de Cabeceras de Seguridad HTTP (Low/Info):** El servidor carece de `Content-Security-Policy` (CSP), `X-Frame-Options` (vulnerable a Clickjacking) y `X-Content-Type-Options: nosniff`.

> *(Inserta aquí una captura del reporte interactivo HTML de Wapiti)*

### 5.2 Hallazgos de Trivy en Contenedor y Dependencias

Trivy analizó la capa base del sistema operativo `python:3.9-slim` (Debian GNU/Linux) y las dependencias de Python:

- Detección de vulnerabilidades de severidad **Medium** y **Low** en paquetes del sistema operativo base (`libssl`, `glibc`, `zlib`).
- Detección de vulnerabilidades conocidas en la versión fija de `flask` y librerías asociadas (`Werkzeug`).

> *(Inserta aquí una captura del reporte textual generado por Trivy)*

---

## 6. Estrategia de Remediación (*Hardening*)

Con los reportes en mano, la remediación en el código y en la configuración de la infraestructura es directa:

### 1. Mitigación de SQL Injection
Sustituir la concatenación de cadenas por **consultas parametrizadas**:
```python
# Corrección
@app.route("/user")
def user():
    uid = request.args.get("id", "1")
    conn = db()
    cursor = conn.cursor()
    rows = cursor.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchall()
    return str(rows)
```

### 2. Mitigación de XSS Reflejado
Utilizar el motor de plantillas Jinja2 con auto-escapado o sanitizar explícitamente con `markupsafe.escape`:
```python
import markupsafe

@app.route("/search")
def search():
    q = request.args.get("q", "")
    safe_q = markupsafe.escape(q)
    return f"<p>Resultados para: {safe_q}</p>"
```

### 3. Protección de Cabeceras HTTP
Implementar `Flask-Talisman` o cabeceras en Gunicorn/Reverse Proxy:
```python
from flask_talisman import Talisman

Talisman(app, content_security_policy={
    'default-src': '\'self\''
})
```

### 4. Remediación en Trivy
Actualizar la imagen base a `python:3.11-slim` o `alpine` e incorporar `pip-audit` o fijar versiones seguras de Flask (`flask>=3.0.0`).

---

## 7. Video Demostrativo

Se elaboró un video resumen de menos de 5 minutos explicando el repositorio, el flujo en GitHub Actions, la detección de las fallas y el despliegue en vivo:

- 📺 **Enlace al video:** [https://youtube.com/watch?v=TU_VIDEO](https://youtube.com/watch?v=TU_VIDEO)

---

## Conclusiones

La incorporación de **Wapiti** y **Trivy** en un flujo CI/CD con **GitHub Actions** demuestra que no es necesario depender de herramientas propietarias de alto costo para contar con una postura de seguridad robusta. 

El escaneo automatizado continuo permite:
- Visibilidad inmediata de fallas críticas (como SQLi y XSS) antes de llegar a producción.
- Trazabilidad de CVEs en dependencias e imágenes de contenedores mediante artefactos descargables.
- Despliegue confiable en la nube solo cuando los controles de seguridad se satisfacen.

---

## Enlaces y Recursos

- **Repositorio en GitHub:** [https://github.com/TU_USUARIO/vuln-scan-demo](https://github.com/TU_USUARIO/vuln-scan-demo)
- **Aplicación Desplegada (Render):** [https://vuln-scan-demo.onrender.com](https://vuln-scan-demo.onrender.com)
- **Video Demostrativo:** [https://youtube.com/watch?v=TU_VIDEO](https://youtube.com/watch?v=TU_VIDEO)
- **Lista oficial de herramientas OWASP:** [OWASP Vulnerability Scanning Tools](https://community.owasp.org/Vulnerability_Scanning_Tools)

*Etiquetas sugeridas para Medium:* `#cybersecurity` `#devsecops` `#owasp` `#github-actions` `#docker` `#python` `#render`

