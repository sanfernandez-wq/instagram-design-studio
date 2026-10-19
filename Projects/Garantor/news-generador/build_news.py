#!/usr/bin/env python3
"""Generador de news Garantor — estética nueva (Guía de Estilo v2.0 · Manual V03).

Uso:
    python3 build_news.py contenido.json foto.jpg "carpeta/de/salida" [--html]

Genera, dentro de la carpeta de salida:
    news_completa.png
    News Separado/01_header.png ... 06_cierre_footer.png
    Whastapp/placa1_estado.png, placa2_estado.png
    (news.html solo con --html, por ejemplo para Perfit)

Marcado en los textos del JSON:
    {palabras}  -> Lora Italic (acento de la marca)
    **texto**   -> Poppins SemiBold navy
"""
import argparse
import base64
import io
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
CHROME = Path("/opt/pw-browsers/chromium")

# Paleta Garantor v2.0
NAVY, BLUE, INDIGO = "#252F4D", "#5273F6", "#515FDE"
GRAY_LIGHT, GRAY_MID, GRAY_DARK, BORDER = "#F5F6FA", "#6B7280", "#333333", "#E7E9F0"

# Set oficial de íconos de la guía (línea, trazo redondeado). El color sale de `currentColor`.
ICONS = {
    "seguridad": '<path d="M12 3l7 2.5v5.5c0 4.6-3 7.8-7 9-4-1.2-7-4.4-7-9V5.5z"/>',
    "rapidez": '<path d="M13.5 2.5L5 13h5.5L10 21.5 18.5 11H13z"/>',
    "hogar": '<path fill="currentColor" stroke="none" fill-rule="evenodd" d="M10.7 3.3a2 2 0 0 1 2.6 0l7 6.1c.44.38.7.94.7 1.5V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-8.1c0-.58.25-1.13.7-1.51zM12 12.5a2.5 2.5 0 0 0-2.5 2.5v3a1 1 0 0 0 1 1h3a1 1 0 0 0 1-1v-3a2.5 2.5 0 0 0-2.5-2.5"/>',
    "contrato": '<path d="M14 2.5H7a2 2 0 0 0-2 2v15a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7.5z"/><path d="M14 2.5V7a1 1 0 0 0 1 1h4"/><path d="M9 12.5h6M9 16h4"/>',
    "aprobado": '<path d="M20.5 12a8.5 8.5 0 1 1-3.4-6.8"/><path d="M8.5 11.5l3 3L21 5.5"/>',
    "familia": '<circle cx="9" cy="7.5" r="3.5"/><path d="M2.5 20.5c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6"/><path d="M16 4.2a3.5 3.5 0 0 1 0 6.6"/><path d="M17.5 14.8c2.4.6 4 2.6 4 5.7"/>',
    "pago": '<path d="M4 7.5a2 2 0 0 1 2-2h11a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z"/><path d="M19 10.5h-3a2 2 0 0 0 0 4h3"/>',
    "soporte": '<path d="M4.5 14v-2a7.5 7.5 0 0 1 15 0v2"/><path d="M4.5 14.5a2 2 0 0 1 2-2H8v6H6.5a2 2 0 0 1-2-2z"/><path d="M19.5 14.5a2 2 0 0 0-2-2H16v6h1.5a2 2 0 0 0 2-2z"/>',
}

SOCIAL = {
    "instagram": '<svg viewBox="0 0 24 24" fill="none"><rect x="3" y="3" width="18" height="18" rx="5" stroke="#FFFFFF" stroke-width="1.6"/><circle cx="12" cy="12" r="4" stroke="#FFFFFF" stroke-width="1.6"/><circle cx="17.2" cy="6.8" r="1" fill="#FFFFFF"/></svg>',
    "mail": '<svg viewBox="0 0 24 24" fill="none"><rect x="3" y="5" width="18" height="14" rx="2" stroke="#FFFFFF" stroke-width="1.6"/><path d="M3 6L12 13L21 6" stroke="#FFFFFF" stroke-width="1.6"/></svg>',
    "whatsapp": '<svg viewBox="0 0 24 24" fill="none"><path d="M12 3C7.03 3 3 7.03 3 12C3 13.6 3.42 15.1 4.16 16.4L3.2 21L7.9 20.06C9.15 20.68 10.54 21 12 21C16.97 21 21 16.97 21 12C21 7.03 16.97 3 12 3Z" stroke="#FFFFFF" stroke-width="1.5" stroke-linejoin="round"/><g transform="translate(6.6,5.83) scale(0.47)"><path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z" fill="#FFFFFF"/></g></svg>',
}

