#!/usr/bin/env python3
"""Genera paginas/*.html y js/search-index.js a partir de src/.
Uso:  pip install beautifulsoup4   (una sola vez)
      python3 build.py
Edita los datos de contacto en CONFIG y el contenido en src/pages/."""
import html, json, re, unicodedata
from pathlib import Path
from bs4 import BeautifulSoup
try:
    from PIL import Image
except ImportError:
    Image = None

ROOT = Path(__file__).parent
CONFIG = {  # Cambia aquí y se actualiza en todas las páginas. VERIFICAR con la entidad.
    'ENTIDAD': 'Municipalidad Distrital del Tigre',   # nombre oficial (confirmar)
    'ENTIDAD_CORTO': 'Muni del Tigre',

    'FACEBOOK_URL': '',
    'WHATSAPP': '51916235468',
    'PHONE': '',
    'EMAIL': '',
    'ADDRESS': 'Por confirmar con la entidad',
    'HORARIO': 'Por confirmar',
    'PHONE_TEL': '',   # mismo teléfono en formato para enlace tel:
    # Mapa (ubicación aproximada de Intuto; ajustar al punto exacto de la sede)
    'MAP_LAT': '-3.49010', 'MAP_LON': '-74.78112',
    'MAP_BBOX': '-74.81112%2C-3.51010%2C-74.75112%2C-3.47010',
    # Dirección pública del sitio, ej. 'https://www.muni-intuto.gob.pe'. Si queda vacío no se genera sitemap.xml.
    'SITE_URL': '',
}
PAGES = [  # (archivo, título, icono, descripción, palabras clave para el buscador)
    ('index.html', 'Inicio', 'bi-house-door', 'Portada, accesos rápidos e información general', 'municipalidad distrito tigre intuto rio tigre loreto inicio bienvenida portada'),
    ('institucion.html', 'Institución', 'bi-building', 'Misión, visión, organización e información institucional', 'institucion resena historica historia 1943 distrito tigre mision vision autoridades organigrama territorio simbolos escudo bandera petroleo kichwa'),
    ('tramites.html', 'Trámites', 'bi-file-earmark-text', 'Requisitos, solicitudes y procedimientos', 'tramites documentos requisitos registro civil solicitudes mesa de partes constancias'),
    ('mesa-partes.html', 'Mesa de partes virtual', 'bi-inbox', 'Prototipo de registro y seguimiento demostrativo de solicitudes', 'mesa partes virtual expediente seguimiento solicitud registro ciudadano demo'),
    ('servicios-municipales.html', 'Servicios municipales', 'bi-people', 'Servicios y orientación para la comunidad', 'servicios municipales comunidad obras atencion desarrollo social'),
    ('transparencia.html', 'Transparencia', 'bi-shield-check', 'Documentos públicos, presupuesto y directorio', 'transparencia presupuesto documentos resoluciones acuerdos directorio funcionarios datos publicos'),
    ('agenda.html', 'Agenda', 'bi-calendar-event', 'Avisos, eventos y noticias municipales', 'agenda actividades eventos calendario fechas avisos noticias alerta'),
    ('turismo.html', 'Turismo', 'bi-compass', 'Naturaleza, cultura y atractivos del río Tigre', 'turismo cultura naturaleza atractivos rio tigre artesania historia'),
    ('noticias.html', 'Noticias', 'bi-newspaper', 'Archivo de noticias municipales con fecha', 'noticias notas de prensa actualidad novedades archivo fecha'),
    ('obras.html', 'Obras', 'bi-cone-striped', 'Estado y avance de las obras municipales', 'obras proyectos avance construccion inversion en proceso culminada embarcadero aulas'),
    ('documentos.html', 'Documentos de gestión', 'bi-folder2-open', 'Ordenanzas, acuerdos, decretos y resoluciones con filtros', 'documentos gestion ordenanzas acuerdos decretos resoluciones filtros pdf normas'),
    ('visitas.html', 'Visitas en línea', 'bi-camera-video', 'Solicitar una cita o visita', 'visitas cita citas reunion alcalde atencion en linea'),
    ('privacidad.html', 'Política de privacidad', 'bi-lock', 'Cómo trata este sitio los datos y preferencias', 'privacidad datos personales cookies preferencias'),
    ('reclamaciones.html', 'Libro de reclamaciones', 'bi-journal-text', 'Cómo presentar un reclamo o sugerencia', 'reclamaciones reclamos quejas sugerencias libro'),
]

