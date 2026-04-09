"""Seed the content plan database with 100+ article topics organized by clusters."""
import asyncio
import json
from app.database import init_db, async_session, ContentPlan

CONTENT_PLAN = [
    # ── CLUSTER 1: Herramientas IA para Productividad (priority 1-2) ──
    {"topic": "Las 15 mejores herramientas de inteligencia artificial para aumentar tu productividad en 2026", "cluster": "productividad", "category": "herramientas-ia", "focus_keyword": "herramientas inteligencia artificial productividad", "secondary_keywords": ["apps ia productividad", "software ia trabajo", "mejores herramientas ia 2026"], "priority": 1},
    {"topic": "ChatGPT vs Claude vs Gemini: cual es mejor para tu trabajo diario en 2026", "cluster": "productividad", "category": "herramientas-ia", "focus_keyword": "chatgpt vs claude vs gemini", "secondary_keywords": ["comparativa ia 2026", "mejor chatbot ia", "ia para trabajo"], "priority": 1},
    {"topic": "Como usar Notion AI para organizar tu vida y tu negocio", "cluster": "productividad", "category": "herramientas-ia", "focus_keyword": "notion ai como usar", "secondary_keywords": ["notion ai tutorial", "notion ia productividad", "organizar con ia"], "priority": 2},
    {"topic": "Microsoft Copilot: guia completa para sacarle el maximo provecho en Office", "cluster": "productividad", "category": "herramientas-ia", "focus_keyword": "microsoft copilot guia", "secondary_keywords": ["copilot office 365", "copilot word excel", "ia microsoft"], "priority": 2},
    {"topic": "7 herramientas de IA gratuitas que reemplazan software de pago", "cluster": "productividad", "category": "herramientas-ia", "focus_keyword": "herramientas ia gratis", "secondary_keywords": ["ia gratuita alternativas", "software ia gratis 2026", "apps ia sin pagar"], "priority": 1},
    {"topic": "Automatiza tu email con IA: las mejores herramientas para gestionar tu bandeja de entrada", "cluster": "productividad", "category": "herramientas-ia", "focus_keyword": "automatizar email con ia", "secondary_keywords": ["ia para correos", "gestionar email ia", "productividad email"], "priority": 2},
    {"topic": "Las mejores extensiones de Chrome con IA que necesitas instalar ya", "cluster": "productividad", "category": "herramientas-ia", "focus_keyword": "extensiones chrome ia", "secondary_keywords": ["plugins chrome ia", "extensiones navegador ia", "chrome ia productividad"], "priority": 2},
    {"topic": "Como usar IA para tomar notas automaticas en reuniones", "cluster": "productividad", "category": "herramientas-ia", "focus_keyword": "ia notas reuniones", "secondary_keywords": ["transcribir reuniones ia", "otter ai fireflies", "automatizar actas reuniones"], "priority": 2},
    {"topic": "Perplexity AI vs Google: por que cada vez mas personas usan IA para buscar informacion", "cluster": "productividad", "category": "herramientas-ia", "focus_keyword": "perplexity ai vs google", "secondary_keywords": ["buscador ia", "perplexity tutorial", "buscar con ia"], "priority": 1},
    {"topic": "Las 10 mejores apps de IA para tu celular Android e iPhone", "cluster": "productividad", "category": "herramientas-ia", "focus_keyword": "apps ia celular", "secondary_keywords": ["aplicaciones ia movil", "apps inteligencia artificial android", "ia para iphone"], "priority": 1},

    # ── CLUSTER 2: IA para Negocios y Emprendedores (priority 2-3) ──
    {"topic": "Como las pymes en Latinoamerica estan usando IA para reducir costos operativos", "cluster": "negocios", "category": "ia-negocios", "focus_keyword": "pymes ia latinoamerica", "secondary_keywords": ["ia para pymes", "automatizar negocio ia", "reducir costos ia"], "priority": 2},
    {"topic": "Guia completa: automatiza tu negocio con herramientas no-code e IA", "cluster": "negocios", "category": "ia-negocios", "focus_keyword": "automatizar negocio no-code ia", "secondary_keywords": ["no-code ia", "zapier make ia", "automatizacion sin programar"], "priority": 2},
    {"topic": "Como crear un chatbot de atencion al cliente con IA sin saber programar", "cluster": "negocios", "category": "ia-negocios", "focus_keyword": "chatbot ia atencion cliente", "secondary_keywords": ["crear chatbot ia", "chatbot whatsapp ia", "chatbot sin programar"], "priority": 2},
    {"topic": "IA para ecommerce: 8 formas de aumentar tus ventas con inteligencia artificial", "cluster": "negocios", "category": "ia-negocios", "focus_keyword": "ia ecommerce ventas", "secondary_keywords": ["ia para tienda online", "aumentar ventas ia", "ecommerce inteligencia artificial"], "priority": 3},
    {"topic": "Como usar ChatGPT para escribir propuestas comerciales que cierran ventas", "cluster": "negocios", "category": "ia-negocios", "focus_keyword": "chatgpt propuestas comerciales", "secondary_keywords": ["ia para ventas", "escribir propuestas ia", "chatgpt negocios"], "priority": 3},
    {"topic": "Las mejores herramientas de IA para analisis de datos sin ser data scientist", "cluster": "negocios", "category": "ia-negocios", "focus_keyword": "ia analisis datos facil", "secondary_keywords": ["analizar datos ia", "herramientas datos ia", "data analysis ia"], "priority": 2},
    {"topic": "Como implementar IA en tu empresa: guia paso a paso para 2026", "cluster": "negocios", "category": "ia-negocios", "focus_keyword": "implementar ia empresa", "secondary_keywords": ["ia para empresas", "adoptar ia negocio", "estrategia ia empresarial"], "priority": 2},
    {"topic": "Facturacion y contabilidad con IA: herramientas que ahorran horas de trabajo", "cluster": "negocios", "category": "ia-negocios", "focus_keyword": "contabilidad ia herramientas", "secondary_keywords": ["facturacion automatica ia", "ia para contadores", "automatizar contabilidad"], "priority": 3},
    {"topic": "Como usar IA para investigacion de mercado y analisis de competencia", "cluster": "negocios", "category": "ia-negocios", "focus_keyword": "investigacion mercado ia", "secondary_keywords": ["analisis competencia ia", "estudio mercado ia", "ia market research"], "priority": 3},
    {"topic": "Agentes de IA: que son y como van a transformar los negocios en 2026", "cluster": "negocios", "category": "ia-negocios", "focus_keyword": "agentes ia negocios", "secondary_keywords": ["ai agents 2026", "agentes inteligencia artificial", "ia autonoma negocios"], "priority": 1},

    # ── CLUSTER 3: Tutoriales IA Paso a Paso (priority 1-2) ──
    {"topic": "Tutorial ChatGPT para principiantes: desde cero hasta prompts avanzados", "cluster": "tutoriales", "category": "tutoriales-ia", "focus_keyword": "tutorial chatgpt principiantes", "secondary_keywords": ["como usar chatgpt", "chatgpt desde cero", "prompts chatgpt"], "priority": 1},
    {"topic": "Como escribir prompts efectivos: la guia definitiva del prompt engineering", "cluster": "tutoriales", "category": "tutoriales-ia", "focus_keyword": "como escribir prompts efectivos", "secondary_keywords": ["prompt engineering guia", "mejores prompts ia", "crear prompts chatgpt"], "priority": 1},
    {"topic": "Tutorial Midjourney 2026: como crear imagenes profesionales con IA", "cluster": "tutoriales", "category": "tutoriales-ia", "focus_keyword": "tutorial midjourney 2026", "secondary_keywords": ["midjourney como usar", "crear imagenes ia", "midjourney guia completa"], "priority": 1},
    {"topic": "Como usar Claude AI: guia completa del asistente de Anthropic", "cluster": "tutoriales", "category": "tutoriales-ia", "focus_keyword": "como usar claude ai", "secondary_keywords": ["claude anthropic tutorial", "claude vs chatgpt", "claude ai guia"], "priority": 1},
    {"topic": "Aprende a usar DALL-E 3 para crear imagenes increibles desde ChatGPT", "cluster": "tutoriales", "category": "tutoriales-ia", "focus_keyword": "dall-e 3 tutorial", "secondary_keywords": ["crear imagenes dall-e", "dall-e chatgpt", "generar imagenes ia"], "priority": 2},
    {"topic": "Como usar Gemini de Google: tutorial completo con ejemplos practicos", "cluster": "tutoriales", "category": "tutoriales-ia", "focus_keyword": "como usar gemini google", "secondary_keywords": ["gemini tutorial espanol", "google gemini guia", "gemini ia google"], "priority": 1},
    {"topic": "Cursor AI: el editor de codigo con IA que esta revolucionando la programacion", "cluster": "tutoriales", "category": "tutoriales-ia", "focus_keyword": "cursor ai tutorial", "secondary_keywords": ["cursor editor ia", "programar con ia", "cursor ide guia"], "priority": 2},
    {"topic": "Como crear videos con IA: guia de herramientas para principiantes", "cluster": "tutoriales", "category": "tutoriales-ia", "focus_keyword": "crear videos ia", "secondary_keywords": ["herramientas video ia", "generar videos ia", "ia para videos"], "priority": 2},
    {"topic": "Automatiza tareas repetitivas con Make (Integromat) e IA: tutorial paso a paso", "cluster": "tutoriales", "category": "tutoriales-ia", "focus_keyword": "make integromat ia tutorial", "secondary_keywords": ["automatizar con make", "integromat tutorial", "no-code automatizacion"], "priority": 2},
    {"topic": "Como usar IA para aprender idiomas: las mejores apps y tecnicas en 2026", "cluster": "tutoriales", "category": "tutoriales-ia", "focus_keyword": "aprender idiomas con ia", "secondary_keywords": ["ia para idiomas", "apps idiomas ia", "duolingo ia alternativas"], "priority": 2},

    # ── CLUSTER 4: IA para Creadores de Contenido (priority 2-3) ──
    {"topic": "Como usar IA para crear contenido para redes sociales sin perder autenticidad", "cluster": "creadores", "category": "ia-creadores", "focus_keyword": "ia contenido redes sociales", "secondary_keywords": ["crear posts ia", "ia para instagram", "contenido redes ia"], "priority": 2},
    {"topic": "Las mejores herramientas de IA para editar fotos profesionalmente", "cluster": "creadores", "category": "ia-creadores", "focus_keyword": "editar fotos ia herramientas", "secondary_keywords": ["editor fotos ia", "ia para fotografos", "retoque fotos ia"], "priority": 2},
    {"topic": "Como crear un podcast con IA: desde la grabacion hasta la edicion automatica", "cluster": "creadores", "category": "ia-creadores", "focus_keyword": "crear podcast ia", "secondary_keywords": ["podcast ia herramientas", "editar podcast ia", "ia para podcasters"], "priority": 3},
    {"topic": "IA para YouTube: herramientas para guiones, thumbnails y edicion de video", "cluster": "creadores", "category": "ia-creadores", "focus_keyword": "ia para youtube", "secondary_keywords": ["herramientas youtube ia", "crear thumbnails ia", "guiones youtube ia"], "priority": 2},
    {"topic": "Como escribir un libro con ayuda de IA: guia practica para escritores", "cluster": "creadores", "category": "ia-creadores", "focus_keyword": "escribir libro ia", "secondary_keywords": ["ia para escritores", "chatgpt para escribir libro", "ia escritura creativa"], "priority": 3},
    {"topic": "Genera musica con IA: las mejores plataformas para crear canciones y beats", "cluster": "creadores", "category": "ia-creadores", "focus_keyword": "generar musica ia", "secondary_keywords": ["crear musica ia", "ia para musicos", "suno udio tutorial"], "priority": 3},
    {"topic": "Como crear presentaciones impactantes con IA en minutos", "cluster": "creadores", "category": "ia-creadores", "focus_keyword": "presentaciones ia", "secondary_keywords": ["crear presentaciones ia", "gamma ai tutorial", "slides ia herramientas"], "priority": 2},
    {"topic": "Herramientas de IA para diseno grafico: alternativas gratuitas a Canva Pro", "cluster": "creadores", "category": "ia-creadores", "focus_keyword": "diseno grafico ia gratis", "secondary_keywords": ["ia para disenar", "alternativas canva ia", "herramientas diseno ia"], "priority": 2},
    {"topic": "Como usar IA para escribir articulos de blog optimizados para SEO", "cluster": "creadores", "category": "ia-creadores", "focus_keyword": "ia escribir articulos seo", "secondary_keywords": ["blog ia seo", "generar articulos ia", "ia para blogging"], "priority": 2},
    {"topic": "Clonar tu voz con IA: como y para que sirve (guia etica)", "cluster": "creadores", "category": "ia-creadores", "focus_keyword": "clonar voz ia", "secondary_keywords": ["voz ia clonacion", "eleven labs tutorial", "ia voz sintetica"], "priority": 3},

    # ── CLUSTER 5: Noticias y Tendencias IA (priority 3-4) ──
    {"topic": "El estado de la inteligencia artificial en 2026: tendencias que debes conocer", "cluster": "tendencias", "category": "noticias-ia", "focus_keyword": "tendencias ia 2026", "secondary_keywords": ["estado ia 2026", "futuro ia", "predicciones ia 2026"], "priority": 1},
    {"topic": "GPT-5 y el futuro de los modelos de lenguaje: que esperar en 2026", "cluster": "tendencias", "category": "noticias-ia", "focus_keyword": "gpt-5 futuro modelos lenguaje", "secondary_keywords": ["gpt-5 fecha", "openai 2026", "modelos ia futuro"], "priority": 3},
    {"topic": "IA en Latinoamerica: como la region esta adoptando la inteligencia artificial", "cluster": "tendencias", "category": "noticias-ia", "focus_keyword": "ia latinoamerica adopcion", "secondary_keywords": ["ia latam 2026", "inteligencia artificial latam", "ia colombia mexico"], "priority": 2},
    {"topic": "Regulacion de IA en el mundo: que leyes existen y como te afectan", "cluster": "tendencias", "category": "noticias-ia", "focus_keyword": "regulacion ia leyes", "secondary_keywords": ["leyes ia 2026", "regulacion inteligencia artificial", "ia regulacion europa"], "priority": 3},
    {"topic": "Los trabajos que la IA no puede reemplazar (y los que si)", "cluster": "tendencias", "category": "noticias-ia", "focus_keyword": "trabajos ia no puede reemplazar", "secondary_keywords": ["ia reemplazar trabajos", "futuro trabajo ia", "empleos ia 2026"], "priority": 2},
    {"topic": "IA open source vs IA privada: Llama, Mistral y la batalla por la IA libre", "cluster": "tendencias", "category": "noticias-ia", "focus_keyword": "ia open source vs privada", "secondary_keywords": ["llama meta ia", "mistral ia", "ia codigo abierto"], "priority": 3},
    {"topic": "Como la IA esta transformando la educacion en Latinoamerica", "cluster": "tendencias", "category": "noticias-ia", "focus_keyword": "ia educacion latinoamerica", "secondary_keywords": ["ia para estudiar", "educacion ia 2026", "ia escuelas universidades"], "priority": 3},
    {"topic": "IA y privacidad: como proteger tus datos cuando usas herramientas de IA", "cluster": "tendencias", "category": "noticias-ia", "focus_keyword": "ia privacidad datos", "secondary_keywords": ["proteger datos ia", "privacidad inteligencia artificial", "seguridad ia"], "priority": 2},

    # ── Extra articles for breadth ──
    {"topic": "Que es la inteligencia artificial generativa y por que todos hablan de ella", "cluster": "productividad", "category": "herramientas-ia", "focus_keyword": "inteligencia artificial generativa", "secondary_keywords": ["ia generativa que es", "ia generativa ejemplos", "genai 2026"], "priority": 1},
    {"topic": "ChatGPT Plus vs gratis: vale la pena pagar por la version premium", "cluster": "tutoriales", "category": "tutoriales-ia", "focus_keyword": "chatgpt plus vs gratis", "secondary_keywords": ["chatgpt premium vale la pena", "chatgpt plus precio", "chatgpt gratuito vs pago"], "priority": 1},
    {"topic": "Las 5 habilidades que necesitas para trabajar con IA en 2026", "cluster": "tendencias", "category": "noticias-ia", "focus_keyword": "habilidades trabajar con ia", "secondary_keywords": ["skills ia 2026", "aprender ia", "competencias ia"], "priority": 2},
    {"topic": "Como usar IA para planificar viajes perfectos y ahorrar dinero", "cluster": "productividad", "category": "herramientas-ia", "focus_keyword": "ia planificar viajes", "secondary_keywords": ["ia para viajar", "planificar vacaciones ia", "apps viaje ia"], "priority": 3},
    {"topic": "Notion vs Obsidian vs Roam: cual es mejor con IA en 2026", "cluster": "productividad", "category": "herramientas-ia", "focus_keyword": "notion vs obsidian ia", "secondary_keywords": ["comparativa notas ia", "mejor app notas ia", "obsidian ia plugins"], "priority": 2},
    {"topic": "Como usar IA para mejorar tu curriculum y conseguir empleo", "cluster": "productividad", "category": "herramientas-ia", "focus_keyword": "ia curriculum empleo", "secondary_keywords": ["mejorar cv ia", "ia buscar trabajo", "resume ia herramientas"], "priority": 2},
    {"topic": "n8n: la herramienta open source para automatizar todo con IA", "cluster": "negocios", "category": "ia-negocios", "focus_keyword": "n8n automatizacion ia", "secondary_keywords": ["n8n tutorial", "n8n vs zapier", "automatizar n8n ia"], "priority": 2},
    {"topic": "Como crear tu propio asistente virtual con IA personalizado", "cluster": "tutoriales", "category": "tutoriales-ia", "focus_keyword": "crear asistente virtual ia", "secondary_keywords": ["chatbot personalizado ia", "asistente ia propio", "gpts personalizados"], "priority": 2},
    {"topic": "IA para freelancers: 10 herramientas para trabajar mas rapido y ganar mas", "cluster": "negocios", "category": "ia-negocios", "focus_keyword": "ia freelancers herramientas", "secondary_keywords": ["ia para freelance", "freelancer productividad ia", "ganar dinero ia freelance"], "priority": 2},
    {"topic": "Canva con IA: todas las funciones de inteligencia artificial que debes conocer", "cluster": "creadores", "category": "ia-creadores", "focus_keyword": "canva ia funciones", "secondary_keywords": ["canva inteligencia artificial", "canva magic studio", "disenar con ia canva"], "priority": 2},
]


async def seed():
    await init_db()
    async with async_session() as session:
        for item in CONTENT_PLAN:
            plan = ContentPlan(
                topic=item["topic"],
                cluster=item["cluster"],
                category=item["category"],
                focus_keyword=item["focus_keyword"],
                secondary_keywords=json.dumps(item["secondary_keywords"]),
                priority=item["priority"],
            )
            session.add(plan)
        await session.commit()
        print(f"Seeded {len(CONTENT_PLAN)} article topics into content plan.")


if __name__ == "__main__":
    import json
    asyncio.run(seed())