SOCIAL_LINKS = {
    "instagram": "https://www.instagram.com/garantor.ar/",
    "mail": "https://www.garantor.com.ar",
    "whatsapp": "https://api.whatsapp.com/send?phone=5491172037777&text=Hola!%20Quiero%20saber%20mas%20sobre%20Garantor",
}


def arrow(color):
    return (f'<svg viewBox="0 0 24 24" fill="none"><path d="M5 12H19" stroke="{color}" stroke-width="2" '
            f'stroke-linecap="round"/><path d="M13 6L19 12L13 18" stroke="{color}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round"/></svg>')


def icon(name, color=BLUE, stroke=2.2):
    body = ICONS[name]
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{stroke}" '
            f'stroke-linecap="round" stroke-linejoin="round" style="color:{color}">{body}</svg>')


_svg_counter = [0]


def logo(variant, isotipo=False):
    """Logo vectorial oficial. variant: 'blanco' (fondos navy) o 'color' (fondos claros)."""
    svg = (ASSETS / "logos" / f"garantor_{variant}.svg").read_text()
    _svg_counter[0] += 1
    svg = svg.replace("clip0_955_2919", f"clipG{_svg_counter[0]}")
    svg = re.sub(r'<svg width="1143" height="233"', '<svg', svg, count=1)
    if isotipo:  # solo el ícono: se recorta el viewBox al área del isotipo
        svg = svg.replace('viewBox="0 0 1143 233"', 'viewBox="0 0 218.4 232.8"', 1)
    return svg


def data_uri(path, mime):
    return f"data:{mime};base64," + base64.b64encode(Path(path).read_bytes()).decode()


def font_css():
    rules = []
    for w in (300, 400, 500, 600, 700):
        rules.append(
            "@font-face{font-family:'Poppins';font-style:normal;font-weight:%d;font-display:block;"
            "src:url(%s) format('truetype');}" % (w, data_uri(ASSETS / "fonts" / f"Poppins-{w}.ttf", "font/ttf")))
    for w in (400, 500, 600):
        rules.append(
            "@font-face{font-family:'Lora';font-style:italic;font-weight:%d;font-display:block;"
            "src:url(%s) format('truetype');}" % (w, data_uri(ASSETS / "fonts" / f"Lora-{w}-Italic.ttf", "font/ttf")))
    return "\n".join(rules)


def fmt(text):
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return re.sub(r"\{(.+?)\}", r"<em>\1</em>", text)