def read(p): return Path(p).read_text(encoding='utf-8')
def parse(text):
    m = re.match(r'---\n(.*?)\n---\n(.*)', text, re.S)
    meta = dict(l.split(': ', 1) if ': ' in l else (l.rstrip(':'), '') for l in m.group(1).splitlines())
    return meta, m.group(2)
def render(tpl, vars_):
    tpl = re.sub(r'\{\{> ([\w-]+)\}\}', lambda m: read(ROOT / 'src/partials' / (vars_.get(m.group(1).replace('-block', ''), m.group(1)) + '.html')).rstrip(), tpl)
    return re.sub(r'\{\{(\w+)\}\}', lambda m: vars_.get(m.group(1), m.group(0)), tpl)
def slug(t):
    t = unicodedata.normalize('NFD', t).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')[:64].rstrip('-') or 'seccion'
def clean(t): return ' '.join(t.split())


# ---------------------------------------------------------------------------
# Páginas generadas desde src/data/*.json (noticias, obras, documentos, galerías)
# ---------------------------------------------------------------------------
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
def e(s): return html.escape(str(s), quote=True)
def fecha(iso): y, m, d = iso.split('-'); return f'{int(d)} de {MESES[int(m) - 1]} de {y}'
def soles(n): return f'S/ {n:,.0f}'
def norm(s): return unicodedata.normalize('NFD', str(s).lower()).encode('ascii', 'ignore').decode()
def load(name): return json.loads(read(ROOT / 'src/data' / f'{name}.json'))
def existe(f): return (ROOT / 'imagenes' / f).exists()
_dims = {}
def dims(f):
    if not Image or not existe(f): return ''
    if f not in _dims:
        with Image.open(ROOT / 'imagenes' / f) as im: _dims[f] = im.size
    return f' width="{_dims[f][0]}" height="{_dims[f][1]}"'
def foto(f, alt, focus='center'):
    return f'<img src="../imagenes/{f}" alt="{e(alt)}" loading="lazy"{dims(f)} style="object-position:{e(focus)}">'
STATUS_CLASS = {'En proceso': 'proceso', 'Culminada': 'culminada', 'Por iniciar': 'pendiente'}
MODAL_FOTO = ('<div class="modal fade" id="modalPostal" tabindex="-1" aria-labelledby="modalPostalLabel" aria-hidden="true"><div class="modal-dialog modal-dialog-centered modal-lg"><div class="modal-content">'
              '<div class="modal-header"><h5 class="modal-title" id="modalPostalLabel"></h5><button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button></div>'
              '<div class="modal-body text-center"><img class="img-fluid rounded" src="" alt=""></div></div></div></div>')

def filter_group(key, label, values, todos='Todos'):
    btns = [f'<button type="button" class="btn btn-outline-success btn-sm filter-btn active" data-filter-key="{key}" data-filter-value="" aria-pressed="true">{todos}</button>']
    btns += [f'<button type="button" class="btn btn-outline-success btn-sm filter-btn" data-filter-key="{key}" data-filter-value="{e(v)}" aria-pressed="false">{e(v)}</button>' for v in values]
    return f'<div class="filter-bar" role="group" aria-label="{label}">' + ''.join(btns) + '</div>'

def photo_card(href, fotos, titulo, acento, texto, extra='', boton='Ver detalles'):
    """Tarjeta con foto arriba, título, dato destacado, descripción y botón (como en un catálogo)."""
    img = f'<a class="photo-card-img" href="{href}" tabindex="-1" aria-hidden="true">{foto(fotos[0], titulo)}</a>' if fotos and existe(fotos[0]) else ''
    return (f'<article class="card photo-card h-100">{img}<div class="card-body d-flex flex-column"><h3 class="h5">{e(titulo)}</h3>{acento}{extra}'
            f'<p class="text-muted flex-grow-1">{e(texto)}</p><div><a class="btn btn-dark btn-sm" href="{href}">{boton}<span class="visually-hidden">: {e(titulo)}</span></a></div></div></article>')

