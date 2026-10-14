#!/usr/bin/env python3
"""Prepara los archivos de versiones de la Biblia que Lámpara descarga.

Baja cada versión libre desde su fuente (fijada en un commit), la limpia, la pasa al
formato que entiende ConvertidorBiblia ({"books":[{"name","chapters":[{"chapter",
"verses":[{"verse","text"}]}]}]}) y la revisa contra la versificación de las Biblias en
inglés y español (eng.vrs) antes de escribirla. Nunca cambia palabras del texto: solo quita
marcas de formato (notas al pie, referencias cruzadas, títulos de sección).

Uso:  python3 preparar_biblias.py CARPETA_SALIDA
Deja CARPETA_SALIDA/<idioma>/<id>.json y CARPETA_SALIDA/informe.json (huellas y controles).
"""
import concurrent.futures as cf
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

RAW = "https://raw.githubusercontent.com/"
SCROLLMAPPER = RAW + "scrollmapper/bible_databases/e1b254cef86d0e65b1a5d1a94b8b112d0f296a2c/sources/"
WLDEH = RAW + "wldeh/bible-api/1d6987e268fcadb1e96ceb487e3d365a5e837f4a/bibles/"
SPABLM = RAW + "kahunapule/spablm/a741e2b6de48f8c08bab9e003bc4ae8f291bf99f/"
SPAVBL = RAW + "yojananyosef/spavbl_app/22e7781073a232e99f175e3eb0e044101aeb0f7f/public/bible/"
OSO = RAW + "palabra-de-dios/Biblia-del-Oso-1569/134b5090342cc332d61a04c101bb94cb930555ad/"
ENG_VRS = RAW + "BibleNLP/ebible/c531ff2da02843ded6d09afbe29a197ab844981f/metadata/eng.vrs"

# Orden de BookCatalog (Lámpara) y nombres en inglés que espera ConvertidorBiblia.
CODIGOS = ("GEN EXO LEV NUM DEU JOS JDG RUT 1SA 2SA 1KI 2KI 1CH 2CH EZR NEH EST JOB PSA PRO ECC SNG "
           "ISA JER LAM EZK DAN HOS JOL AMO OBA JON MIC NAM HAB ZEP HAG ZEC MAL MAT MRK LUK JHN ACT ROM "
           "1CO 2CO GAL EPH PHP COL 1TH 2TH 1TI 2TI TIT PHM HEB JAS 1PE 2PE 1JN 2JN 3JN JUD REV").split()
NOMBRES = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth",
    "I Samuel", "II Samuel", "I Kings", "II Kings", "I Chronicles", "II Chronicles", "Ezra",
    "Nehemiah", "Esther", "Job", "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon", "Isaiah",
    "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos", "Obadiah", "Jonah",
    "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi", "Matthew", "Mark",
    "Luke", "John", "Acts", "Romans", "I Corinthians", "II Corinthians", "Galatians", "Ephesians",
    "Philippians", "Colossians", "I Thessalonians", "II Thessalonians", "I Timothy", "II Timothy",
    "Titus", "Philemon", "Hebrews", "James", "I Peter", "II Peter", "I John", "II John", "III John",
    "Jude", "Revelation of John",
]
NOMBRE = dict(zip(CODIGOS, NOMBRES))
CODIGO_POR_NOMBRE = dict(zip(NOMBRES, CODIGOS))

