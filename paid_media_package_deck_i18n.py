"""Copy para la landing tipo deck: Paid Media Management (Meta Ads + Google Ads)."""

from __future__ import annotations


def get_paid_media_package_deck_copy(lang: str) -> dict:
    if lang not in ("es", "en"):
        lang = "es"
    return _COPY[lang]


_COPY = {
    "es": {
        "meta_title": "Paid Media Management para hotelería - DRAGONNÉ",
        "meta_description": (
            "Gestión de pauta digital en Meta Ads y Google Ads: estructura, segmentación, "
            "optimización continua y lectura periódica de resultados para sostener una operación con criterio."
        ),
        "breadcrumb_name": "Paid Media Management",
        "skip": "Saltar al contenido",
        "scroll_hint": "Sigue bajando",
        "nav_lang_en": "EN",
        "nav_lang_es": "ES",
        "nav_back_hotels": "",
        "nav_schedule_meeting": "Agendar reunión",
        "contact_title": "Hablemos",
        "contact_kicker": "Siguiente paso",
        "contact_email": "jorge@dragonne.co",
        "contact_copy": (
            "Si necesitas continuidad y control en la pauta del hotel (Meta + Google), conversemos sobre objetivo, "
            "presupuesto y cómo se vería la operación mes a mes."
        ),
        "contact_signature_name": "Jorge Flores",
        "contact_signature_role": "Head of Hospitality",
        "contact_signature_email": "jorge@dragonne.co",
        "contact_signature_avatar": "/static/team/jorge-flores.jpg",
        "contact_primary_label": "Agendar reunión",
        "contact_secondary_label": "Solicitar información",
        "contact_secondary_href": "mailto:jorge@dragonne.co?subject=Paid%20Media%20Management",
        "cta_calendar": "Agendar reunión",
        "cta_pdf": "Descargar PDF",
        "cta_contact": "Contáctanos",
        "close_secondary_label": "Escríbenos",
        "close_secondary_target": "_self",
        "floating_cta_label": "Agendar reunión",
        "floating_cta_href": "",
        "floating_cta_target": "_blank",
        "footer_note": "DRAGONNÉ · operación de pauta y optimización continua para hotelería.",
        "slides": [
            {
                "variant": "hero",
                "kicker": "Servicio",
                "title_lines": [
                    "Paid Media Management",
                    "Meta Ads + Google Ads para hotelería.",
                ],
                "lead": (
                    "Estructura, administración y optimización de campañas publicitarias con seguimiento ordenado: "
                    "segmentación clara, control operativo y lectura periódica de resultados."
                ),
            },
            {
                "variant": "light",
                "step": 1,
                "kicker": "Problema típico",
                "title": "Activar anuncios no es lo mismo que operar pauta.",
                "body": (
                    "En muchos hoteles, se prenden campañas aisladas y luego se quedan sin seguimiento. "
                    "Sin estructura, sin criterios claros, y con poca visibilidad de qué funciona y por qué."
                ),
            },
            {
                "variant": "dark",
                "step": 2,
                "kicker": "Control",
                "title": "La inversión necesita disciplina operativa.",
                "body": (
                    "El objetivo es sostener una operación de pauta bien estructurada: segmentación, medición básica, "
                    "monitoreo y ajustes continuos para aprovechar mejor el presupuesto del hotel."
                ),
            },
            {
                "variant": "light",
                "step": 3,
                "kicker": "Enfoque",
                "title_lines": [
                    "Tres frentes:",
                    "estructura, optimización y lectura.",
                ],
                "wide": True,
                "bullets": [
                    {
                        "icon": "rocket",
                        "title": "Estructura y activación",
                        "text": (
                            "Configuración inicial y estructura de campañas en Meta Ads y Google Ads con base "
                            "en objetivos comerciales."
                        ),
                    },
                    {
                        "icon": "radar",
                        "title": "Segmentación y optimización continua",
                        "text": (
                            "Audiencias, anuncios, palabras clave y distribución de presupuesto con ajustes continuos "
                            "según desempeño."
                        ),
                    },
                    {
                        "icon": "revenue",
                        "title": "Seguimiento y lectura de resultados",
                        "text": (
                            "Revisión periódica para mantener visibilidad de inversión, comportamiento y oportunidades de mejora "
                            "en el siguiente ciclo."
                        ),
                    },
                ],
            },
            {
                "variant": "dark",
                "step": 4,
                "kicker": "Alcance",
                "title": "Paid Media Management",
                "wide": True,
                "body": (
                    "Gestión de pauta en Meta Ads y Google Ads con una operación constante: "
                    "configuración inicial, definición de segmentaciones, investigación de palabras clave, "
                    "remarketing cuando aplique, optimización continua y un cierre periódico con lectura de resultados."
                ),
                "bullets": [
                    {
                        "icon": "mix",
                        "title": "Estructura de campañas",
                        "text": "Una lógica clara de objetivos, segmentación y presupuesto para sostener la operación.",
                    },
                    {
                        "icon": "users",
                        "title": "Audiencias y palabras clave",
                        "text": "Segmentaciones (ubicación, intereses, perfil) y keywords para campañas en Google Ads.",
                    },
                    {
                        "icon": "radar",
                        "title": "Monitoreo + optimización",
                        "text": "Monitoreo y optimización continua (anuncios, segmentación, keywords, presupuesto).",
                    },
                    {
                        "icon": "globe",
                        "title": "Revisión básica de tracking",
                        "text": "Pixel/eventos cuando existan, y validación básica de enlaces de destino y proceso de reserva.",
                    },
                ],
            },
            {
                "variant": "services",
                "step": 5,
                "kicker": "Quién lo lleva",
                "title_lines": [
                    "Lo gestiona un especialista",
                    "en pauta y optimización.",
                ],
                "wide": True,
                "body": (
                    "Implementación, monitoreo y optimización con criterio para estructurar inversiones digitales "
                    "orientadas a resultados y dar seguimiento operativo constante."
                ),
                "services": [
                    {"icon": "meta_brand", "label": "Meta Ads"},
                    {"icon": "google_brand", "label": "Google Ads"},
                    {"icon": "radar", "label": "Remarketing"},
                    {"icon": "revenue", "label": "Optimización"},
                ],
            },
            {
                "variant": "light",
                "step": 6,
                "kicker": "Condiciones",
                "title": "Para ejecutar bien, se necesitan accesos y una vía clara de autorización.",
                "body": (
                    "Accesos a cuentas publicitarias, página de Facebook, Instagram, Google Ads, materiales creativos disponibles "
                    "y un canal claro para revisar y aprobar campañas cuando sea necesario."
                ),
            },
            {
                "variant": "light",
                "step": 7,
                "kicker": "Cadencia",
                "title": "Orden, continuidad y un cierre periódico de resultados.",
                "body": (
                    "La pauta funciona mejor cuando se opera con una cadencia constante: seguimiento, ajustes, "
                    "y una lectura periódica que convierta métricas en decisiones."
                ),
            },
            {
                "variant": "dark",
                "step": 8,
                "kicker": "Impacto",
                "title": "Más control. Menos dispersión.",
                "body": (
                    "Una operación de pauta ordenada reduce decisiones reactivas y mejora el aprendizaje entre ciclos. "
                    "No se trata de “gastar más”, sino de ejecutar mejor."
                ),
            },
            {"variant": "lead", "kicker": "", "title": ""},
            {
                "variant": "close",
                "kicker": "Empecemos",
                "title": "Guardar en PDF o contactarnos",
            },
        ],
    },
    "en": {
        "meta_title": "Paid Media Management for Hospitality - DRAGONNÉ",
        "meta_description": (
            "Meta Ads + Google Ads management: structure, segmentation, continuous optimization and a periodic "
            "performance readout to keep the operation steady."
        ),
        "breadcrumb_name": "Paid Media Management",
        "skip": "Skip to content",
        "scroll_hint": "Keep scrolling",
        "nav_lang_en": "EN",
        "nav_lang_es": "ES",
        "nav_back_hotels": "",
        "nav_schedule_meeting": "Schedule a meeting",
        "contact_title": "Let's talk",
        "contact_kicker": "Next step",
        "contact_email": "jorge@dragonne.co",
        "contact_copy": (
            "If you need continuity and operational control across your hotel's paid media (Meta + Google), "
            "let's align on goals, budget and what the monthly operating cadence looks like."
        ),
        "contact_signature_name": "Jorge Flores",
        "contact_signature_role": "Head of Hospitality",
        "contact_signature_email": "jorge@dragonne.co",
        "contact_signature_avatar": "/static/team/jorge-flores.jpg",
        "contact_primary_label": "Schedule a meeting",
        "contact_secondary_label": "Request information",
        "contact_secondary_href": "mailto:jorge@dragonne.co?subject=Paid%20Media%20Management",
        "cta_calendar": "Schedule a meeting",
        "cta_pdf": "Download PDF",
        "cta_contact": "Contact us",
        "close_secondary_label": "Email us",
        "close_secondary_target": "_self",
        "floating_cta_label": "Schedule a meeting",
        "floating_cta_href": "",
        "floating_cta_target": "_blank",
        "footer_note": "DRAGONNÉ · paid media operations and continuous optimization for hospitality.",
        "slides": [
            {
                "variant": "hero",
                "kicker": "Service",
                "title_lines": [
                    "Paid Media Management",
                    "Meta Ads + Google Ads for hospitality.",
                ],
                "lead": (
                    "Structure, management and optimization with an operating cadence: clear segmentation, "
                    "operational control and a periodic performance readout."
                ),
            },
            {
                "variant": "light",
                "step": 1,
                "kicker": "Common issue",
                "title": "Running ads is not the same as operating paid media.",
                "body": (
                    "Many hotels launch one-off campaigns and then stop following through. "
                    "Without structure and clear criteria, performance stays unclear and budget gets wasted."
                ),
            },
            {
                "variant": "dark",
                "step": 2,
                "kicker": "Control",
                "title": "Your investment needs operational discipline.",
                "body": (
                    "The goal is continuity: a structured setup, basic tracking checks, monitoring and ongoing adjustments "
                    "to make better use of your paid media budget."
                ),
            },
            {
                "variant": "light",
                "step": 3,
                "kicker": "Approach",
                "title_lines": [
                    "Three lanes:",
                    "structure, optimization, reading.",
                ],
                "wide": True,
                "bullets": [
                    {
                        "icon": "rocket",
                        "title": "Structure and launch",
                        "text": "Initial setup and campaign structure across Meta Ads and Google Ads aligned to business goals.",
                    },
                    {
                        "icon": "radar",
                        "title": "Segmentation and continuous optimization",
                        "text": (
                            "Audiences, ads, keywords and budget allocation with weekly optimizations based on performance."
                        ),
                    },
                    {
                        "icon": "revenue",
                        "title": "Monthly readout",
                        "text": "A periodic performance review to keep visibility and improve the next cycle.",
                    },
                ],
            },
            {
                "variant": "dark",
                "step": 4,
                "kicker": "Scope",
                "title": "Paid Media Management",
                "wide": True,
                "body": (
                    "Meta Ads + Google Ads management with a steady operating cadence: initial setup, segmentation criteria, "
                    "keyword research, remarketing when applicable, continuous optimization and a periodic performance readout."
                ),
                "bullets": [
                    {
                        "icon": "mix",
                        "title": "Campaign structure",
                        "text": "A clear logic for objectives, targeting and budget allocation that keeps the work grounded.",
                    },
                    {
                        "icon": "users",
                        "title": "Audiences and keywords",
                        "text": "Segmentation plus keyword research and selection for Google Ads.",
                    },
                    {
                        "icon": "radar",
                        "title": "Monitoring + optimization",
                        "text": "Monitoring and continuous optimization (ads, targeting, keywords, budget).",
                    },
                    {
                        "icon": "globe",
                        "title": "Basic tracking checks",
                        "text": "Pixel/events when available + basic landing and booking flow validation.",
                    },
                ],
            },
            {
                "variant": "services",
                "step": 5,
                "kicker": "Owner",
                "title_lines": [
                    "Run by a specialist",
                    "in paid media optimization.",
                ],
                "wide": True,
                "body": (
                    "Implementation, monitoring and optimization with the judgment to structure digital investment "
                    "and keep an operational follow-through."
                ),
                "services": [
                    {"icon": "meta_brand", "label": "Meta Ads"},
                    {"icon": "google_brand", "label": "Google Ads"},
                    {"icon": "radar", "label": "Remarketing"},
                    {"icon": "revenue", "label": "Optimization"},
                ],
            },
            {
                "variant": "light",
                "step": 6,
                "kicker": "Requirements",
                "title": "Access + a clear approval lane.",
                "body": (
                    "Access to ad accounts, Facebook Page, Instagram profile, Google Ads account, available creative assets, "
                    "and a clear way to review and approve campaigns when needed."
                ),
            },
            {
                "variant": "light",
                "step": 7,
                "kicker": "Cadence",
                "title": "Continuity + a periodic readout.",
                "body": (
                    "Paid media works better when it runs with a steady cadence: follow-through, adjustments, "
                    "and periodic reading that turns metrics into decisions."
                ),
            },
            {
                "variant": "dark",
                "step": 8,
                "kicker": "Impact",
                "title": "More control. Less noise.",
                "body": (
                    "A structured operating cadence reduces reactive decisions and improves learning across cycles. "
                    "It's not about “spending more”—it's about executing better."
                ),
            },
            {"variant": "lead", "kicker": "", "title": ""},
            {
                "variant": "close",
                "kicker": "Next",
                "title": "Save as PDF or contact us",
            },
        ],
    },
}