def noticia_card(n):
    acento = (f'<p class="photo-card-accent mb-1"><time datetime="{n["date"]}"><i class="bi bi-calendar3" aria-hidden="true"></i> {fecha(n["date"])}</time></p>'
              f'<p class="mb-2"><span class="news-tag"><i class="bi {n["icon"]}" aria-hidden="true"></i> {e(n["category"])}</span></p>')
    return photo_card(f'noticia-{n["slug"]}.html', n.get('fotos', []), n['title'], acento, n['summary'])

def obra_slug(o): return o.get('slug') or slug(o['title'])
def obra_card(o):
    p = o['progress']
    acento = (f'<p class="mb-1"><span class="status-pill status-{STATUS_CLASS[o["status"]]}">{e(o["status"])}</span></p>'
              f'<p class="photo-card-accent mb-2">{soles(o["budget"])}</p>')
    barra = (f'<div class="progress mb-1" role="progressbar" aria-label="Avance de la obra: {e(o["title"])}" aria-valuenow="{p}" aria-valuemin="0" aria-valuemax="100"><div class="progress-bar" style="width:{p}%"></div></div>'
             f'<p class="small mb-2">Avance {p}%</p>')
    return photo_card(f'obra-{obra_slug(o)}.html', o.get('fotos', []), o['title'], acento, o['description'], barra)

def gallery(items, titulo, id_):
    """Colección de fotos de un apartado: miniaturas que se amplían al pulsar."""
    cards = []
    for g in items:
        if not existe(g['file']): print('AVISO: falta la foto', g['file']); continue
        cards.append(f'<div class="col-6 col-md-4 col-lg-3"><figure class="postal"><button type="button" class="postal-btn" data-bs-toggle="modal" data-bs-target="#modalPostal" '
                     f'data-img="../imagenes/{g["file"]}" data-title="{e(g["title"])}" data-alt="{e(g["alt"])}" aria-label="Ampliar la foto: {e(g["title"])}">'
                     f'{foto(g["file"], g["alt"], g.get("focus", "center"))}</button><figcaption>{e(g["title"])}</figcaption></figure></div>')
    if not cards: return ''
    return (f'<section id="{id_}" class="mt-4 p-3 bg-light rounded galeria"><h3 class="h5 text-center mb-3"><i class="bi bi-images" aria-hidden="true"></i> {titulo}</h3>'
            f'<div class="row g-3 justify-content-center">{"".join(cards)}</div></section>' + MODAL_FOTO)

