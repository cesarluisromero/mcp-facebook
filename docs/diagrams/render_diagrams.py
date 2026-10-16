"""Generate the plan's editable Mermaid sources and standalone SVG diagrams.

Uses only Python's standard library. Run from any directory with Python 3.
"""

from html import escape
from pathlib import Path
import textwrap
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
INK = "#17324d"
MUTED = "#50677b"
BLUE = "#2463a2"
TEAL = "#14766d"
PARTS = []


def add(markup):
    PARTS.append(markup)


def label(x, y, value, size=16, anchor="middle", color=INK, weight="400"):
    lines = value.split("\n")
    add(f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{color}" '
        f'font-size="{size}" font-weight="{weight}">')
    for i, line in enumerate(lines):
        add(f'<tspan x="{x}" dy="{0 if i == 0 else size * 1.35}">{escape(line)}</tspan>')
    add('</text>')


def rect(x, y, w, h, fill="#ffffff", stroke="#cbd9e5", radius=12):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" '
        f'fill="{fill}" stroke="{stroke}"/>')


def line(x1, y1, x2, y2, color="#849aad", dashed=False, arrow=False):
    attrs = ' stroke-dasharray="6 5"' if dashed else ''
    attrs += ' marker-end="url(#arrow)"' if arrow else ''
    add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'stroke="{color}" stroke-width="1.6"{attrs}/>')


def actor(x, y, name):
    add(f'<circle cx="{x}" cy="{y}" r="13" fill="#ffffff" stroke="{INK}" stroke-width="2"/>')
    for a, b, c, d in [(x, y + 13, x, y + 51), (x - 24, y + 28, x + 24, y + 28),
                       (x, y + 51, x - 21, y + 77), (x, y + 51, x + 21, y + 77)]:
        line(a, b, c, d, INK)
    label(x, y + 101, name, 16, weight="600")


def save(name, title, width, height, body):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
           f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title">'
           f'<title id="title">{escape(title)}</title>'
           '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" '
           'orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#2463a2"/></marker></defs>'
           '<g font-family="Segoe UI, Arial, sans-serif">'
           f'<rect width="{width}" height="{height}" fill="#f8fafc"/>'
           + ''.join(body) + '</g></svg>')
    ET.fromstring(svg)
    (OUT / f'{name}.svg').write_text(svg, encoding='utf-8')


def use_cases(name, title, cases, actors, meta_ids):
    PARTS.clear()
    height = 220 + 108 * len(cases)
    label(550, 39, title, 25, weight="700")
    label(550, 67, "Asociaciones de actores con casos de uso; no indican orden de ejecución.", 15, color=MUTED)
    rect(250, 95, 600, height - 158, "#ffffff")
    label(550, 125, "MCP de Facebook en VPS · interfaz ChatGPT Work", 17, weight="600")
    ys = {case_id: 185 + i * 108 for i, (case_id, _) in enumerate(cases)}
    for aid, ay, aname, ids in actors:
        for cid in ids:
            line(135, ay + 30, 320, ys[cid])
    my = height / 2 - 45
    for cid in meta_ids:
        line(780, ys[cid], 965, my + 30)
    for cid, title_case in cases:
        cy = ys[cid]
        add(f'<ellipse cx="550" cy="{cy}" rx="230" ry="39" fill="#edf5fd" stroke="{BLUE}" stroke-width="1.6"/>')
        label(550, cy - 7, cid, 14, color=BLUE, weight="700")
        label(550, cy + 16, title_case, 17, weight="600")
    for aid, ay, aname, ids in actors:
        actor(110, ay, aname)
    actor(990, my, "Meta\nSistema externo")
    label(550, height - 25, "Acciones sujetas a los permisos, políticas y capacidades verificadas del plan.", 14, color=MUTED)
    save(name, title, 1100, height, PARTS)

    mmd = ["flowchart LR"]
    for aid, ay, aname, ids in actors:
        mmd.append(f'    {aid}["{aname.replace(chr(10), "<br/>")}"]')
    mmd.extend(['    META["Meta · sistema externo"]', '    subgraph MCP["MCP en VPS · interfaz ChatGPT Work"]'])
    for cid, title_case in cases:
        mmd.append(f'        {cid.replace("-", "_")}(["{cid} · {title_case}"])')
    mmd.append('    end')
    for aid, ay, aname, ids in actors:
        for cid in ids:
            mmd.append(f'    {aid} --- {cid.replace("-", "_")}')
    for cid in meta_ids:
        mmd.append(f'    {cid.replace("-", "_")} --- META')
    (OUT / f'{name}.mmd').write_text('\n'.join(mmd) + '\n', encoding='utf-8')


