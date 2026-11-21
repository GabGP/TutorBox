# APK Installation Audio Instructions (Kʼicheʼ & Qʼeqchiʼ)

Generated offline with Meta MMS Text-to-Speech via [generate_tts.py](generate_tts.py):

- **Kʼicheʼ (Central):** `facebook/mms-tts-quc-dialect_central` → [kiche_instruction.wav](kiche_instruction.wav), published as `pwa/tareas/descargas/audio/kiche.mp3`
- **Qʼeqchiʼ:** `facebook/mms-tts-kek` → [qeqchi_instruction.wav](qeqchi_instruction.wav), published as `pwa/tareas/descargas/audio/qeqchi.mp3`

## Setup and Use

Setup works like the Spanish voices. A kit set up with Ansible (`voice_tier: all`, the default) already has everything. By hand, from the repository root:

```bash
./run.py --download-models mayan   # Python packages (mayan-audio extra) + both MMS models
```

That installs the `mayan-audio` extra of `backend/pyproject.toml` (CPU-only PyTorch, transformers, SciPy, LAME), downloads both checkpoints to `.cache/models/tts/mms/` and exports each to `model.onnx`, which the classroom voice engine uses ([Voice Feedback §5](../../docs/architecture/voice-feedback.md)). Then:

```bash
.cache/venv/bin/python pwa/tts-tests/generate_tts.py            # WAVs next to the script
.cache/venv/bin/python pwa/tts-tests/generate_tts.py --publish  # also the MP3s on /descargas/
```

It runs on the CPU, never touches the network (about 2 minutes on the Jetson for both languages) and stops with the setup command if a package or a model is missing. The text lives in [guide_clauses.py](guide_clauses.py), the synthesis and MP3 encoding in [synthesis.py](synthesis.py).

## Why the MMS Input Spelling Differs from Modern ALMG Orthography

Meta MMS TTS checkpoints were trained on Bible corpora that use **traditional SIL orthographies** rather than the modern standardized ALMG (*Academia de Lenguas Mayas de Guatemala*) alphabet. Passing modern ALMG text directly causes silent character drops and wrong velar/uvular consonants:

| Feature | Modern ALMG | `mms-tts-quc-dialect_central` (Kʼicheʼ) | `mms-tts-kek` (Qʼeqchiʼ) |
| --- | --- | --- | --- |
| Glottal stop | `'` / `ʼ` | `ꞌ` (U+A78C saltillo — ASCII `'` is dropped!) | `'` (ASCII U+0027 — `ꞌ`/`ʼ` are dropped!) |
| `/k/` | `k` | `c` (before a/o/u/C), `qu` (before e/i) | `c` (before a/o/u/C), `qu` (before e/i) |
| `/kʼ/` | `k'` | `cꞌ` (before a/o/u/C), `qꞌu` (before e/i) | `c'` (before a/o/u/C), `q'u` (before e/i) |
| `/q/`, `/qʼ/` | `q`, `q'` | `k`, `kꞌ` | `k`, `k'` |
| `/ɓ/` | `b'` | `b` | `b` |
| `/w/` | `w` | `w` | `cu` (before vowels), `u` (syllable-final; `w` is dropped!) |
| Long vowels | `aa, ee, ii, oo, uu` | — (uses `ä` for lax `/ə/`) | `a̱, e̱, i̱, o̱, u̱` (U+0331 macron below) |
| Acronyms & punctuation | `APK`, `,`, `.` | Spelled out (`a pe ca`); pauses added between clauses | Spelled out (`a pe ca`); pauses added between clauses |

## Parallel Script

### Intro
- **English:** This is what you do to install an application on your cell phone with an APK file.
- **Spanish:** Esto es lo que haces para instalar una aplicación en tu celular con un archivo APK.
- **Kʼicheʼ (ALMG):** Are wa' ri kab'an che ub'anik instalar jun aplicación pa ri a celular ruk' jun archivo APK.
- **Kʼicheʼ (MMS):** `are waꞌ ri caban che ubanic instalar jun aplicación pa ri a celular rucꞌ jun archivo a pe ca`
- **Qʼeqchiʼ (ALMG):** A'in chanru taab'aanu instalar jun aplicación sa' laa celular rik'in jun archivo APK.
- **Qʼeqchiʼ (MMS):** `a'in chanru ta̱ba̱nu instalar jun aplicación sa' la̱ celular riq'uin jun archivo a pe ca`