# Carpetas de libros en wldeh/bible-api (nombres en español; cambian un poco por versión).
WLDEH_LIBROS = {
    "GEN": ["génesis"], "EXO": ["éxodo"], "LEV": ["levítico"], "NUM": ["números"], "DEU": ["deuteronomio"],
    "JOS": ["josué"], "JDG": ["jueces"], "RUT": ["rut"], "1SA": ["1samuel"], "2SA": ["2samuel"],
    "1KI": ["1reyes"], "2KI": ["2reyes"], "1CH": ["1crónicas"], "2CH": ["2crónicas"], "EZR": ["esdras"],
    "NEH": ["nehemías"], "EST": ["ester"], "JOB": ["job"], "PSA": ["salmos"], "PRO": ["proverbios"],
    "ECC": ["eclesiastés"], "SNG": ["cantares", "cantardeloscantares"], "ISA": ["isaías"],
    "JER": ["jeremías"], "LAM": ["lamentaciones"], "EZK": ["ezequiel"], "DAN": ["daniel"],
    "HOS": ["oseas"], "JOL": ["joel"], "AMO": ["amós"], "OBA": ["abdías"], "JON": ["jonás"],
    "MIC": ["miqueas"], "NAM": ["nahum", "nahúm"], "HAB": ["habacuc"], "ZEP": ["sofonías"],
    "HAG": ["hageo", "ageo"], "ZEC": ["zacarías"], "MAL": ["malaquías"], "MAT": ["mateo"],
    "MRK": ["marcos"], "LUK": ["lucas"], "JHN": ["juan"], "ACT": ["hechos"], "ROM": ["romanos"],
    "1CO": ["1corintios"], "2CO": ["2corintios"], "GAL": ["gálatas"], "EPH": ["efesios"],
    "PHP": ["filipenses"], "COL": ["colosenses"], "1TH": ["1tesalonicenses"], "2TH": ["2tesalonicenses"],
    "1TI": ["1timoteo"], "2TI": ["2timoteo"], "TIT": ["tito"], "PHM": ["filemón"], "HEB": ["hebreos"],
    "JAS": ["santiago"], "1PE": ["1pedro"], "2PE": ["2pedro"], "1JN": ["1juan"], "2JN": ["2juan"],
    "3JN": ["3juan"], "JUD": ["judas"], "REV": ["apocalipsis"],
}
# Carpetas de libros en kahunapule/spablm (nombres en inglés).
SPABLM_LIBROS = dict(zip(CODIGOS, [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth", "1 Samuel",
    "2 Samuel", "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Esther", "Job",
    "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah", "Lamentations", "Ezekiel",
    "Daniel", "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah",
    "Haggai", "Zechariah", "Malachi", "Matthew", "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians",
    "2 Corinthians", "Galatians", "Ephesians", "Philippians", "Colossians", "1 Thessalonians",
    "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews", "James", "1 Peter",
    "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation",
]))
OSO_ARCHIVO = {c: f"{n:02d}-{c}BO1569.usfm" for c, n in zip(CODIGOS, list(range(2, 41)) + list(range(70, 97)))}

# ---------------------------------------------------------------------------------------------
# Red

def bajar(url, intentos=4):
    for i in range(intentos):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(1.5 * (i + 1))
        except Exception:
            time.sleep(1.5 * (i + 1))
    raise RuntimeError("No se pudo bajar " + url)


def url(base, ruta):
    return base + urllib.parse.quote(ruta)

# ---------------------------------------------------------------------------------------------
# Versificación de referencia (eng.vrs: la que usan la RV 1909 y las Biblias en inglés)

def versificacion():
    texto = bajar(ENG_VRS).decode("utf-8")
    capitulos = {}
    for linea in texto.splitlines():
        partes = linea.split("#")[0].split()
        if not partes or partes[0] not in NOMBRE or "=" in linea:
            continue
        capitulos[partes[0]] = [int(x.split(":")[1]) for x in partes[1:]]
    return capitulos

# ---------------------------------------------------------------------------------------------
# Limpieza (solo marcas; el texto no se toca)

def espacios(t):
    return " ".join(t.split())