use_cases(
    "casos-acceso", "Casos de uso · conexión y control",
    [("CU-01", "Conectar cliente y activos"), ("CU-02", "Elegir cliente y consultar capacidades"),
     ("CU-11", "Consultar tareas, auditoría y fallos"), ("CU-12", "Desconectar cliente y revocar acceso")],
    [("ADMIN", 140, "Administrador", ["CU-01", "CU-12"]),
     ("CLIENTE", 285, "Representante\ndel cliente", ["CU-01"]),
     ("EQUIPO", 450, "Tú / equipo\nautorizado", ["CU-02", "CU-11"])],
    ["CU-01", "CU-02"],
)

use_cases(
    "casos-paginas", "Casos de uso · páginas y Messenger",
    [("CU-03", "Publicar texto o imagen"), ("CU-04", "Programar una publicación"),
     ("CU-05", "Consultar, editar o eliminar publicaciones"), ("CU-06", "Responder o moderar comentarios"),
     ("CU-07", "Consultar y responder mensajes")],
    [("OPERADOR", 315, "Tú / operador", ["CU-03", "CU-04", "CU-05", "CU-06", "CU-07"])],
    ["CU-03", "CU-04", "CU-05", "CU-06", "CU-07"],
)

use_cases(
    "casos-anuncios", "Casos de uso · publicidad e informes",
    [("CU-08", "Consultar métricas y resultados"), ("CU-09", "Crear campaña en pausa"),
     ("CU-10", "Cambiar estado o presupuesto")],
    [("ANALISTA", 145, "Analista", ["CU-08"]),
     ("OPERADOR", 325, "Operador / aprobador\nsegún política", ["CU-09", "CU-10"])],
    ["CU-08", "CU-09", "CU-10"],
)


# One event list produces both the rendered SVG and the editable Mermaid source.
participants = [
    ("U", "Tú", "Cuenta de ChatGPT"), ("W", "ChatGPT Work", "Interfaz y herramientas"),
    ("M", "Servidor MCP", "Permisos y lógica · VPS"), ("D", "Datos protegidos", "Operaciones y tokens · VPS"),
    ("F", "API de Meta", "Servicio externo"), ("P", "Página Facebook", "Destino de publicación"),
]
events = [
    ("note", "Conexión previa: Work autorizado ante el MCP y cliente vinculado a Meta mediante flujos separados."),
    ("msg", "U", "W", 'Publica ahora en la página de Cliente A: «Hoy abrimos a las 9».', False),
    ("msg", "W", "M", "list_assets / get_capabilities + token de acceso al MCP", False),
    ("msg", "M", "D", "Validar identidad, cliente, roles y activos asignados", False),
    ("msg", "D", "M", "Contexto y capacidades autorizadas", True),
    ("msg", "M", "W", "Página y acciones disponibles; si falta acceso, detener", True),
    ("start", "opt", "Solo si faltan datos o el destino es ambiguo"),
    ("msg", "W", "U", "Pedir precisión sobre página, contenido o momento", False),
    ("msg", "U", "W", "Precisar los datos de la publicación", False),
    ("end",),
    ("msg", "W", "M", "prepare_post(page_id, contenido exacto)", False),
    ("msg", "M", "D", "Validar y guardar operación, contenido y política aplicable", False),
    ("msg", "M", "W", "operation_id + vista previa + requisitos de autorización", True),
    ("start", "opt", "Solo si la política exige aprobación adicional"),
    ("msg", "W", "U", "Mostrar página y contenido exactos para confirmar", False),
    ("msg", "U", "M", "Confirmar en interfaz autenticada vinculada a la operación", False),
    ("msg", "M", "D", "Registrar autorización vinculada a parámetros y caducidad", False),
    ("end",),
    ("msg", "W", "M", "publish_post(operation_id) + token de acceso al MCP", False),
    ("msg", "M", "D", "Revalidar permisos y autorización; reservar y deduplicar", False),
    ("msg", "D", "M", "Estado de la operación y autorización vigente", True),
    ("start", "break", "Sin autorización vigente o con operación en curso / ya ejecutada"),
    ("msg", "M", "W", "Detener: informar rechazo o devolver el estado registrado", True),
    ("msg", "W", "U", "Comunicar el resultado sin volver a publicar", True),
    ("end",),
    ("msg", "M", "D", "Recuperar credencial de la página asignada", False),
    ("msg", "D", "M", "Credencial Meta para uso exclusivo dentro del VPS", True),
    ("msg", "M", "F", "Crear publicación con el token de la página autorizada", False),
    ("start", "alt", "Meta publica y se puede comprobar el resultado"),
    ("msg", "F", "P", "Crear publicación en la página elegida", False),
    ("msg", "F", "M", "Respuesta con identificador de publicación", True),
    ("msg", "M", "F", "Consultar publicación y verificar estado / enlace", False),
    ("msg", "F", "M", "Estado confirmado y enlace cuando esté disponible", True),
    ("msg", "M", "D", "Guardar resultado y auditoría sin secretos", False),
    ("msg", "M", "W", "published + post_id + enlace disponible", True),
    ("msg", "W", "U", "Confirmar publicación y mostrar el enlace disponible", True),
    ("else", "Meta devuelve un rechazo conocido"),
    ("msg", "F", "M", "Error de permisos, contenido u otra restricción", True),
    ("msg", "M", "D", "Registrar fallo conocido", False),
    ("msg", "M", "W", "failed + motivo y siguiente acción", True),
    ("msg", "W", "U", "Informar el fallo sin afirmar que se publicó", True),
    ("else", "Timeout, procesamiento pendiente o verificación inconclusa"),
    ("msg", "M", "D", "Guardar pending / unknown; programar reconciliación", False),
    ("msg", "M", "W", "Estado pendiente + ID de seguimiento; sin reintento ciego", True),
    ("msg", "W", "U", "Informar que la publicación aún no está confirmada", True),
    ("end",),
    ("note", "Nunca se entregan tokens de Meta a ChatGPT. Una solicitud autorizada no exige confirmación repetida."),
]