def generated_pages():
    noticias = sorted(load('noticias'), key=lambda n: n['date'], reverse=True)
    obras = load('obras')
    docs = sorted(load('documentos'), key=lambda d: d['date'], reverse=True)
    def seccion(id_, icono, titulo, tarjetas, enlace, texto_enlace):
        if not tarjetas: return ''   # sin datos: la sección no aparece en la portada
        return (f'<section id="{id_}" class="mt-5"><h2 class="section-title"><i class="bi {icono}"></i> {titulo}</h2><div class="row g-4">{tarjetas}</div>'
                f'<div class="text-center mt-3"><a class="btn btn-outline-success" href="{enlace}">{texto_enlace}</a></div></section>')
    EXTRA['NOTICIAS_SECTION'] = seccion('noticias', 'bi-newspaper', 'Noticias', ''.join(f'<div class="col-md-6">{noticia_card(n)}</div>' for n in noticias[:2]), 'noticias.html', 'Ver archivo de noticias')
    EXTRA['OBRAS_SECTION'] = seccion('obras', 'bi-cone-striped', 'Obras destacadas', ''.join(f'<div class="col-md-4">{obra_card(o)}</div>' for o in [o for o in obras if o['status'] == 'En proceso'][:3]), 'obras.html', 'Ver todas las obras')
    gal = load('galeria')   # una colección de fotos por apartado
    for sec, titulo in [('turismo', 'Postales de Intuto'), ('institucion', 'Galería institucional'), ('servicios', 'Servicios en imágenes'), ('agenda', 'Galería de actividades')]:
        EXTRA['GALERIA_' + sec.upper()] = gallery(gal.get(sec, []), titulo, 'galeria-' + sec)
    sub = lambda title, desc, hero: {'title': f'{title} | {{{{ENTIDAD}}}}', 'description': desc, 'body_class': 'sub-page', 'hero': 'hero-sub', 'carousel': 'none', 'hero_title': hero}
    out = []
    # --- Noticias: archivo + una página por noticia (con su colección de fotos)
    cats = sorted({n['category'] for n in noticias})
    items = ''.join(f'<div class="col-md-6 col-lg-4" data-filter-item data-category="{e(n["category"])}" data-text="{e(norm(n["title"] + " " + n["summary"]))}">{noticia_card(n)}</div>' for n in noticias)
    out.append(('noticias.html', sub('Noticias', 'Archivo de noticias de la municipalidad, ordenadas por fecha.', 'Noticias'),
        '<div data-filter-root>' + filter_group('category', 'Filtrar por categoría', cats) +
        '<p class="small text-muted mt-2" data-filter-count role="status" aria-live="polite"></p><div class="row g-4">' + items + '</div>'
        '<p class="alert alert-secondary d-none mt-3" data-filter-empty>No hay noticias en esta categoría.</p></div>'))
    for n in noticias:
        paras = ''.join(f'<p>{e(p)}</p>' for p in n['body'])
        fotos = gallery([{'file': f, 'title': f'{n["title"]} ({k})', 'alt': f'{n["title"]}, foto {k}'} for k, f in enumerate(n.get('fotos', []), 1)], 'Fotos de la noticia', 'fotos')
        out.append((f'noticia-{n["slug"]}.html', sub(n['title'], n['summary'], 'Noticias'),
            f'<article class="card page-card p-4"><div class="d-flex flex-wrap gap-2 align-items-center mb-2"><span class="news-tag"><i class="bi {n["icon"]}" aria-hidden="true"></i> {e(n["category"])}</span></div>'
            f'<h2 class="card-heading">{e(n["title"])}</h2><p class="meta-line"><i class="bi bi-calendar3" aria-hidden="true"></i> <time datetime="{n["date"]}">{fecha(n["date"])}</time></p>'
            f'{paras}{fotos}<div class="mt-3"><a class="btn btn-outline-success" href="noticias.html"><i class="bi bi-arrow-left" aria-hidden="true"></i> Volver a noticias</a></div></article>'))
    # --- Obras: archivo + una página por obra (con su colección de fotos)
    estados = ['En proceso', 'Culminada', 'Por iniciar']
    cnt = {s: sum(o['status'] == s for o in obras) for s in estados}
    stats = ''.join(f'<div class="col-4"><div class="card stat-card text-center p-3"><strong class="fs-3">{v}</strong><span class="small">{k}</span></div></div>' for k, v in [('Total de obras', len(obras)), ('En proceso', cnt['En proceso']), ('Culminadas', cnt['Culminada'])])
    cards = ''.join(f'<div class="col-md-6 col-lg-4" data-filter-item data-status="{e(o["status"])}" data-text="{e(norm(o["title"] + " " + o["location"]))}">{obra_card(o)}</div>' for o in obras)
    out.append(('obras.html', sub('Obras', 'Estado y porcentaje de avance de las obras de la municipalidad.', 'Obras y proyectos'),
        f'<div class="row g-3 mb-4">{stats}</div><div data-filter-root>' + filter_group('status', 'Filtrar por estado', estados, 'Todas') +
        '<p class="small text-muted mt-2" data-filter-count role="status" aria-live="polite"></p><div class="row g-4">' + cards + '</div>'
        '<p class="alert alert-secondary d-none mt-3" data-filter-empty>No hay obras con ese estado.</p></div>'))
    for o in obras:
        p = o['progress']
        fotos = gallery([{'file': f, 'title': f'{o["title"]} ({k})', 'alt': f'{o["title"]}, foto {k}'} for k, f in enumerate(o.get('fotos', []), 1)], 'Fotos de la obra', 'fotos')
        out.append((f'obra-{obra_slug(o)}.html', sub(o['title'], o['description'], 'Obras y proyectos'),
            f'<article class="card page-card p-4"><p class="mb-2"><span class="status-pill status-{STATUS_CLASS[o["status"]]}">{e(o["status"])}</span></p><h2 class="card-heading">{e(o["title"])}</h2><p>{e(o["description"])}</p>'
            f'<ul class="list-unstyled contact-list"><li><i class="bi bi-geo-alt-fill" aria-hidden="true"></i> {e(o["location"])}</li><li><i class="bi bi-calendar3" aria-hidden="true"></i> Inicio: {fecha(o["start"])}</li><li><i class="bi bi-cash-coin" aria-hidden="true"></i> Inversión: {soles(o["budget"])}</li></ul>'
            f'<div class="progress mb-1" role="progressbar" aria-label="Avance de la obra" aria-valuenow="{p}" aria-valuemin="0" aria-valuemax="100"><div class="progress-bar" style="width:{p}%"></div></div><p class="small">Avance {p}%</p>'
            f'{fotos}<div class="mt-3"><a class="btn btn-outline-success" href="obras.html"><i class="bi bi-arrow-left" aria-hidden="true"></i> Volver a obras</a></div></article>'))
    # --- Documentos de gestión (lista con filtros)
    tipos = ['Acuerdos', 'Decretos', 'Ordenanzas', 'Resoluciones']
    anios = sorted({d['year'] for d in docs}, reverse=True)
    rows = ''.join(
        f'<li class="list-group-item doc-item" data-filter-item data-type="{e(d["type"])}" data-year="{d["year"]}" data-text="{e(norm(d["number"] + " " + d["title"]))}">'
        f'<i class="bi bi-file-earmark-pdf doc-icon" aria-hidden="true"></i><div class="flex-grow-1"><strong>{e(d["number"])}</strong>'
        f'<div class="small">{e(d["title"])}</div><div class="small text-muted"><time datetime="{d["date"]}">{fecha(d["date"])}</time> · {e(d["type"])}</div></div>'
        f'<span class="small text-muted text-nowrap">PDF pendiente</span></li>' for d in docs)
    controls = ('<div class="row g-2 align-items-end mb-2"><div class="col-md-6"><label class="form-label small mb-1" for="docBuscar">Buscar en los documentos</label>'
                '<input type="search" class="form-control" id="docBuscar" data-filter-key="q" placeholder="Ej.: presupuesto, embarcadero"></div>'
                '<div class="col-md-3"><label class="form-label small mb-1" for="docAnio">Año</label><select class="form-select" id="docAnio" data-filter-key="year"><option value="">Todos</option>' +
                ''.join(f'<option>{a}</option>' for a in anios) + '</select></div></div>')
    out.append(('documentos.html', sub('Documentos de gestión', 'Ordenanzas, acuerdos, decretos y resoluciones de la municipalidad, con filtros por tipo y año.', 'Documentos de gestión'),
        '<div data-filter-root>' + controls + filter_group('type', 'Filtrar por tipo de documento', tipos) +
        '<p class="small text-muted mt-2" data-filter-count role="status" aria-live="polite"></p><ul class="list-group">' + rows + '</ul>'
        '<p class="alert alert-secondary d-none mt-3" data-filter-empty>No se encontraron documentos con esos filtros.</p></div>'))
    def vacio(msg, icono): return f'<div class="card page-card p-4 text-center"><i class="bi {icono} fs-1 text-success" aria-hidden="true"></i><p class="mb-0 mt-2">{msg}</p></div>'
    vac = {'noticias.html': (noticias, vacio('Pronto publicaremos aquí las noticias de la municipalidad.', 'bi-newspaper')),
           'obras.html': (obras, vacio('Pronto publicaremos aquí el estado y el avance de las obras.', 'bi-cone-striped')),
           'documentos.html': (docs, vacio('Pronto publicaremos aquí las ordenanzas, acuerdos, decretos y resoluciones.', 'bi-folder2-open'))}
    return [(n, m, vac[n][1] if n in vac and not vac[n][0] else c) for n, m, c in out]

