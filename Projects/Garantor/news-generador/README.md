# News Garantor — estética nueva (Guía v2.0 · Manual V03)

Genera la news y las placas de WhatsApp con la identidad nueva de Garantor:
Poppins + Lora Itálica, navy `#252F4D`, azul `#5273F6`, gradiente azul → índigo `#515FDE`.

## Uso

1. Copiar `contenido_ejemplo.json` y reemplazar los textos.
   - `{palabras}` → acento en Lora Itálica azul (solo palabras cortas dentro de un titular)
   - `**texto**` → negrita navy
   - `foto_foco` → punto de la foto que tiene que quedar centrado en el recorte (x, y de 0 a 1)
2. Correr:

```bash
python3 build_news.py contenido.json foto.jpg "../News DD-MM-AAAA"
```

Agregar `--html` si hace falta el `news.html` (por ejemplo, para cargarlo en Perfit).

## Qué genera

```
News DD-MM-AAAA/
├── news_completa.png          (600 px de ancho a 3x = 1800 px)
├── News Separado/             (01_header … 06_cierre_footer; suman exacto el alto de la news)
└── Whastapp/                  (placa1_estado.png, placa2_estado.png — 1080×1920)
```

El script chequea que las fuentes estén cargadas, que las partes sumen el alto de la news
y que el contenido de las placas quede entre y=175 y y=1720 (zona segura de los estados).

## Criterios de la guía aplicados

- Header navy con logo blanco; cuerpo blanco en Poppins; botón azul.
- Placas: fondo navy, isologo + badge arriba, 2 orbes, CTA azul al final.
- Co-branding RE/MAX con igual jerarquía sobre fondo neutro (franja blanca en la news, tarjeta blanca en las placas).
  Si `audiencia` no es `RE/MAX` (por ejemplo, RED SUMA), el logo de RE/MAX no se incluye.
- Íconos: set oficial de 8 de la guía (`seguridad`, `rapidez`, `hogar`, `contrato`, `aprobado`, `familia`, `pago`, `soporte`).
- Gradiente institucional solo como fondo (cierre), nunca en texto.

## Requisitos

`pip install playwright pillow numpy`. Usa el Chromium instalado en `/opt/pw-browsers/chromium` si existe.
Las fuentes (Poppins y Lora, licencia OFL) van en `assets/fonts` y se embeben en base64.