def limpiar_usfm(t):
    t = re.sub(r"\\(f|fe|x|ef|ex)\s.*?\\\1\*", " ", t, flags=re.S)           # notas y referencias
    t = re.sub(r"\\\+?w\s+([^|\\]*?)(\|[^\\]*)?\\\+?w\*", r"\1", t)            # \w palabra|strong\w*
    t = re.sub(r"\\fig\s.*?\\fig\*", " ", t, flags=re.S)
    t = re.sub(r"\\\+?[a-z]+[0-9]*\*", "", t)                                    # cierres \add* \nd*
    t = re.sub(r"\\\+?[a-z]+[0-9]*\s?", " ", t)                                  # aperturas \add \q1
    t = t.replace("¶", " ")
    return espacios(t)


def limpiar_json(t):
    t = re.sub(r"<[^>]+>", " ", t)            # etiquetas HTML sueltas
    t = t.replace("¶", " ")
    return espacios(t)

# ---------------------------------------------------------------------------------------------
# Lectores por fuente. Cada uno devuelve {codigo: {capitulo: {versiculo: texto}}}

def leer_scrollmapper(ruta):
    datos = json.loads(bajar(SCROLLMAPPER + ruta))
    biblia = {}
    for libro in datos["books"]:
        c = CODIGO_POR_NOMBRE.get(libro["name"])
        if not c:
            continue
        for cap in libro["chapters"]:
            for v in cap["verses"]:
                texto = limpiar_json(v["text"])
                if texto:
                    biblia.setdefault(c, {}).setdefault(int(cap["chapter"]), {}).setdefault(int(v["verse"]), texto)
    return biblia


def leer_usfm(texto, biblia, codigo):
    """Lee USFM; el título de un salmo (\\d) se une al versículo 1, como en la RV 1909."""
    texto = re.sub(r"\\(f|fe|x|ef|ex)\s.*?\\\1\*", " ", texto, flags=re.S)
    # Encabezados y títulos de sección ocupan su línea completa: no son texto bíblico.
    texto = re.sub(r"(?m)^\\(id|ide|h|toc\d|mt\d?|ms\d?|mr|s\d?|r|sp|rem|is\d?|ip|imt\d?|io\d?|iot|cl|sr|sd\d?|usfm|sts)\b.*$", " ", texto)
    capitulo, verso, titulo, actual = None, None, "", []

    def cerrar():
        if capitulo and verso:
            t = limpiar_usfm(" ".join(actual))
            if t:
                biblia.setdefault(codigo, {}).setdefault(capitulo, {})[verso] = t

    partes = re.split(r"(\\c\s+\d+|\\v\s+\d+(?:-\d+)?|\\d\b)", texto)
    for parte in partes:
        m = re.match(r"\\(c|v)\s+(\d+)", parte)
        if m and m.group(1) == "c":
            cerrar(); verso = None; actual = []; titulo = ""
            capitulo = int(m.group(2))
        elif m:
            cerrar(); verso = int(m.group(2)); actual = []
            if titulo:
                actual.append(titulo); titulo = ""
        elif parte == "\\d":
            actual = actual if verso else []
            if verso is None:
                titulo = "\0"  # marca: lo que sigue es el título
        else:
            if titulo == "\0":
                titulo = limpiar_usfm(parte)
            elif verso is not None:
                actual.append(parte)
    cerrar()


def leer_spablm():
    biblia = {}
    trabajos = []
    vrs = VRS
    for c in CODIGOS:
        for cap in range(1, len(vrs[c]) + 2):
            trabajos.append((c, cap, url(SPABLM, f"{SPABLM_LIBROS[c]}/{cap}/data")))
    with cf.ThreadPoolExecutor(16) as ex:
        for (c, cap, u), datos in zip(trabajos, ex.map(lambda t: bajar(t[2]), trabajos)):
            if datos:
                leer_usfm(datos.decode("utf-8"), biblia, c)
    return biblia


def leer_oso():
    biblia = {}
    for c in CODIGOS:
        datos = bajar(url(OSO, OSO_ARCHIVO[c]))
        if datos:
            leer_usfm(datos.decode("utf-8"), biblia, c)
    return biblia


