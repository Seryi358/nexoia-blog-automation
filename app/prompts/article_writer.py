SYSTEM_PROMPT = """Eres un escritor experto en tecnologia e inteligencia artificial para el blog IA Practica.
Escribes en espanol latinoamericano (no espanol de Espana).
Tu audiencia son profesionales, emprendedores y entusiastas de la tecnologia en Latinoamerica.

REGLAS DE ESCRITURA:
1. Escribe con un tono conversacional pero profesional, como un experto que explica a un colega
2. Usa ejemplos practicos y reales, no teoricos
3. Incluye datos especificos, numeros y estadisticas cuando sea posible
4. Estructura con encabezados claros (H2, H3) que contengan keywords
5. Parrafos cortos (2-4 oraciones maximo)
6. Incluye listas con viñetas para facilitar la lectura
7. Abre con un gancho que capture la atencion en las primeras 2 oraciones
8. Cierra con una conclusion que resuma los puntos clave y un call-to-action
9. NO uses frases cliche de IA como "en el mundo actual", "sin lugar a dudas", "cabe destacar"
10. NO uses emojis en el cuerpo del articulo
11. Evita la voz pasiva excesiva - se directo
12. Incluye una seccion de "Preguntas Frecuentes" al final con 3-4 FAQs en formato pregunta/respuesta

FORMATO DE SALIDA:
- El contenido debe estar en HTML valido
- Usa <h2> para secciones principales y <h3> para subsecciones
- Usa <p> para parrafos
- Usa <ul><li> para listas
- Usa <strong> para enfasis en keywords importantes
- Usa <blockquote> para citas o datos destacados
- NO incluyas <h1> (WordPress lo genera del titulo)
- NO incluyas imagenes en el HTML (se agregan por separado)
- Incluye la keyword principal de forma natural 3-5 veces en el texto
"""

ARTICLE_PROMPT = """Escribe un articulo completo para el blog IA Practica sobre el siguiente tema:

TEMA: {topic}
KEYWORD PRINCIPAL: {focus_keyword}
KEYWORDS SECUNDARIAS: {secondary_keywords}
CATEGORIA: {category}
CLUSTER: {cluster}

REQUISITOS CRITICOS:
- LONGITUD MINIMA OBLIGATORIA: {min_words} palabras. Esto es CRITICO. Cuenta tus palabras. Articulos menores a {min_words} palabras seran rechazados. Escribe contenido extenso y detallado.
- Incluye AL MENOS 7 secciones con H2, cada una con 2-4 parrafos sustanciales
- Incluye subsecciones H3 dentro de cada H2 con contenido detallado
- Cada seccion H2 debe tener MINIMO 150 palabras
- Incluye una seccion de FAQ al final con 4-5 preguntas con respuestas detalladas (3-4 oraciones cada respuesta)
- La keyword principal debe aparecer en el primer parrafo
- Incluye datos y estadisticas actualizadas a 2026
- Incluye ejemplos practicos, casos de uso reales y comparaciones detalladas
- NO escribas contenido generico o superficial - profundiza en cada punto

RECOMENDACIONES DE HERRAMIENTAS (AFILIADOS):
Cuando menciones herramientas o servicios en el articulo, incluye naturalmente una seccion o caja de recomendacion usando este formato HTML:
<div style="background:#f0f7ff;border:2px solid #1E40AF;border-radius:12px;padding:20px;margin:24px 0;">
<h3 style="color:#1E40AF;margin-top:0;">Herramienta Recomendada: [Nombre]</h3>
<p>[Descripcion breve de por que la recomendamos - 2-3 oraciones]</p>
<p><a href="[URL_HERRAMIENTA]" target="_blank" rel="noopener sponsored" style="background:#1E40AF;color:white;padding:10px 20px;border-radius:6px;text-decoration:none;display:inline-block;">Probar [Nombre] gratis</a></p>
</div>
Incluye 1-2 cajas de recomendacion por articulo, solo cuando sea relevante al tema. NO fuerces recomendaciones que no tengan relacion con el contenido.

{affiliate_links_instruction}

{internal_links_instruction}

Responde UNICAMENTE con un JSON valido con esta estructura exacta:
{{
  "title": "Titulo SEO optimizado (50-60 caracteres ideal)",
  "slug": "slug-url-amigable-con-keywords",
  "meta_description": "Meta descripcion atractiva (150-160 caracteres) que incluya la keyword principal",
  "content_html": "<h2>...</h2><p>...</p>...",
  "tags": ["tag1", "tag2", "tag3"],
  "word_count": 2000
}}
"""

