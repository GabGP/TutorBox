"""Clause-by-clause text of the APK install guide in Kʼicheʼ and Qʼeqchiʼ.

The spelling follows the SIL/Bible orthographies the Meta MMS checkpoints were
trained on, not modern ALMG: see instructions.md for the mapping. Each step is a
list of clauses; the generator pauses briefly between clauses and longer between
steps, because both tokenizers drop punctuation.
"""

KICHE_STEPS: list[list[str]] = [
    # Intro: This is what you do to install an application on your cell phone with an APK file.
    [
        "are waꞌ ri caban che ubanic instalar jun aplicación pa ri a celular rucꞌ jun archivo a pe ca",
    ],
    # Step 1: First, open the Files or Downloads folder on your cell phone, and look for the APK file.
    [
        "nabe — chajakaꞌ ri cꞌolibal archivos o descargas pa ri a celular",
        "xukujeꞌ chatzucuj ri archivo a pe ca",
    ],
    # Step 2: Second, tap on the APK file so the installation begins.
    [
        "ucab — chapitzꞌaꞌ pa uwiꞌ ri archivo a pe ca rech cämajix ri instalación",
    ],
    # Step 3: Third, if a message appears asking for permission, enter Settings and allow installing apps.
    [
        "urox — we cäcꞌutun jun tzij ri cutaꞌ permiso chawe",
        "chatoc pa configuración xukujeꞌ chayaꞌ kꞌij rech cuban instalar aplicaciones",
    ],
    # Step 4: Fourth, go back, tap the Install button, and wait a moment until it finishes.
    [
        "ucaj — chattzelej lok — chapitzꞌaꞌ ri botón instalar",
        "xukujeꞌ chaweyej jubikꞌ cꞌa cäqꞌuisic",
    ],
    # Step 5: Fifth, when it finishes, tap the Open button. Now you can use the application.
    [
        "uroꞌ — are tak cäqꞌuisic — chapitzꞌaꞌ ri botón abrir",
        "cämic catcuinic cacoj ri aplicación",
    ],
]

QEQCHI_STEPS: list[list[str]] = [
    # Intro: Here is how to install an application on your cell phone with an APK file.
    [
        "a'in chanru ta̱ba̱nu instalar jun aplicación sa' la̱ celular riq'uin jun archivo a pe ca",
    ],
    # Step 1: First, open the Files or Downloads folder on your cell phone, and look for the APK file.
    [
        "xbe̱n — te li carpeta archivos malaj descargas sa' la̱ celular",
        "ut sic' li archivo a pe ca",
    ],
    # Step 2: Second, tap on the APK file so the installation begins.
    [
        "xcab — pitz' sa' xbe̱n li archivo a pe ca re nak ta̱ticla̱k li instalación",
    ],
    # Step 3: Third, if it asks you for permission, enter Settings and give permission to install apps.
    [
        "rox — cui naxpatz' permiso a̱cue",
        "ocan sa' configuración ut q'ue permiso re xba̱nunquil instalar aplicaciones",
    ],
    # Step 4: Fourth, go back, tap the Install button, and wait a moment until it finishes.
    [
        "xca̱ — sutk'in chak — pitz' li botón instalar",
        "ut oybeni bayak toj re̱tal ta̱rake'k",
    ],
    # Step 5: Fifth, when it finishes, tap the Open button. Now you can use your application.
    [
        "ro' — nak ta̱rake'k — pitz' li botón abrir",
        "anakcuan naru ta̱cuocsi la̱ aplicación",
    ],
]
