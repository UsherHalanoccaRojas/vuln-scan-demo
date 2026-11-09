# Guía completa: Escaneo de vulnerabilidades con herramientas OWASP (Wapiti + Trivy)

> **Importante:** verifica en https://community.owasp.org/Vulnerability_Scanning_Tools que las herramientas elegidas aparezcan en la lista y que no se hayan usado en los laboratorios. Si alguna se usó, cámbiala. Cada integrante debe publicar su propio artículo, así que pueden repartirse herramientas distintas (Wapiti, Vega, Nuclei, Trivy, Dependency-Check, etc.).

---

## Índice

1. Requisitos de la tarea
2. Contenido del repositorio GitHub
3. Configuración del despliegue en la nube
4. Artículo para Medium (listo para pegar)
5. Guion del video (máx. 5 min)
6. Checklist de entrega
7. Formato del ZIP

---

## 1. Requisitos de la tarea

- Artículo por integrante en Medium, Dev.to o Hashnode sobre escaneo de vulnerabilidades con herramientas de la lista OWASP **no usadas en los laboratorios**.
- El artículo debe incluir:
  1. Repositorio público de la app.
  2. Despliegue mediante automatización.
  3. Publicación en nube pública o SaaS público.
  4. Video de máximo 5 minutos en YouTube, Facebook, TikTok u otra red pública.
- Enviar enlaces del artículo y del video al grupo de Telegram.
- Subir los enlaces en un ZIP a la tarea.

---

## 2. Contenido del repositorio GitHub

### Estructura

```
vuln-scan-demo/
├── app/
│   ├── app.py
│   └── requirements.txt
├── Dockerfile
├── .github/
│   └── workflows/
│       └── pipeline.yml
├── .gitignore
└── README.md
```

### `app/app.py`

App Flask pequeña con fallas intencionales para que los escáneres encuentren algo.

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

# Vulnerable a XSS reflejado
@app.route("/search")
def search():
    q = request.args.get("q", "")
    return f"<p>Resultados para: {q}</p>"

# Vulnerable a SQL Injection
@app.route("/user")
def user():
    uid = request.args.get("id", "1")
    rows = db().execute(f"SELECT * FROM users WHERE id = {uid}").fetchall()
    return str(rows)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

### `app/requirements.txt`

```
flask==2.2.5
gunicorn==21.2.0
```

### `Dockerfile`

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ .
EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
```

### `.github/workflows/pipeline.yml`

```yaml
name: Build, Scan and Deploy

on:
  push:
    branches: [main]

jobs:
  scan-dependencies-and-image:
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
    runs-on: ubuntu-latest
    needs: dast-scan
    steps:
      - name: Disparar despliegue en Render
        run: curl -X POST "${{ secrets.RENDER_DEPLOY_HOOK }}"
```

> Si `trivy-action@master` da problemas, fija una versión estable (por ejemplo `aquasecurity/trivy-action@0.28.0`). Si Wapiti no guarda el reporte donde esperas, revisa la ruta con `ls` en un paso previo.

### `.gitignore`

```
__pycache__/
*.pyc
reports/
```

### `README.md`

~~~markdown
# vuln-scan-demo

Aplicación web Flask con vulnerabilidades intencionales, usada para demostrar
escaneo de vulnerabilidades automatizado con herramientas de la lista OWASP.

## Herramientas
- **Wapiti** (DAST): escaneo dinámico de caja negra.
- **Trivy**: escaneo de imagen de contenedor y dependencias.

## Ejecutar localmente
    docker build -t demo-app .
    docker run -p 8000:8000 demo-app
    # abrir http://localhost:8000

## Pipeline
GitHub Actions: build -> Trivy -> Wapiti -> deploy en Render.

## Enlaces
- App desplegada: https://TU-APP.onrender.com
- Artículo: LINK_ARTICULO
- Video: LINK_VIDEO

## Integrantes
- Nombre Apellido
~~~

---

## 3. Configuración del despliegue en la nube pública

1. Crea una cuenta en **Render.com** (plan gratuito).
2. New → **Web Service** → conecta tu repositorio de GitHub → Runtime: **Docker**.
3. En Settings copia el **Deploy Hook URL**.
4. En GitHub: Settings → Secrets and variables → Actions → New repository secret → nombre `RENDER_DEPLOY_HOOK`, valor: la URL copiada.
5. Haz `git push` a `main` y verifica en la pestaña **Actions** que las tres etapas terminan en verde.

Alternativas de nube: Railway, Fly.io, Google Cloud Run, Azure App Service, AWS App Runner.

---

## 4. Artículo para Medium (listo para pegar)

**Título:** Escaneo de vulnerabilidades en una aplicación web con Wapiti y Trivy: pipeline automatizado con GitHub Actions y Render

**Subtítulo:** Cómo integrar herramientas de la lista OWASP en un flujo CI/CD y desplegar en la nube.

---

### Introducción

Detectar vulnerabilidades antes de que un atacante lo haga es una de las prácticas más importantes del desarrollo seguro. OWASP mantiene un catálogo de herramientas de escaneo de vulnerabilidades, y en este artículo uso dos que no se trabajaron en los laboratorios del curso: **Wapiti** (análisis dinámico, DAST) y **Trivy** (análisis de imágenes y dependencias). Los integro en un pipeline automatizado y despliego la aplicación en un proveedor de nube pública.

### 1. La aplicación y su repositorio público

Construí una aplicación en Flask con dos fallas intencionales:

- **XSS reflejado** en `/search`, porque el parámetro `q` se devuelve sin sanitizar.
- **SQL Injection** en `/user`, porque el parámetro `id` se concatena directamente en la consulta.

El código completo está en: `https://github.com/TU_USUARIO/vuln-scan-demo`