def leer_wldeh(version):
    biblia = {}
    trabajos = []
    for c in CODIGOS:
        for nombre in WLDEH_LIBROS[c]:
            for cap in range(1, len(VRS[c]) + 2):
                trabajos.append((c, cap, url(WLDEH, f"{version}/books/{nombre}/chapters/{cap}.json")))
    with cf.ThreadPoolExecutor(16) as ex:
        for (c, cap, u), datos in zip(trabajos, ex.map(lambda t: bajar(t[2]), trabajos)):
            if not datos:
                continue
            for v in json.loads(datos)["data"]:
                m = re.match(r"\d+", str(v["verse"]))
                texto = limpiar_json(v["text"])
                if m and texto:
                    biblia.setdefault(c, {}).setdefault(int(v["chapter"]), {}).setdefault(int(m.group()), texto)
    return biblia

def leer_spavbl():
    """Versión Biblia Libre: un JSON por libro, con las notas al pie aparte (no se usan)."""
    biblia = {}
    for c in CODIGOS:
        datos = json.loads(bajar(SPAVBL + c + ".json"))
        for cap in datos["chapters"]:
            for v in cap["verses"]:
                texto = limpiar_json(v["text"])
                if texto:
                    biblia.setdefault(c, {}).setdefault(int(cap["chapter"]), {}).setdefault(int(v["number"]), texto)
    return biblia


def leer_kjv():
    """KJV edición Cambridge. La fuente trae 4 versículos vacíos (Jos 15:1, Job 7:1, Os 8:1,
    Ro 8:1): se completan con la KJV de 1769 del mismo repositorio, sin marcas de Strong."""
    biblia = leer_scrollmapper("en/KJVPCE/KJVPCE.json")
    respaldo = leer_scrollmapper("en/KJV/KJV.json")
    for c, caps in respaldo.items():
        for cap, versos in caps.items():
            for v, t in versos.items():
                if v not in biblia.get(c, {}).get(cap, {}) and re.fullmatch(r"[^<>{}\\]+", t):
                    biblia.setdefault(c, {}).setdefault(cap, {})[v] = t
    return biblia


def arreglar(biblia, regla):
    """Correcciones de marcas puntuales de una fuente (nunca cambia palabras)."""
    for caps in biblia.values():
        for versos in caps.values():
            for v, t in list(versos.items()):
                versos[v] = espacios(regla(t))
    return biblia


def darby_en(t):
    t = re.sub(r"([a-z])(God[a-z]*|Jehovah|Lord|LORD|Christ|Jesus|Spirit)\b", r"\1 \2", t)  # "AndGod"
    return t.replace("*", "")                                                   # marcas de nota


def asv(t):
    return re.sub(r"\[(Selah)(?![^\[]*\])", r"\1", t)                         # "[Selah" sin cierre


def blivre(t):
    return re.sub(r"/fn/.*?/\*fn", " ", t)                                       # nota filtrada


# ---------------------------------------------------------------------------------------------
# Catálogo de lo que se prepara

VERSIONES = [
    # id, idioma, lector
    ("rv1865", "es", lambda: leer_scrollmapper("es/SpaRV1865/SpaRV1865.json")),
    ("oso1569", "es", lambda: arreglar(leer_oso(), lambda t: t.lstrip("*"))),
    ("vbl", "es", leer_spavbl),
    ("blm", "es", leer_spablm),
    # "Palabra de Dios para ti" queda fuera: su fuente trae notas metidas en el texto y
    # pasajes cortados entre [[ ]] (por ejemplo Mateo 16:2-3).
    ("bes", "es", lambda: leer_wldeh("es-bes")),
    ("kjv", "en", leer_kjv),
    ("bsb", "en", lambda: leer_scrollmapper("en/BSB/BSB.json")),
    ("nheb", "en", lambda: leer_scrollmapper("en/NHEB/NHEB.json")),
    ("asv", "en", lambda: arreglar(leer_scrollmapper("en/ASV/ASV.json"), asv)),
    ("ylt", "en", lambda: leer_scrollmapper("en/YLT/YLT.json")),
    ("darby", "en", lambda: arreglar(leer_scrollmapper("en/Darby/Darby.json"), darby_en)),
    ("webster", "en", lambda: leer_scrollmapper("en/Webster/Webster.json")),
    ("bbe", "en", lambda: leer_scrollmapper("en/BBE/BBE.json")),
    ("geneva1599", "en", lambda: leer_scrollmapper("en/Geneva1599/Geneva1599.json")),
    ("blivre", "pt", lambda: arreglar(leer_scrollmapper("pt/PorBLivre/PorBLivre.json"), blivre)),
    ("darby-fr", "fr", lambda: arreglar(leer_scrollmapper("fr/FreJND/FreJND.json"), lambda t: t.replace("*", ""))),
    ("elb1905", "de", lambda: leer_scrollmapper("de/GerElb1905/GerElb1905.json")),
]

