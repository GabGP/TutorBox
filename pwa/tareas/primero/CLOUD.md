# Hosting Gratuito — Aprende Matemáticas con Kuk

Tu app es un PWA 100% estático (solo la carpeta `public/`). No necesita servidor.
Las opciones están ordenadas de más fácil a más difícil.

---

## Opción 1 — Netlify (más fácil, arrastra y suelta)

**Gratis incluye:**
- 100 GB de ancho de banda por mes
- 300 minutos de build por mes
- 1 sitio por cuenta en el plan gratuito (ilimitados con drag & drop)
- HTTPS automático
- URL: `tu-nombre.netlify.app`
- Sin tarjeta de crédito

**Límite que te importa:** 100 GB/mes es ~500,000 visitas al mes. Más que suficiente.

### Pasos

1. Ve a **https://app.netlify.com/signup**
2. Crea una cuenta con tu correo (o Google/GitHub)
3. Verifica tu correo y entra al dashboard
4. En el dashboard, busca el recuadro que dice **"Want to deploy a new site without connecting to Git?"**
   - Si no lo ves, haz clic en **"Add new site"** → **"Deploy manually"**
5. Abre el Explorador de archivos en tu computadora y navega a:
   `C:\Users\gdavd\Documents\Vibe\edTech\primariagt\primero\public`
6. Selecciona **todos los archivos y carpetas dentro de `public/`** (Ctrl+A)
7. Arrastra esa selección al recuadro de Netlify que dice **"Drag and drop your site output folder here"**
8. Espera 10–30 segundos mientras sube
9. Netlify te da una URL aleatoria tipo `https://amazing-darwin-123456.netlify.app`
10. (Opcional) Cambia el nombre: **Site settings → General → Site name → Change site name**

**Para actualizar la app en el futuro:**
- Repite los pasos 4–8. Netlify reemplaza el sitio automáticamente.

---

## Opción 2 — GitHub Pages (fácil, requiere Git)

**Gratis incluye:**
- Ancho de banda ilimitado (uso justo, sin SLA exacto — en práctica ~100 GB/mes)
- 1 GB de almacenamiento por repositorio
- HTTPS automático
- URL: `tu-usuario.github.io/nombre-repo`
- Sin tarjeta de crédito

**Límite que te importa:** Repositorios públicos son gratis. Si quieres el repo privado, necesitas GitHub Pro ($4/mes) para tener Pages con privado.

### Pasos

**Parte A — Sube el código a GitHub**

1. Ve a **https://github.com/signup** y crea una cuenta
2. Verifica tu correo
3. Haz clic en el botón **"+"** (esquina superior derecha) → **"New repository"**
4. Ponle un nombre, ejemplo: `kuk-matematicas`
5. Selecciona **Public**
6. **No** marques ninguna casilla de inicialización (sin README, sin .gitignore)
7. Haz clic en **"Create repository"**
8. GitHub te muestra una página con instrucciones. Copia la URL del repo, ejemplo:
   `https://github.com/tu-usuario/kuk-matematicas.git`

9. Abre una terminal en tu computadora (busca "Git Bash" o "CMD")
10. Ejecuta estos comandos uno por uno:

```bash
cd "C:\Users\gdavd\Documents\Vibe\edTech\primariagt\primero\public"
git init
git add .
git commit -m "Initial deploy"
git branch -M main
git remote add origin https://github.com/TU-USUARIO/kuk-matematicas.git
git push -u origin main
```

> Reemplaza `TU-USUARIO` con tu usuario de GitHub real.

**Parte B — Activa GitHub Pages**

11. En GitHub, abre tu repositorio
12. Haz clic en **"Settings"** (pestaña superior)
13. En el menú izquierdo, haz clic en **"Pages"**
14. En **"Source"**, selecciona **"Deploy from a branch"**
15. En **"Branch"**, selecciona **`main`** y la carpeta **`/ (root)`**
16. Haz clic en **"Save"**
17. Espera 1–3 minutos
18. Recarga la página — GitHub te muestra tu URL:
    `https://tu-usuario.github.io/kuk-matematicas/`