*(Pega aquí una captura del repositorio.)*

### 2. Herramientas utilizadas

**Wapiti** es un escáner de caja negra: no necesita el código fuente, rastrea las páginas y prueba inyecciones, XSS, inclusión de archivos y más contra la aplicación en ejecución.

**Trivy** analiza imágenes de contenedores, dependencias y configuraciones en busca de CVEs conocidos.

Ambas están disponibles de forma gratuita y se integran fácilmente en CI/CD.

### 3. Pipeline de automatización

Usé **GitHub Actions** con tres etapas encadenadas:

1. **Build + Trivy:** construye la imagen Docker y la escanea.
2. **DAST con Wapiti:** levanta el contenedor, ejecuta el escáner y guarda el reporte HTML como artefacto.
3. **Deploy:** si las etapas anteriores terminan bien, se llama al Deploy Hook de Render para publicar la nueva versión.

*(Pega el fragmento del archivo `pipeline.yml` y una captura de la ejecución exitosa en la pestaña Actions.)*

Cada `git push` a `main` activa todo el proceso sin intervención manual.

### 4. Despliegue en la nube pública

Publiqué la aplicación en **Render**, que construye la imagen desde el Dockerfile del repositorio. La app quedó disponible en: `https://TU-APP.onrender.com`

*(Captura de la app funcionando.)*

### 5. Resultados del escaneo

**Wapiti** detectó:

- Cross Site Scripting en el parámetro `q` de `/search`.
- SQL Injection en el parámetro `id` de `/user`.
- Cabeceras de seguridad ausentes (CSP, X-Frame-Options).

**Trivy** reportó vulnerabilidades en paquetes del sistema base y dependencias de Python, clasificadas por severidad.

*(Pega capturas de ambos reportes. Reemplaza esta lista con tus hallazgos reales.)*

### 6. Remediación

- **SQLi:** usar consultas parametrizadas: `execute("SELECT * FROM users WHERE id = ?", (uid,))`
- **XSS:** escapar la salida con `markupsafe.escape(q)`.
- **Cabeceras:** agregar CSP y X-Frame-Options con `flask-talisman`.
- **Trivy:** actualizar la imagen base y las versiones de las dependencias.

### 7. Video demostrativo

El proceso completo, desde el código hasta el reporte, está en este video de menos de 5 minutos: `LINK_DEL_VIDEO`

### Conclusiones

Integrar escáneres en el pipeline convierte la seguridad en parte del flujo diario de desarrollo y no en una revisión tardía. Con herramientas gratuitas de la lista OWASP, un equipo pequeño puede detectar fallas comunes y corregirlas antes de llegar a producción.

**Repositorio:** `LINK_GITHUB`
**Aplicación desplegada:** `LINK_APP`
**Video:** `LINK_VIDEO`

*Etiquetas sugeridas: cybersecurity, devsecops, owasp, github-actions, docker*

---

## 5. Guion del video (máx. 5 min)

| Tiempo | Contenido |
|---|---|
| 0:00-0:30 | Presentación del equipo y objetivo |
| 0:30-1:15 | Mostrar el repositorio público y el código de la app |
| 1:15-2:15 | Explicar el pipeline y hacer un `git push` en vivo |
| 2:15-3:15 | Ver la ejecución en GitHub Actions y el despliegue en Render |
| 3:15-4:15 | Mostrar los reportes de Wapiti y Trivy |
| 4:15-5:00 | Remediación rápida y cierre |

Grábalo con OBS o la grabación de pantalla de tu sistema y súbelo a YouTube (puede ser "no listado").

---

## 6. Checklist de entrega

- [ ] Repositorio público con todo el contenido
- [ ] Pipeline funcionando (captura en verde)
- [ ] App desplegada con URL pública
- [ ] Video de menos de 5 min subido a una red social
- [ ] Artículo publicado en Medium (o Dev.to / Hashnode)
- [ ] Enlaces enviados al grupo de Telegram
- [ ] ZIP con los enlaces subido a la tarea

---

## 7. Formato del ZIP

Crea un archivo `enlaces.txt` y comprímelo en un `.zip`:

```
Integrante: Nombre Apellido
Artículo: https://medium.com/...
Video: https://youtube.com/...
GitHub: https://github.com/...
App: https://...onrender.com
```

---

## Variantes por integrante (para que cada artículo sea distinto)

| Integrante | Herramienta DAST/SAST | Herramienta de dependencias/imagen |
|---|---|---|
| 1 | Wapiti | Trivy |
| 2 | Nuclei | Dependency-Check |
| 3 | Vega | Grype |
| 4 | Arachni / Nikto | Snyk CLI |

Confirma que cada una figure en la lista de OWASP antes de usarla.
