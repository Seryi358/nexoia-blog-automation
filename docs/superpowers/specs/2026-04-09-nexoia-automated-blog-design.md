# NexoIA - Automated AI Blog Design Spec

## Overview
Automated Spanish-language blog about AI tools and productivity, targeting LATAM audience. Generates income via Google AdSense through high-quality, SEO-optimized content published automatically 3x/week.

## Brand
- **Name:** NexoIA
- **Tagline:** "Tu conexion con la Inteligencia Artificial"
- **Domain:** nexoia.com (primary) | iaproductiva.com, pulsoia.com (alternates)
- **Language:** Spanish (LATAM focus, Colombia primary)

## Color Palette
- Primary: #1E40AF (Deep Blue)
- Secondary: #7C3AED (Violet)
- Accent: #06B6D4 (Cyan)
- Background: #F0F4FF (Blue-White)
- Cards: #FFFFFF
- Text: #111827 (Near-Black)
- Muted: #6B7280

## Architecture

### WordPress Blog (Hostinger)
- Theme: Astra (free) with child theme
- SEO: Rank Math (free)
- Cache: LiteSpeed Cache (Hostinger native)
- Pages: Home, About, Contact, Privacy Policy, Terms of Service
- Categories: 5 content clusters
- SSL: Let's Encrypt (Hostinger)

### Automation Engine (EasyPanel/VPS)
- Framework: FastAPI (Python 3.12)
- AI Content: OpenAI GPT-4o
- AI Images: KIE AI Nano Banana 2
- Scheduler: APScheduler (Mon/Wed/Fri)
- Database: SQLite (article tracking)
- Publishing: WordPress REST API
- Port: 8001

## Content Strategy
5 topical authority clusters, 3 articles/week, 1800-2500 words each.
Target: 20 seed articles before AdSense application.

### Clusters
1. Herramientas IA para Productividad (8-10 articles)
2. IA para Negocios y Emprendedores (8-10 articles)
3. Tutoriales IA Paso a Paso (8-10 articles)
4. IA para Creadores de Contenido (6-8 articles)
5. Noticias y Tendencias IA 2026 (5-7 articles)

## Legal Compliance
- Privacy Policy: Colombian Law 1581/2012 (Habeas Data)
- Cookie consent banner
- Terms of service
- GDPR-compatible (for EU visitors)

## AdSense Requirements
- 20+ quality articles before application
- Essential pages (Privacy, Terms, About, Contact)
- Mobile-friendly, fast loading
- Clear navigation and categories
- No thin/AI-looking content