**Para actualizar la app en el futuro:**
```bash
cd "C:\Users\gdavd\Documents\Vibe\edTech\primariagt\primero\public"
git add .
git commit -m "Update"
git push
```
GitHub Pages se actualiza automáticamente en 1–2 minutos.

**Problema común:** El service worker puede fallar en subdirectorios. Si la app no carga offline, edita `public/sw.js` y cambia la línea:
```js
const CACHE_NAME = `kuk-math-${CACHE_VERSION}`;
```
No se necesita ningún cambio adicional para rutas — la app usa hash routing (`#map`, `#lesson`) que funciona bien en Pages.

---

## Opción 3 — Cloudflare Pages (más potente, requiere Git + cuenta Cloudflare)

**Gratis incluye:**
- **Ancho de banda ilimitado** (sin límite de GB)
- **Solicitudes ilimitadas**
- 500 builds por mes
- HTTPS automático con CDN global (más rápido en Guatemala que las otras opciones)
- URL: `tu-proyecto.pages.dev`
- Sin tarjeta de crédito

**Límite que te importa:** El único límite real es 500 builds/mes — si subes cambios más de 500 veces al mes, los builds se pausan hasta el siguiente mes. En práctica nunca llegarás a ese límite.

### Pasos

**Parte A — Sube el código a GitHub** (igual que Opción 2, pasos 1–10)

Si ya hiciste la Opción 2, salta directo a la Parte B.

**Parte B — Conecta Cloudflare Pages**

1. Ve a **https://dash.cloudflare.com/sign-up** y crea una cuenta
2. Verifica tu correo
3. En el dashboard de Cloudflare, en el menú izquierdo busca **"Workers & Pages"**
4. Haz clic en **"Pages"** → **"Create a project"**
5. Selecciona **"Connect to Git"**
6. Haz clic en **"Connect GitHub"**
7. Autoriza a Cloudflare a acceder a tu GitHub (selecciona "Only select repositories" y elige `kuk-matematicas`)
8. Haz clic en **"Begin setup"**
9. En la pantalla de configuración del build:
   - **Project name:** `kuk-matematicas` (o el nombre que quieras)
   - **Production branch:** `main`
   - **Framework preset:** `None`
   - **Build command:** *(dejar en blanco)*
   - **Build output directory:** *(dejar en blanco — Cloudflare sirve el root del repo)*
10. Haz clic en **"Save and Deploy"**
11. Espera 1–2 minutos mientras hace el primer deploy
12. Cloudflare te da la URL: `https://kuk-matematicas.pages.dev`

**Para actualizar la app en el futuro:**
```bash
cd "C:\Users\gdavd\Documents\Vibe\edTech\primariagt\primero\public"
git add .
git commit -m "Update"
git push
```
Cloudflare detecta el push y redespliega automáticamente en ~1 minuto.

**Ventaja extra:** Cloudflare tiene servidores en Latinoamérica (incluido Miami y São Paulo, los más cercanos a Guatemala), lo que hace la app más rápida para tus usuarios que GitHub Pages o Netlify.

---

## Comparación rápida

| | Netlify | GitHub Pages | Cloudflare Pages |
|---|---|---|---|
| **Dificultad** | Muy fácil | Fácil | Media |
| **Ancho de banda** | 100 GB/mes | ~100 GB/mes | Ilimitado |
| **Velocidad en GT** | Buena | Buena | Mejor |
| **Actualizar** | Drag & drop | `git push` | `git push` |
| **Tarjeta de crédito** | No | No | No |
| **Tiempo de setup** | 5 min | 15 min | 20 min |
| **URL gratis** | `.netlify.app` | `.github.io/repo` | `.pages.dev` |

**Recomendación:** Empieza con **Netlify** (Opción 1) para lanzar hoy mismo. Si más adelante quieres más velocidad o ancho de banda ilimitado, migra a **Cloudflare Pages** — es el mejor long-term.