CLAVE = [("PSA", 23, 1), ("JHN", 3, 16), ("JOL", 2, 28), ("MAL", 4, 5), ("ROM", 8, 28), ("REV", 22, 21), ("GEN", 1, 1)]


def revisar(biblia):
    total = sum(len(v) for caps in biblia.values() for v in caps.values())
    faltan, sobran = [], []
    for c in CODIGOS:
        caps = biblia.get(c, {})
        for i, maximo in enumerate(VRS[c], start=1):
            tiene = caps.get(i, {})
            for v in range(1, maximo + 1):
                if v not in tiene:
                    faltan.append(f"{c} {i}:{v}")
        for cap, versos in caps.items():
            if cap > len(VRS[c]):
                sobran += [f"{c} {cap}:{v}" for v in versos]
            else:
                sobran += [f"{c} {cap}:{v}" for v in versos if v > VRS[c][cap - 1]]
    libros = [c for c in CODIGOS if biblia.get(c)]
    return {
        "versiculos": total,
        "libros": len(libros),
        "librosQueFaltan": [c for c in CODIGOS if not biblia.get(c)],
        "faltan": len(faltan), "faltanEjemplos": faltan[:12],
        "sobran": len(sobran), "sobranEjemplos": sobran[:12],
        "clave": {f"{b} {c}:{v}": biblia.get(b, {}).get(c, {}).get(v, "")[:90] for b, c, v in CLAVE},
    }


def escribir(biblia, destino):
    salida = {"books": [
        {"name": NOMBRE[c], "chapters": [
            {"chapter": cap, "verses": [{"verse": v, "text": t} for v, t in sorted(biblia[c][cap].items())]}
            for cap in sorted(biblia[c])]}
        for c in CODIGOS if biblia.get(c)]}
    datos = json.dumps(salida, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "wb") as f:
        f.write(datos)
    return hashlib.sha256(datos).hexdigest(), len(datos)


if __name__ == "__main__":
    salida = sys.argv[1] if len(sys.argv) > 1 else "biblias"
    solo = set(sys.argv[2:])
    VRS = versificacion()
    informe = {}
    ruta_informe = os.path.join(salida, "informe.json")
    if os.path.exists(ruta_informe):
        informe = json.load(open(ruta_informe))
    for vid, idioma, lector in VERSIONES:
        if solo and vid not in solo:
            continue
        inicio = time.time()
        biblia = lector()
        control = revisar(biblia)
        sha, tam = escribir(biblia, os.path.join(salida, idioma, vid + ".json"))
        control.update({"idioma": idioma, "ruta": f"{idioma}/{vid}.json", "sha256": sha, "bytes": tam})
        informe[vid] = control
        print(f"{vid:11} {control['versiculos']:6} versículos  libros {control['libros']}  faltan {control['faltan']:4}  sobran {control['sobran']:4}  {tam/1e6:5.1f} MB  {time.time()-inicio:5.1f}s", flush=True)
        json.dump(informe, open(ruta_informe, "w"), ensure_ascii=False, indent=1)
