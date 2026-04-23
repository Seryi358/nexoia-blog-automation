"""Seed the content plan database with diverse, non-overlapping topics organized by clusters.

Idempotent: safe to re-run. Uses SQLite `INSERT OR IGNORE` via the composite
UNIQUE(topic, focus_keyword) constraint defined in app.database.
"""
import asyncio
import json

from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.database import (
    init_db,
    async_session,
    dedupe_content_plan,
    ContentPlan,
)


CONTENT_PLAN = [
    # CLUSTER 1: Herramientas IA para Productividad (12 topics)
    {"topic": "Las 15 mejores herramientas de IA para productividad en 2026 (ranking actualizado)", "cluster": "productividad", "category": "herramientas-ia", "focus_keyword": "herramientas ia productividad 2026", "secondary_keywords": ["apps ia productividad", "software ia trabajo", "ranking herramientas ia"], "priority": 1},
    {"topic": "ChatGPT vs Claude vs Gemini vs Grok: comparativa honesta para trabajo diario", "cluster": "productividad", "category": "herramientas-ia", "focus_keyword": "chatgpt vs claude vs gemini vs grok", "secondary_keywords": ["comparativa ia 2026", "mejor chatbot ia", "ia para trabajo"], "priority": 1},
    {"topic": "Notion AI 3.0: como usarlo para gestionar proyectos, equipos y vida personal", "cluster": "productividad", "category": "herramientas-ia", "focus_keyword": "notion ai 3 como usar", "secondary_keywords": ["notion ia tutorial", "notion ia proyectos", "organizar con ia"], "priority": 2},
    {"topic": "Microsoft Copilot 365: la guia completa para dominar Word, Excel, Outlook y Teams", "cluster": "productividad", "category": "herramientas-ia", "focus_keyword": "microsoft copilot 365 guia", "secondary_keywords": ["copilot office", "copilot excel word", "ia microsoft"], "priority": 2},
    {"topic": "7 herramientas de IA gratuitas que reemplazan software de $500+ al mes", "cluster": "productividad", "category": "herramientas-ia", "focus_keyword": "herramientas ia gratis alternativas", "secondary_keywords": ["ia gratuita potente", "software ia gratis 2026", "apps ia sin pagar"], "priority": 1},
    {"topic": "Superhuman, Shortwave y Mailtag: cual gestor de email con IA vale la pena en 2026", "cluster": "productividad", "category": "herramientas-ia", "focus_keyword": "superhuman vs shortwave mailtag", "secondary_keywords": ["ia para correos", "gestor email ia", "mejor email ia"], "priority": 2},
    {"topic": "Extensiones Chrome con IA imprescindibles 2026 (probadas durante 3 meses)", "cluster": "productividad", "category": "herramientas-ia", "focus_keyword": "extensiones chrome ia 2026", "secondary_keywords": ["plugins chrome ia", "extensiones navegador ia", "chrome productividad ia"], "priority": 2},
    {"topic": "Fireflies vs Otter vs Granola: cual tomador de notas con IA elegir en 2026", "cluster": "productividad", "category": "herramientas-ia", "focus_keyword": "fireflies vs otter vs granola", "secondary_keywords": ["transcribir reuniones ia", "notas reuniones ia", "acta automatica"], "priority": 2},
    {"topic": "Perplexity, You.com y Phind: el fin de Google? Comparativa de buscadores con IA", "cluster": "productividad", "category": "herramientas-ia", "focus_keyword": "perplexity you phind comparativa", "secondary_keywords": ["buscador ia", "alternativas google ia", "buscar con ia"], "priority": 1},
    {"topic": "Las 10 mejores apps de IA para Android e iPhone en 2026 (gratis y de pago)", "cluster": "productividad", "category": "herramientas-ia", "focus_keyword": "mejores apps ia celular 2026", "secondary_keywords": ["aplicaciones ia movil", "apps ia android", "ia para iphone"], "priority": 1},
    {"topic": "Arc Search, Dia Browser y el futuro de la navegacion con IA: que probe en 2026", "cluster": "productividad", "category": "herramientas-ia", "focus_keyword": "arc search dia browser ia", "secondary_keywords": ["navegador ia 2026", "browser inteligencia artificial", "arc browser review"], "priority": 3},
    {"topic": "Como usar IA para llevar tu curriculum al siguiente nivel y conseguir entrevistas", "cluster": "productividad", "category": "herramientas-ia", "focus_keyword": "ia curriculum entrevistas", "secondary_keywords": ["mejorar cv ia", "ia buscar trabajo", "resume ia 2026"], "priority": 2},

    # CLUSTER 2: IA para Negocios y Emprendedores (12 topics)
    {"topic": "Como las pymes colombianas estan usando IA para triplicar ventas en 2026", "cluster": "negocios", "category": "ia-negocios", "focus_keyword": "pymes ia colombia ventas", "secondary_keywords": ["ia pymes colombia", "aumentar ventas ia", "negocios ia latam"], "priority": 2},
    {"topic": "Make vs Zapier vs n8n 2026: cual elegir para automatizar tu negocio con IA", "cluster": "negocios", "category": "ia-negocios", "focus_keyword": "make vs zapier vs n8n 2026", "secondary_keywords": ["automatizar negocio no-code", "zapier make ia", "n8n tutorial"], "priority": 2},
    {"topic": "Chatbot de WhatsApp con IA en 30 minutos (y cero codigo): paso a paso", "cluster": "negocios", "category": "ia-negocios", "focus_keyword": "chatbot whatsapp ia sin codigo", "secondary_keywords": ["crear chatbot ia", "chatbot whatsapp business", "ia atencion cliente"], "priority": 2},
    {"topic": "IA para ecommerce 2026: 8 tacticas comprobadas para aumentar conversion 30%", "cluster": "negocios", "category": "ia-negocios", "focus_keyword": "ia ecommerce conversion 2026", "secondary_keywords": ["ia tienda online", "conversion ia", "ecommerce ia latam"], "priority": 3},
    {"topic": "Como escribir propuestas comerciales con IA que cierran 4 de cada 10 ventas", "cluster": "negocios", "category": "ia-negocios", "focus_keyword": "propuestas comerciales ia cerrar ventas", "secondary_keywords": ["ia ventas b2b", "escribir propuestas ia", "chatgpt negocios"], "priority": 3},
    {"topic": "Analiza 10.000 filas de Excel en 5 minutos con IA sin saber programar", "cluster": "negocios", "category": "ia-negocios", "focus_keyword": "analizar excel con ia", "secondary_keywords": ["analisis datos ia facil", "excel ia tutorial", "data analysis sin codigo"], "priority": 2},
    {"topic": "Roadmap 90 dias para implementar IA en tu empresa (sin quemar plata)", "cluster": "negocios", "category": "ia-negocios", "focus_keyword": "implementar ia empresa 90 dias", "secondary_keywords": ["ia para empresas", "adoptar ia negocio", "estrategia ia empresarial"], "priority": 2},
    {"topic": "Contabilidad con IA: como Alegra, Siigo y otras suites usan IA en 2026", "cluster": "negocios", "category": "ia-negocios", "focus_keyword": "contabilidad ia alegra siigo", "secondary_keywords": ["facturacion automatica ia", "ia contadores latam", "automatizar contabilidad"], "priority": 3},
    {"topic": "Investigacion de mercado con IA: como analizar competencia como un consultor McKinsey", "cluster": "negocios", "category": "ia-negocios", "focus_keyword": "investigacion mercado ia", "secondary_keywords": ["analisis competencia ia", "mckinsey ia", "ia market research"], "priority": 3},
    {"topic": "Agentes de IA para negocios: que son, como usarlos y los 5 casos que ya funcionan", "cluster": "negocios", "category": "ia-negocios", "focus_keyword": "agentes ia casos de uso 2026", "secondary_keywords": ["ai agents 2026", "agentes inteligencia artificial", "ia autonoma negocios"], "priority": 1},
    {"topic": "n8n self-hosted para automatizar con IA: la guia que te ahorra $200/mes de Zapier", "cluster": "negocios", "category": "ia-negocios", "focus_keyword": "n8n self-hosted ia", "secondary_keywords": ["n8n ia tutorial", "alternativa zapier gratis", "automatizar n8n"], "priority": 2},
    {"topic": "IA para freelancers: 10 herramientas que multiplican tu hora facturable en 2026", "cluster": "negocios", "category": "ia-negocios", "focus_keyword": "ia freelancers productividad 2026", "secondary_keywords": ["freelance ia", "ganar dinero ia freelance", "ia trabajo independiente"], "priority": 2},

    # CLUSTER 3: Tutoriales IA Paso a Paso (12 topics)
    {"topic": "Tutorial ChatGPT desde cero: domina prompts avanzados en una tarde", "cluster": "tutoriales", "category": "tutoriales-ia", "focus_keyword": "tutorial chatgpt desde cero 2026", "secondary_keywords": ["como usar chatgpt", "chatgpt principiantes", "prompts avanzados"], "priority": 1},
    {"topic": "Prompt engineering 2026: el framework CRAFT que multiplica la calidad de respuestas", "cluster": "tutoriales", "category": "tutoriales-ia", "focus_keyword": "prompt engineering framework craft", "secondary_keywords": ["escribir prompts efectivos", "mejores prompts ia", "craft framework"], "priority": 1},
    {"topic": "Midjourney v7 tutorial: parametros secretos, estilos y 50 prompts probados", "cluster": "tutoriales", "category": "tutoriales-ia", "focus_keyword": "midjourney v7 tutorial 2026", "secondary_keywords": ["midjourney como usar", "crear imagenes ia", "midjourney prompts"], "priority": 1},
    {"topic": "Claude Sonnet 4.6 y Opus 4.7 de Anthropic: guia completa con 20 casos reales", "cluster": "tutoriales", "category": "tutoriales-ia", "focus_keyword": "claude sonnet 4 opus guia", "secondary_keywords": ["claude anthropic tutorial", "claude vs chatgpt", "claude 4 casos"], "priority": 1},
    {"topic": "DALL-E 3 vs Nano Banana 2 vs Imagen 4: cual generador de imagenes es mejor en 2026", "cluster": "tutoriales", "category": "tutoriales-ia", "focus_keyword": "dalle 3 vs nano banana 2 vs imagen 4", "secondary_keywords": ["generador imagenes ia 2026", "dall-e 3 tutorial", "nano banana vs dalle"], "priority": 2},
    {"topic": "Gemini 3 Pro y Gemini 3 Ultra: como usarlos para trabajo real (no solo chat)", "cluster": "tutoriales", "category": "tutoriales-ia", "focus_keyword": "gemini 3 pro ultra tutorial", "secondary_keywords": ["gemini 3 espanol", "google gemini guia", "gemini ia 2026"], "priority": 1},
    {"topic": "Cursor AI vs Windsurf vs Cline: cual editor con IA para programar en 2026", "cluster": "tutoriales", "category": "tutoriales-ia", "focus_keyword": "cursor vs windsurf vs cline", "secondary_keywords": ["cursor editor ia", "windsurf ide", "programar con ia"], "priority": 2},
    {"topic": "Sora 2 y Runway Gen-4: como crear videos profesionales con IA desde cero", "cluster": "tutoriales", "category": "tutoriales-ia", "focus_keyword": "sora 2 runway gen-4 videos ia", "secondary_keywords": ["generar videos ia 2026", "sora openai tutorial", "ia video profesional"], "priority": 2},
    {"topic": "Make 2.0 con IA integrada: el tutorial que convierte Excel en un CRM automatico", "cluster": "tutoriales", "category": "tutoriales-ia", "focus_keyword": "make 2 ia excel crm", "secondary_keywords": ["automatizar make", "crm ia automatico", "no-code automatizacion"], "priority": 2},
    {"topic": "Como aprender ingles (o cualquier idioma) en 3 meses usando IA", "cluster": "tutoriales", "category": "tutoriales-ia", "focus_keyword": "aprender ingles con ia 3 meses", "secondary_keywords": ["ia idiomas 2026", "apps idiomas ia", "duolingo vs ia"], "priority": 2},
    {"topic": "OpenAI Assistants API: construye tu propio ChatGPT personalizado en 1 hora", "cluster": "tutoriales", "category": "tutoriales-ia", "focus_keyword": "openai assistants api tutorial", "secondary_keywords": ["crear asistente ia propio", "gpts personalizados", "chatbot personalizado"], "priority": 2},
    {"topic": "Suno v5 y Udio: como producir una cancion con IA que suena como un hit profesional", "cluster": "tutoriales", "category": "tutoriales-ia", "focus_keyword": "suno v5 udio musica ia", "secondary_keywords": ["generar musica ia 2026", "crear cancion ia", "suno tutorial"], "priority": 3},

    # CLUSTER 4: IA para Creadores de Contenido (10 topics)
    {"topic": "Estrategia de contenido con IA para Instagram 2026: plantilla replicable de 4 semanas", "cluster": "creadores", "category": "ia-creadores", "focus_keyword": "estrategia contenido instagram ia 2026", "secondary_keywords": ["ia instagram estrategia", "contenido instagram ia", "plantilla instagram"], "priority": 2},
    {"topic": "Photoshop vs Generative Fill de Firefly vs Topaz: que editor de foto con IA comprar", "cluster": "creadores", "category": "ia-creadores", "focus_keyword": "photoshop firefly topaz ia fotos", "secondary_keywords": ["editor fotos ia 2026", "ia fotografos", "retoque fotos ia"], "priority": 2},
    {"topic": "Podcast con IA: de la idea al audio publicado en Spotify en un dia", "cluster": "creadores", "category": "ia-creadores", "focus_keyword": "crear podcast con ia un dia", "secondary_keywords": ["podcast ia herramientas", "editar podcast ia", "ia podcasters"], "priority": 3},
    {"topic": "YouTube con IA: guiones, thumbnails, edicion y SEO (mi workflow completo)", "cluster": "creadores", "category": "ia-creadores", "focus_keyword": "workflow youtube con ia 2026", "secondary_keywords": ["youtube ia herramientas", "thumbnails ia", "guiones youtube"], "priority": 2},
    {"topic": "Como escribir un libro con IA sin que se note: el metodo Brandon Sanderson + Claude", "cluster": "creadores", "category": "ia-creadores", "focus_keyword": "escribir libro ia metodo sanderson", "secondary_keywords": ["ia escritores", "chatgpt libro", "claude escritura creativa"], "priority": 3},
    {"topic": "Suno, Udio, Riffusion: que plataforma musical con IA elegir si eres productor o compositor", "cluster": "creadores", "category": "ia-creadores", "focus_keyword": "suno udio riffusion musica ia", "secondary_keywords": ["generar musica ia", "ia musicos", "crear canciones ia"], "priority": 3},
    {"topic": "Gamma, Tome y Beautiful.ai: cual creador de presentaciones con IA te hace ahorrar 5 horas", "cluster": "creadores", "category": "ia-creadores", "focus_keyword": "gamma tome beautiful ai presentaciones", "secondary_keywords": ["presentaciones ia 2026", "slides ia herramientas", "gamma ai tutorial"], "priority": 2},
    {"topic": "Disenar como un pro sin saber Illustrator: Canva Magic Studio, Ideogram y Recraft", "cluster": "creadores", "category": "ia-creadores", "focus_keyword": "canva ideogram recraft diseno ia", "secondary_keywords": ["diseno grafico ia gratis", "alternativas canva", "herramientas diseno ia"], "priority": 2},
    {"topic": "Escribe articulos de blog que Google ama con IA (el metodo E-E-A-T 2026)", "cluster": "creadores", "category": "ia-creadores", "focus_keyword": "ia articulos blog eeat 2026", "secondary_keywords": ["blog ia seo", "eeat google", "ia para blogging"], "priority": 2},
    {"topic": "ElevenLabs v3 y clonacion de voz: guia, casos legales y como no meterte en problemas", "cluster": "creadores", "category": "ia-creadores", "focus_keyword": "elevenlabs v3 clonar voz legal", "secondary_keywords": ["voz ia clonacion", "elevenlabs tutorial", "ia voz sintetica"], "priority": 3},

    # CLUSTER 5: Noticias y Tendencias IA 2026 (8 topics)
    {"topic": "El estado de la IA en 2026: 12 datos que todo lider de empresa debe conocer", "cluster": "tendencias", "category": "noticias-ia", "focus_keyword": "estado ia 2026 datos lideres", "secondary_keywords": ["tendencias ia 2026", "estadisticas ia", "futuro ia"], "priority": 1},
    {"topic": "GPT-5 y Gemini 4: que sabemos, fechas rumoreadas y que cambiara en 2027", "cluster": "tendencias", "category": "noticias-ia", "focus_keyword": "gpt 5 gemini 4 fechas 2027", "secondary_keywords": ["gpt-5 fecha", "openai 2027", "modelos ia futuro"], "priority": 3},
    {"topic": "IA en Latinoamerica 2026: ranking de paises, inversion y casos de adopcion", "cluster": "tendencias", "category": "noticias-ia", "focus_keyword": "ia latinoamerica ranking 2026", "secondary_keywords": ["ia latam 2026", "ia colombia mexico argentina", "adopcion ia region"], "priority": 2},
    {"topic": "EU AI Act y regulacion en Latam: lo que tu empresa debe hacer antes de 2027", "cluster": "tendencias", "category": "noticias-ia", "focus_keyword": "eu ai act regulacion latam 2027", "secondary_keywords": ["leyes ia 2026", "regulacion inteligencia artificial", "ia europa"], "priority": 3},
    {"topic": "Los 7 trabajos que la IA ya reemplazo (y los 5 que jamas podra)", "cluster": "tendencias", "category": "noticias-ia", "focus_keyword": "trabajos reemplazados por ia 2026", "secondary_keywords": ["ia reemplazar trabajos", "futuro trabajo ia", "empleos ia"], "priority": 2},
    {"topic": "Llama 4, Mistral Large y DeepSeek V4: el estado del open source vs OpenAI en 2026", "cluster": "tendencias", "category": "noticias-ia", "focus_keyword": "llama 4 mistral deepseek open source", "secondary_keywords": ["llama meta ia", "ia codigo abierto", "open source vs openai"], "priority": 3},
    {"topic": "IA y educacion en Latinoamerica: que paises, que programas y resultados 2026", "cluster": "tendencias", "category": "noticias-ia", "focus_keyword": "ia educacion latinoamerica 2026", "secondary_keywords": ["ia para estudiar", "educacion ia", "ia escuelas universidades"], "priority": 3},
    {"topic": "Privacidad y IA 2026: los 10 errores que estan exponiendo tus datos ahora mismo", "cluster": "tendencias", "category": "noticias-ia", "focus_keyword": "ia privacidad datos errores 2026", "secondary_keywords": ["proteger datos ia", "privacidad inteligencia artificial", "seguridad ia"], "priority": 2},

    # CLUSTER 6: IA Generativa Fundamentos (6 topics)
    {"topic": "Que es la IA generativa y como funciona por dentro (explicado sin matematicas)", "cluster": "fundamentos", "category": "herramientas-ia", "focus_keyword": "ia generativa como funciona", "secondary_keywords": ["ia generativa que es", "ia generativa ejemplos", "genai 2026"], "priority": 1},
    {"topic": "ChatGPT Plus, Team, Pro y Enterprise 2026: cual plan vale la pena y para quien", "cluster": "fundamentos", "category": "tutoriales-ia", "focus_keyword": "chatgpt plus team pro enterprise 2026", "secondary_keywords": ["chatgpt premium vale pena", "chatgpt plus precio", "chatgpt planes comparativa"], "priority": 1},
    {"topic": "Las 5 habilidades imprescindibles para trabajar con IA que no son prompting", "cluster": "fundamentos", "category": "noticias-ia", "focus_keyword": "habilidades trabajar con ia 2026", "secondary_keywords": ["skills ia 2026", "aprender ia", "competencias ia"], "priority": 2},
    {"topic": "IA para planificar vacaciones de lujo gastando como mochilero (prompts reales)", "cluster": "fundamentos", "category": "herramientas-ia", "focus_keyword": "ia planificar viajes mochilero lujo", "secondary_keywords": ["ia para viajar", "planificar vacaciones ia", "apps viaje ia"], "priority": 3},
    {"topic": "Obsidian vs Notion vs Logseq con IA: la guerra de los segundos cerebros en 2026", "cluster": "fundamentos", "category": "herramientas-ia", "focus_keyword": "obsidian notion logseq ia segundo cerebro", "secondary_keywords": ["comparativa notas ia", "mejor app notas ia", "obsidian ia plugins"], "priority": 2},
    {"topic": "RAG, fine-tuning o prompting: cual tecnica usar segun tu caso (con ejemplos)", "cluster": "fundamentos", "category": "tutoriales-ia", "focus_keyword": "rag fine tuning prompting cual usar", "secondary_keywords": ["retrieval augmented generation", "fine tuning ia", "ia empresas tecnicas"], "priority": 3},
]


async def seed() -> int:
    """Seed the content plan idempotently. Returns number of rows inserted."""
    await init_db()
    removed = await dedupe_content_plan()
    if removed:
        print(f"Dedupe: removed {removed} duplicate rows from content_plan")

    inserted = 0
    async with async_session() as session:
        for item in CONTENT_PLAN:
            stmt = (
                sqlite_insert(ContentPlan)
                .values(
                    topic=item["topic"],
                    cluster=item["cluster"],
                    category=item["category"],
                    focus_keyword=item["focus_keyword"],
                    secondary_keywords=json.dumps(item["secondary_keywords"]),
                    priority=item["priority"],
                )
                .on_conflict_do_nothing(index_elements=["topic", "focus_keyword"])
            )
            result = await session.execute(stmt)
            if result.rowcount:
                inserted += 1
        await session.commit()

    print(f"Seed complete: {inserted} new topics added ({len(CONTENT_PLAN) - inserted} already present).")
    return inserted


if __name__ == "__main__":
    asyncio.run(seed())