### Step 1 — Locate the APK File
- **English:** First, open the Files or Downloads folder on your cell phone, and look for the APK file.
- **Spanish:** Primero, abre la carpeta de Archivos o Descargas en tu celular, y busca el archivo APK.
- **Kʼicheʼ (ALMG):** Nab'e, chajaqa' ri k'olib'al Archivos o Descargas pa ri a celular, xuquje' chatzukuj ri archivo APK.
- **Kʼicheʼ (MMS):** `nabe — chajakaꞌ ri cꞌolibal archivos o descargas pa ri a celular` / `xukujeꞌ chatzucuj ri archivo a pe ca`
- **Qʼeqchiʼ (ALMG):** Xb'een, te li carpeta Archivos malaj Descargas sa' laa celular, ut sik' li archivo APK.
- **Qʼeqchiʼ (MMS):** `xbe̱n — te li carpeta archivos malaj descargas sa' la̱ celular` / `ut sic' li archivo a pe ca`

### Step 2 — Tap the APK File
- **English:** Second, tap on the APK file so the installation begins.
- **Spanish:** Segundo, presiona sobre el archivo APK para que empiece la instalación.
- **Kʼicheʼ (ALMG):** Ukab', chapitz'a' pa uwi' ri archivo APK rech kämajix ri instalación.
- **Kʼicheʼ (MMS):** `ucab — chapitzꞌaꞌ pa uwiꞌ ri archivo a pe ca rech cämajix ri instalación`
- **Qʼeqchiʼ (ALMG):** Xkab', pitz' sa' xb'een li archivo APK re naq taatiklaaq li instalación.
- **Qʼeqchiʼ (MMS):** `xcab — pitz' sa' xbe̱n li archivo a pe ca re nak ta̱ticla̱k li instalación`

### Step 3 — Allow Unknown Sources (If Prompted)
- **English:** Third, if a message appears asking for permission, enter Settings and allow installing applications.
- **Spanish:** Tercero, si aparece un mensaje pidiendo permiso, entra a Configuración y da permiso para instalar aplicaciones.
- **Kʼicheʼ (ALMG):** Urox, we käk'utun jun tzij ri kuta' permiso chawe, chatok pa Configuración xuquje' chaya' q'ij rech kub'an instalar aplicaciones.
- **Kʼicheʼ (MMS):** `urox — we cäcꞌutun jun tzij ri cutaꞌ permiso chawe` / `chatoc pa configuración xukujeꞌ chayaꞌ kꞌij rech cuban instalar aplicaciones`
- **Qʼeqchiʼ (ALMG):** Rox, wi naxpatz' permiso aawe, okan sa' Configuración ut k'e permiso re xb'aanunkil instalar aplicaciones.
- **Qʼeqchiʼ (MMS):** `rox — cui naxpatz' permiso a̱cue` / `ocan sa' configuración ut q'ue permiso re xba̱nunquil instalar aplicaciones`

### Step 4 — Install & Wait
- **English:** Fourth, go back, tap the Install button, and wait a little until it finishes.
- **Spanish:** Cuarto, regresa, presiona el botón Instalar, y espera un poco hasta que termine.
- **Kʼicheʼ (ALMG):** Ukaj, chattzelej loq, chapitz'a' ri botón Instalar, xuquje' chaweyej jub'iq' k'a käk'isik.
- **Kʼicheʼ (MMS):** `ucaj — chattzelej lok — chapitzꞌaꞌ ri botón instalar` / `xukujeꞌ chaweyej jubikꞌ cꞌa cäqꞌuisic`
- **Qʼeqchiʼ (ALMG):** Xkaa, sutq'in chaq, pitz' li botón Instalar, ut oyb'eni b'ayaq toj reetal taaraqe'q.
- **Qʼeqchiʼ (MMS):** `xca̱ — sutk'in chak — pitz' li botón instalar` / `ut oybeni bayak toj re̱tal ta̱rake'k`

### Step 5 — Open & Use the App
- **English:** Fifth, when it finishes, tap the Open button. Now you can use the application.
- **Spanish:** Quinto, cuando termine, presiona el botón Abrir. Ahora ya puedes usar la aplicación.
- **Kʼicheʼ (ALMG):** Uro', are taq käk'isik, chapitz'a' ri botón Abrir. Kamik katkuinik kakoj ri aplicación.
- **Kʼicheʼ (MMS):** `uroꞌ — are tak cäqꞌuisic — chapitzꞌaꞌ ri botón abrir` / `cämic catcuinic cacoj ri aplicación`
- **Qʼeqchiʼ (ALMG):** Ro', naq taaraqe'q, pitz' li botón Abrir. Anaqwan naru taawoksi laa aplicación.
- **Qʼeqchiʼ (MMS):** `ro' — nak ta̱rake'k — pitz' li botón abrir` / `anakcuan naru ta̱cuocsi la̱ aplicación`

> **Review Note:** Before shipping audio to end users, have a native Kʼicheʼ speaker and a native Qʼeqchiʼ speaker listen to the generated WAV files to validate naturalness, local dialect phrasing, and pronunciation of Spanish UI loanwords (*Archivos*, *Descargas*, *Configuración*, *Instalar*, *Abrir*).