layout = read(ROOT / 'src/layout.html')
jsonld = {'@context': 'https://schema.org', '@type': 'GovernmentOrganization',
          'name': CONFIG['ENTIDAD'],
          'address': {'@type': 'PostalAddress', 'streetAddress': CONFIG['ADDRESS'], 'addressLocality': 'Intuto',
                      'addressRegion': 'Loreto', 'addressCountry': 'PE'}}
if CONFIG['PHONE']: jsonld['telephone'] = CONFIG['PHONE']
if CONFIG['EMAIL']: jsonld['email'] = CONFIG['EMAIL']
if CONFIG['FACEBOOK_URL']: jsonld['sameAs'] = [CONFIG['FACEBOOK_URL']]
if CONFIG['SITE_URL']: jsonld['url'] = CONFIG['SITE_URL']
CONFIG['JSONLD'] = json.dumps(jsonld, ensure_ascii=False)
(ROOT / 'paginas').mkdir(exist_ok=True)
titles = {f: t for f, t, *_ in PAGES}
sections = []
EXTRA = {}
entries = []
for src in sorted((ROOT / 'src/pages').glob('*.html')):
    meta, content = parse(read(src)); entries.append((src.name, meta, content))
entries += generated_pages()   # llena también EXTRA (noticias y obras de la portada)
built = []
for name, meta, content in entries:
    vars_ = {**CONFIG, **EXTRA, **meta, 'content': content}
    html = render(layout, vars_)
    html = render(html, vars_)  # segunda pasada: variables dentro de parciales
    soup = BeautifulSoup(html, 'html.parser')
    for img in soup.find_all('img'):   # rendimiento: tamaño intrínseco y carga diferida
        in_first = img.find_parent(class_='active') or img.find_parent(['nav', 'header']) or img.find_parent(class_=['hero', 'hero-small'])
        if not in_first and not img.get('loading'): img['loading'] = 'lazy'
        if Image and img.find_parent(class_='carousel-item') and not img.get('width'):
            try:
                with Image.open((ROOT / 'paginas' / img['src']).resolve()) as im: img['width'], img['height'] = im.size
            except OSError: pass
    main, used = soup.find('main'), set()
    for el in main.select('h2,h3,h4,h5,.alert,.list-group-item'):
        if el.name in ('h2', 'h3', 'h4', 'h5'):
            title = clean(el.get_text(' '))
            box = el.find_parent(class_='card') or el.find_parent('section') or el.parent
        else:
            title = clean(el.get_text(' '))[:70]; box = el
        if not title: continue
        sid = el.get('id') or 's-' + slug(title)
        base, n = sid, 2
        while sid in used: sid = f'{base}-{n}'; n += 1
        used.add(sid); el['id'] = sid
        sections.append({'page': name, 'pageTitle': titles.get(name, render(meta['title'], vars_)), 'id': sid,
                         'title': title[:80], 'text': clean(box.get_text(' '))[:500]})
    (ROOT / 'paginas' / name).write_text(str(soup), encoding='utf-8')
    built.append(name)
    print('OK', name)

# Limpieza: elimina páginas de paginas/ que ya no se generan (por ejemplo, noticias borradas de noticias.json)
for old in (ROOT / 'paginas').glob('*.html'):
    if old.name not in built: old.unlink(); print('Eliminada', old.name)

data = {'pages': [{'title': t, 'url': f, 'icon': i, 'desc': d, 'keywords': k} for f, t, i, d, k in PAGES], 'sections': sections}
(ROOT / 'js/search-index.js').write_text('window.INTUTO_SEARCH_INDEX=' + json.dumps(data, ensure_ascii=False) + ';', encoding='utf-8')
print(len(sections), 'entradas de búsqueda')

# robots.txt y sitemap.xml (el sitemap solo si se definió SITE_URL)
site = CONFIG['SITE_URL'].rstrip('/')
robots = 'User-agent: *\nAllow: /\n' + (f'Sitemap: {site}/sitemap.xml\n' if site else '')
(ROOT / 'robots.txt').write_text(robots, encoding='utf-8')
if site:
    urls = ''.join(f'  <url><loc>{site}/paginas/{f}</loc></url>\n' for f in built)
    (ROOT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + '</urlset>\n', encoding='utf-8')
    print('sitemap.xml generado')