def crop(photo, aspect, focus=(0.5, 0.5), max_w=1800):
    """Recorta la foto a la proporción `aspect` (ancho/alto) centrando en `focus` y la embebe en base64."""
    im = ImageOps.exif_transpose(Image.open(photo)).convert("RGB")
    w, h = im.size
    if w / h > aspect:
        cw, ch = int(round(h * aspect)), h
    else:
        cw, ch = w, int(round(w / aspect))
    fx, fy = focus
    left = int(round(min(max(fx * w - cw / 2, 0), w - cw)))
    top = int(round(min(max(fy * h - ch / 2, 0), h - ch)))
    im = im.crop((left, top, left + cw, top + ch))
    if im.width > max_w:
        im = im.resize((max_w, int(round(max_w / aspect))), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=82, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode(), im.width


# --------------------------------------------------------------------------------------------
# NEWS (600px)
# --------------------------------------------------------------------------------------------
NEWS_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:#E9EBF2;padding:40px 0;font-family:'Poppins',Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;color:#333333}
.email-wrap{width:600px;margin:0 auto;background:#FFFFFF;overflow:hidden}
em{font-family:'Lora',Georgia,serif;font-style:italic;font-weight:500;color:#5273F6;letter-spacing:0}
strong{font-weight:600;color:#252F4D}
a{text-decoration:none}

/* --- Header + hero (navy con orbes) --- */
.top{position:relative;background:#252F4D;overflow:hidden}
.orb{position:absolute;border-radius:50%;z-index:0}
.floor{position:absolute;left:0;right:0;bottom:0;height:240px;background:#FFFFFF;z-index:1}
.header{position:relative;z-index:2;display:flex;align-items:center;justify-content:space-between;padding:30px 40px 26px}
.header::after{content:'';position:absolute;left:40px;right:40px;bottom:0;height:1px;background:rgba(255,255,255,.12)}
.header .logo svg{height:27px;width:auto;display:block}
.badge{display:inline-flex;align-items:center;gap:8px;background:rgba(82,115,246,.18);border:1px solid rgba(82,115,246,.45);
  border-radius:100px;padding:6px 14px 6px 12px;font-size:9.5px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:#5273F6;white-space:nowrap}
.badge::before{content:'';width:6px;height:6px;border-radius:50%;background:#5273F6}
.hero{position:relative;z-index:2;padding:34px 40px 0}
.s-label{display:flex;align-items:center;gap:10px;font-size:10px;font-weight:600;letter-spacing:.22em;text-transform:uppercase;color:rgba(255,255,255,.62);margin-bottom:14px}
.s-label::before{content:'';width:22px;height:2px;background:#5273F6;flex-shrink:0}
.hero h1{font-size:38px;font-weight:700;line-height:1.1;letter-spacing:-.01em;color:#FFFFFF;max-width:500px}
.hero h1 em{font-weight:500;font-size:1.03em}
.hero .bajada{margin-top:14px;font-size:16px;font-weight:300;line-height:1.6;color:rgba(255,255,255,.74);max-width:440px}
.hero .photo{margin-top:30px;width:520px;height:520px;border-radius:20px;overflow:hidden;box-shadow:0 18px 40px rgba(37,47,77,.20)}
.hero .photo img{width:100%;height:100%;object-fit:cover;display:block}

/* --- Intro --- */
.intro{padding:34px 40px 38px}
.intro p{font-size:16px;line-height:1.7;color:#333333}

/* --- Puntos clave --- */
.puntos{background:#F5F6FA;padding:38px 40px 40px}
.puntos h2{font-size:22px;font-weight:700;line-height:1.2;color:#252F4D;margin-bottom:18px}
.p-card{background:#FFFFFF;border:1px solid #E7E9F0;border-radius:16px;box-shadow:0 4px 18px rgba(37,47,77,.05)}
.p-row{display:flex;align-items:center;gap:16px;padding:18px 22px}
.p-row+.p-row{border-top:1px solid #E7E9F0}
.p-ico{width:46px;height:46px;border-radius:12px;background:rgba(82,115,246,.10);display:flex;align-items:center;justify-content:center;flex-shrink:0}
.p-ico svg{width:22px;height:22px;display:block}
.p-label{font-size:10px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:#5273F6;margin-bottom:3px}
.p-text{font-size:14.5px;font-weight:500;line-height:1.5;color:#252F4D}

/* --- Frase + CTA --- */
.frase-cta{padding:44px 40px 38px;text-align:center}
.frase{font-size:27px;font-weight:700;line-height:1.2;letter-spacing:-.01em;color:#252F4D;margin-bottom:26px}
.cta-wrap{display:inline-flex;align-items:center}
.cta-btn{background:#5273F6;color:#FFFFFF;font-weight:600;font-size:16px;letter-spacing:.01em;border-radius:999px;height:54px;padding:0 30px;display:flex;align-items:center}
.cta-arrow{width:54px;height:54px;border-radius:50%;background:#252F4D;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.cta-arrow svg{width:22px;height:22px;display:block}
.nota{margin-top:16px;font-size:13px;color:#6B7280}

/* --- Co-branding (fondo neutro, igual jerarquía) --- */
.cobrand{padding:0 40px}
.cobrand-in{border-top:1px solid #E7E9F0;padding:24px 0 28px;display:flex;align-items:center;justify-content:center;gap:28px}
.cobrand .g svg{height:24px;width:auto;display:block}
.cobrand .sep{width:1px;height:32px;background:#E7E9F0}
.cobrand .r{height:46px;width:auto;display:block}

/* --- Cierre (gradiente institucional) --- */
.cierre{position:relative;overflow:hidden;background:linear-gradient(120deg,#5273F6 0%,#515FDE 100%);padding:36px 40px 38px;color:#FFFFFF}
.cierre .wm{position:absolute;right:-46px;bottom:-62px;width:230px;opacity:.07}
.cierre .wm svg{width:100%;height:auto;display:block}
.cierre h3{position:relative;font-size:20px;font-weight:700;margin-bottom:8px}
.cierre p{position:relative;font-size:14.5px;line-height:1.65;color:rgba(255,255,255,.88);max-width:430px}
.cierre p b{color:#FFFFFF;font-weight:600}
.cierre .firma{position:relative;margin-top:22px;font-size:15px;font-weight:600}
.cierre .firma-linea{position:relative;font-size:15px;font-weight:300;color:rgba(255,255,255,.92)}
.cierre em{color:#FFFFFF}

/* --- Footer --- */
.footer{background:#252F4D;padding:26px 40px 28px;display:flex;align-items:center;justify-content:space-between;gap:20px}
.footer .addr{font-size:11.5px;line-height:1.75;color:rgba(255,255,255,.62)}
.footer .addr a{color:#FFFFFF}
.social{display:flex;gap:16px;flex-shrink:0}
.social svg{width:22px;height:22px;display:block}
"""


def news_html(c, photo_uri, remax_uri):
    puntos = "\n".join(
        f'<div class="p-row"><div class="p-ico">{icon(p["icono"])}</div>'
        f'<div><div class="p-label">{p["label"]}</div><div class="p-text">{fmt(p["texto"])}</div></div></div>'
        for p in c["puntos"])
    social = "".join(f'<a href="{SOCIAL_LINKS[k]}">{SOCIAL[k]}</a>' for k in ("instagram", "mail", "whatsapp"))
    remax = (f'<div class="sep"></div><img class="r" src="{remax_uri}" alt="RE/MAX Partner estratégico">'
             if c.get("audiencia", "RE/MAX") == "RE/MAX" else "")
    puntos_titulo = f'<h2>{fmt(c["puntos_titulo"])}</h2>' if c.get("puntos_titulo") else ""
    etiqueta = f'<div class="s-label">{c["etiqueta"]}</div>' if c.get("etiqueta") else ""
    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Garantor · News</title>
<style>
{font_css()}
{NEWS_CSS}
</style></head>
<body>
<div class="email-wrap">
  <div class="top">
    <div class="orb" style="width:330px;height:330px;background:rgba(82,115,246,.14);top:-120px;right:-110px"></div>
    <div class="orb" style="width:170px;height:170px;background:rgba(81,95,222,.13);top:250px;left:-70px"></div>
    <div class="orb" style="width:84px;height:84px;border:1px solid rgba(255,255,255,.12);top:150px;right:58px"></div>
    <div class="floor"></div>
    <div class="header">
      <div class="logo">{logo("blanco")}</div>
      <div class="badge">{c["badge"]}</div>
    </div>
    <div class="hero">
      {etiqueta}
      <h1>{fmt(c["titulo"])}</h1>
      <p class="bajada">{fmt(c["bajada"])}</p>
      <div class="photo"><img src="{photo_uri}" alt=""></div>
    </div>
  </div>

  <div class="intro"><p>{fmt(c["intro"])}</p></div>

  <div class="puntos">
    {puntos_titulo}
    <div class="p-card">{puntos}</div>
  </div>

  <div class="frase-cta">
    <div class="frase">{fmt(c["frase"])}</div>
    <a class="cta-wrap" href="{c.get("cta_link", "#")}">
      <span class="cta-btn">{c["cta"]}</span><span class="cta-arrow">{arrow("#FFFFFF")}</span>
    </a>
    <div class="nota">{fmt(c.get("nota", ""))}</div>
  </div>

  <div class="cobrand"><div class="cobrand-in"><div class="g">{logo("color")}</div>{remax}</div></div>

  <div class="cierre">
    <div class="wm">{logo("blanco", isotipo=True)}</div>
    <h3>{c["cierre_titulo"]}</h3>
    <p>{c["cierre_texto"]}</p>
    <div class="firma">{c["firma"]}</div>
    <div class="firma-linea">{fmt(c.get("firma_linea", ""))}</div>
  </div>

  <div class="footer">
    <div class="addr">Garantor | Av. del Libertador 742, 3er Piso, Vicente López<br>
      © {c["fecha"][-4:]} Garantor. Todos los derechos reservados.<br>
      <a href="https://www.garantor.com.ar">www.garantor.com.ar</a></div>
    <div class="social">{social}</div>
  </div>
</div>
</body></html>"""


# --------------------------------------------------------------------------------------------
# PLACAS WHATSAPP (1080x1920) — fondo navy, isologo + badge, 2 orbes, CTA azul al final
# Todo el contenido entre y=175 y y=1720 (zona segura de estados).
# --------------------------------------------------------------------------------------------
PLACA_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1080px;height:1920px;overflow:hidden}
body{font-family:'Poppins',Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased}
em{font-family:'Lora',Georgia,serif;font-style:italic;font-weight:500;color:#5273F6}
.placa{position:relative;width:1080px;height:1920px;background:#252F4D;overflow:hidden}
.orb{position:absolute;border-radius:50%}
.head{position:absolute;top:188px;left:80px;right:80px;display:flex;align-items:center;justify-content:space-between}
.head .logo svg{height:54px;width:auto;display:block}
.badge{display:inline-flex;align-items:center;gap:14px;background:rgba(82,115,246,.18);border:2px solid rgba(82,115,246,.45);
  border-radius:100px;padding:13px 28px 13px 24px;font-size:19px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:#5273F6;white-space:nowrap}
.badge::before{content:'';width:11px;height:11px;border-radius:50%;background:#5273F6}
.s-label{display:flex;align-items:center;gap:18px;font-size:21px;font-weight:600;letter-spacing:.22em;text-transform:uppercase;color:rgba(255,255,255,.62)}
.s-label::before{content:'';width:42px;height:4px;background:#5273F6;flex-shrink:0}
.body{position:absolute;left:80px;right:80px}
.cobrand{position:absolute;left:80px;right:80px;top:1612px;height:104px;background:#FFFFFF;border-radius:26px;display:flex;align-items:center;justify-content:center;gap:44px}
.cobrand .g svg{height:42px;width:auto;display:block}
.cobrand .sep{width:2px;height:54px;background:#E7E9F0}
.cobrand .r{height:76px;width:auto;display:block}

/* placa 1 */
.p1 .photo{width:920px;height:800px;border-radius:40px;overflow:hidden}
.p1 .photo img{width:100%;height:100%;object-fit:cover;display:block}
.p1 .s-label{margin-top:52px}
.p1 h1{margin-top:22px;font-size:80px;font-weight:700;line-height:1.08;letter-spacing:-.01em;color:#FFFFFF}
.p1 h1 em{font-size:1.03em}
.p1 .bajada{margin-top:22px;font-size:32px;font-weight:300;line-height:1.5;color:rgba(255,255,255,.76);max-width:820px}

/* placa 2 */
.p2 h1{margin-top:22px;font-size:72px;font-weight:700;line-height:1.1;letter-spacing:-.01em;color:#FFFFFF}
.p2 .cards{margin-top:44px;display:flex;flex-direction:column;gap:18px}
.p2 .card{display:flex;align-items:center;gap:30px;padding:30px 34px;background:rgba(255,255,255,.06);border:2px solid rgba(255,255,255,.10);border-radius:28px}
.p2 .ico{width:84px;height:84px;border-radius:22px;background:rgba(82,115,246,.20);display:flex;align-items:center;justify-content:center;flex-shrink:0}
.p2 .ico svg{width:42px;height:42px;display:block}
.p2 .label{font-size:19px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:#5273F6;margin-bottom:4px}
.p2 .text{font-size:29px;font-weight:500;line-height:1.4;color:#FFFFFF}
.p2 .frase{margin-top:56px;font-size:50px;font-weight:700;line-height:1.15;color:#FFFFFF}
.p2 .cta-row{margin-top:36px;display:flex;align-items:center;gap:30px}
.cta-wrap{display:inline-flex;align-items:center}
.cta-btn{background:#5273F6;color:#FFFFFF;font-weight:600;font-size:34px;letter-spacing:.01em;border-radius:999px;height:100px;padding:0 50px;display:flex;align-items:center}
.cta-arrow{width:100px;height:100px;border-radius:50%;background:#FFFFFF;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.cta-arrow svg{width:40px;height:40px;display:block}
"""

ORBS = """
<div class="orb" style="width:760px;height:760px;background:rgba(82,115,246,.14);top:-300px;right:-300px"></div>
<div class="orb" style="width:520px;height:520px;background:rgba(81,95,222,.13);bottom:-210px;left:-220px"></div>
"""
RING = {"p1": "top:1760px;right:150px", "p2": "top:1330px;right:70px"}


def placa_shell(inner, cls, c, remax_uri):
    remax = (f'<div class="sep"></div><img class="r" src="{remax_uri}" alt="RE/MAX">'
             if c.get("audiencia", "RE/MAX") == "RE/MAX" else "")
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><style>
{font_css()}
{PLACA_CSS}
</style></head><body><div class="placa {cls}">
{ORBS}
<div class="orb" style="width:180px;height:180px;border:2px solid rgba(255,255,255,.10);{RING[cls]}"></div>
<div class="head"><div class="logo">{logo("blanco")}</div><div class="badge">{c["badge"]}</div></div>
{inner}
<div class="cobrand"><div class="g">{logo("color")}</div>{remax}</div>
</div></body></html>"""


def placa1_html(c, photo_uri, remax_uri):
    etiqueta = f'<div class="s-label">{c["etiqueta"]}</div>' if c.get("etiqueta") else ""
    inner = f"""<div class="body" style="top:300px">
  <div class="photo"><img src="{photo_uri}" alt=""></div>
  {etiqueta}
  <h1>{fmt(c.get("placa1_titulo", c["titulo"]))}</h1>
  <p class="bajada">{fmt(c.get("placa1_bajada", c["bajada"]))}</p>
</div>"""
    return placa_shell(inner, "p1", c, remax_uri)


def placa2_html(c, remax_uri):
    cards = "\n".join(
        f'<div class="card"><div class="ico">{icon(p["icono"], BLUE, 2.2)}</div>'
        f'<div><div class="label">{p["label"]}</div><div class="text">{fmt(p["texto"])}</div></div></div>'
        for p in c["puntos"])
    inner = f"""<div class="body" style="top:330px">
  <div class="s-label">{c.get("placa2_etiqueta", c.get("etiqueta", ""))}</div>
  <h1>{fmt(c.get("placa2_titulo", c.get("puntos_titulo", "")))}</h1>
  <div class="cards">{cards}</div>
  <div class="frase">{fmt(c["frase"])}</div>
  <div class="cta-row"><span class="cta-wrap"><span class="cta-btn">{c["cta"]}</span><span class="cta-arrow">{arrow(BLUE)}</span></span></div>
</div>"""
    return placa_shell(inner, "p2", c, remax_uri)


# --------------------------------------------------------------------------------------------
# Render
# --------------------------------------------------------------------------------------------
def launch(p):
    kw = dict(args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
    if CHROME.exists():
        kw["executable_path"] = str(CHROME)
    return p.chromium.launch(**kw)


def load_fonts(pg):
    pg.evaluate("Promise.all([...document.fonts].map(f => f.load()))")
    pg.evaluate("document.fonts.ready.then(() => true)")
    pg.wait_for_timeout(500)
    status = pg.evaluate("[...document.fonts].map(f => f.family + ' ' + f.weight + ' ' + f.style + ' ' + f.status)")
    bad = [s for s in status if not s.endswith("loaded")]
    if bad:
        sys.exit(f"Fuentes sin cargar: {bad}")
    return status


SECTIONS = [("01_header", ".header"), ("02_foto_titulo", ".hero"), ("03_intro", ".intro"),
            ("04_bullets", ".puntos"), ("05_frase_cta", ".frase-cta"), ("06_cierre_footer", ".cobrand")]


def render_news(html_path, out_dir, scale=3):
    out_dir.mkdir(parents=True, exist_ok=True)
    full = out_dir / "news_completa.png"
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 680, "height": 900}, device_scale_factor=scale)
        pg.goto(html_path.as_uri())
        fonts = load_fonts(pg)
        wrap = pg.query_selector(".email-wrap")
        wb = wrap.bounding_box()
        starts = [pg.query_selector(sel).bounding_box()["y"] - wb["y"] for _, sel in SECTIONS]
        wrap.screenshot(path=str(full))
        b.close()
    im = Image.open(full)
    k = im.height / wb["height"]
    cuts = [0] + [int(round(s * k)) for s in starts[1:]] + [im.height]
    parts_dir = out_dir / "News Separado"
    parts_dir.mkdir(exist_ok=True)
    total = 0
    for i, (name, _) in enumerate(SECTIONS):
        part = im.crop((0, cuts[i], im.width, cuts[i + 1]))
        part.save(parts_dir / f"{name}.png", optimize=True)
        total += part.height
    assert total == im.height, f"Las partes suman {total}px y la news mide {im.height}px"
    return im.size, fonts


def render_placa(html_path, out_png):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
        pg.goto(html_path.as_uri())
        load_fonts(pg)
        pg.screenshot(path=str(out_png), clip={"x": 0, "y": 0, "width": 1080, "height": 1920})
        b.close()
    # Zona segura: nada claro (texto, logos, foto) fuera de y=175..1720
    a = np.asarray(Image.open(out_png).convert("L")).astype(int)
    rows = np.where((a > 110).sum(axis=1) > 0)[0]
    top, bottom = int(rows.min()), int(rows.max())
    if top < 175 or bottom > 1720:
        print(f"  ATENCIÓN {out_png.name}: contenido entre y={top} y y={bottom} (fuera de 175–1720)")
    return top, bottom


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("contenido")
    ap.add_argument("foto")
    ap.add_argument("salida")
    ap.add_argument("--html", action="store_true", help="incluir news.html en la salida (p. ej. para Perfit)")
    args = ap.parse_args()

    c = json.loads(Path(args.contenido).read_text(encoding="utf-8"))
    out = Path(args.salida)
    out.mkdir(parents=True, exist_ok=True)
    focus = tuple(c.get("foto_foco", (0.5, 0.5)))
    remax_uri = data_uri(ASSETS / "logos" / "remax_partner_navy.png", "image/png")

    news_photo, src_w = crop(args.foto, 1.0, focus)
    placa_photo, _ = crop(args.foto, 920 / 800, focus)
    if src_w < 1500:
        print(f"  Aviso: la foto mide {src_w}px de ancho; para la versión final conviene una de 1600px o más.")

    work = Path(tempfile.mkdtemp(prefix="garantor_news_"))
    news_file = work / "news.html"
    news_file.write_text(news_html(c, news_photo, remax_uri), encoding="utf-8")
    size, fonts = render_news(news_file, out)
    print(f"  news_completa.png {size[0]}x{size[1]} · 6 partes OK · fuentes: {len(fonts)} cargadas")

    wa = out / "Whastapp"
    wa.mkdir(exist_ok=True)
    for name, html in (("placa1_estado", placa1_html(c, placa_photo, remax_uri)),
                       ("placa2_estado", placa2_html(c, remax_uri))):
        f = work / f"{name}.html"
        f.write_text(html, encoding="utf-8")
        top, bottom = render_placa(f, wa / f"{name}.png")
        print(f"  {name}.png 1080x1920 · contenido y={top}–{bottom}")

    if args.html:
        shutil.copy(news_file, out / "news.html")
    shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