def event_height(event):
    if event[0] == "note":
        return 64
    if event[0] == "msg":
        return 61
    return 43 if event[0] in ("start", "else") else 21


PARTS.clear()
width = 1380
start_y = 182
height = start_y + sum(event_height(e) for e in events) + 80
label(width / 2, 39, "CU-03 · De tu solicitud en ChatGPT a la publicación en Facebook", 26, weight="700")
label(width / 2, 68, "Diseño propuesto · publicación inmediata de texto en una página autorizada", 17, color=MUTED)
positions = {p[0]: 105 + i * 234 for i, p in enumerate(participants)}
for pid, title, subtitle in participants:
    px = positions[pid]
    rect(px - 103, 100, 206, 65, "#eaf3fc" if pid in ("M", "D") else "#ffffff")
    label(px, 126, title, 17, weight="700")
    label(px, 150, subtitle, 12, color=MUTED)
    line(px, 165, px, height - 49, "#bbc9d4", dashed=True)

# Draw frames first so messages stay above their backgrounds and borders.
y = start_y
stack = []
frames = []
for event in events:
    kind = event[0]
    if kind == "start":
        stack.append((y, event[1], event[2]))
    elif kind == "end":
        sy, group_type, title = stack.pop()
        frames.append((sy, y + 9, group_type, title))
    y += event_height(event)
assert not stack
for sy, ey, group_type, title in frames:
    rect(18, sy, width - 36, ey - sy, "none", "#7891a7", 5)
    rect(18, sy, 50, 30, "#e4ecf3", "#7891a7", 5)
    label(43, sy + 21, group_type, 14, weight="700")
    label(81, sy + 22, title, 15, anchor="start", weight="600")

mmd = ["sequenceDiagram", "    autonumber"]
for pid, title, subtitle in participants:
    ptype = 'actor' if pid == 'U' else 'participant'
    mmd.append(f'    {ptype} {pid} as {title}')
y = start_y
number = 0
for event in events:
    kind = event[0]
    if kind == "msg":
        _, a, b, text, dashed = event
        number += 1
        x1, x2 = positions[a], positions[b]
        ty = y + 13
        # Long messages get a wide white label without shifting the lifelines.
        lines = textwrap.wrap(f'{number}. {text}', width=67)
        tx = max(290, min(width - 290, (x1 + x2) / 2))
        label_width = min(590, max(len(s) for s in lines) * 7.4 + 12)
        rect(tx - label_width / 2, ty - 15, label_width, 18 * len(lines) + 2, "#f8fafc", "none", 3)
        label(tx, ty, '\n'.join(lines), 14)
        line(x1, y + 48, x2, y + 48, BLUE, dashed=dashed, arrow=True)
        arrow = '-->>' if dashed else '->>'
        mmd.append(f'    {a}{arrow}{b}: {text}')
    elif kind == "note":
        rect(38, y + 6, width - 76, 44, "#e9f5f0", "#beded1", 6)
        label(width / 2, y + 34, event[1], 15, color=TEAL)
        mmd.append(f'    Note over U,P: {event[1]}')
    elif kind == "start":
        mmd.append(f'    {event[1]} {event[2]}')
    elif kind == "else":
        line(18, y, width - 18, y, "#7891a7", dashed=True)
        rect(30, y + 3, 1050, 30, "#f8fafc", "none", 0)
        label(42, y + 25, event[1], 15, anchor="start", weight="600")
        mmd.append(f'    else {event[1]}')
    elif kind == "end":
        mmd.append('    end')
    y += event_height(event)
label(width / 2, height - 21, "Las ramas de error no crean una nueva publicación automáticamente. Consultar CU-11 para reconciliación.", 14, color=MUTED)
save("secuencia-publicacion", "Secuencia de publicación desde ChatGPT Work hasta Facebook", width, height, PARTS)
(OUT / 'secuencia-publicacion.mmd').write_text('\n'.join(mmd) + '\n', encoding='utf-8')
print('Generated 4 SVG diagrams and 4 Mermaid sources.')