INTERNAL_LINKS_TEMPLATE = """ENLACES INTERNOS: Incluye naturalmente estos enlaces a otros articulos del blog:
{links}
Usa el formato: <a href="URL">texto ancla descriptivo</a>
Integralos de forma natural en el contenido, no los fuerces.
"""

AFFILIATE_LINKS_TEMPLATE = """LINKS DE AFILIADO: Cuando menciones estas herramientas, usa estos links exactos:
{affiliate_links}
Usa estos links dentro de las cajas de recomendacion. El atributo rel="noopener sponsored" es OBLIGATORIO.
"""

# Affiliate links configuration - add your links here
AFFILIATE_LINKS = {
    "hostinger": {
        "name": "Hostinger",
        "url": "https://hostinger.com?REFERRALCODE=1SERGIO58",
        "description": "Hosting web rapido y economico para tu blog o proyecto online. Dominio gratis incluido."
    },
    "canva": {
        "name": "Canva Pro",
        "url": "https://www.canva.com/",
        "description": "Disena contenido profesional con IA integrada. Plantillas, imagenes y herramientas de diseno."
    },
    "chatgpt": {
        "name": "ChatGPT Plus",
        "url": "https://chat.openai.com/",
        "description": "Accede a GPT-4o y herramientas avanzadas de IA para productividad y creacion de contenido."
    },
    "jasper": {
        "name": "Jasper AI",
        "url": "https://www.jasper.ai/",
        "description": "Plataforma de escritura con IA para marketing. Genera contenido optimizado para SEO."
    },
    "surfer": {
        "name": "Surfer SEO",
        "url": "https://surferseo.com/",
        "description": "Optimiza tu contenido para SEO con IA. Analisis de competencia y sugerencias en tiempo real."
    },
    "notion": {
        "name": "Notion",
        "url": "https://www.notion.so/",
        "description": "Organiza tu trabajo y vida con IA integrada. Notas, proyectos y bases de datos en un solo lugar."
    },
    "midjourney": {
        "name": "Midjourney",
        "url": "https://www.midjourney.com/",
        "description": "Genera imagenes profesionales con IA. La herramienta mas popular para creacion visual."
    },
    "cursor": {
        "name": "Cursor AI",
        "url": "https://www.cursor.com/",
        "description": "Editor de codigo con IA que acelera tu programacion. Autocompletado inteligente y refactoring."
    },
}

def get_affiliate_instruction(topic: str) -> str:
    """Select relevant affiliate links based on article topic."""
    topic_lower = topic.lower()
    relevant = []
    for key, info in AFFILIATE_LINKS.items():
        # Match affiliates to topic keywords
        if key in topic_lower or info["name"].lower() in topic_lower:
            relevant.append(f'- {info["name"]}: {info["url"]} - {info["description"]}')

    # Always include 2-3 general affiliates if none matched
    if len(relevant) < 2:
        defaults = ["hostinger", "canva", "chatgpt"]
        for d in defaults:
            if d in AFFILIATE_LINKS and len(relevant) < 3:
                info = AFFILIATE_LINKS[d]
                link = f'- {info["name"]}: {info["url"]} - {info["description"]}'
                if link not in relevant:
                    relevant.append(link)

    if relevant:
        return AFFILIATE_LINKS_TEMPLATE.format(affiliate_links="\n".join(relevant))
    return ""
