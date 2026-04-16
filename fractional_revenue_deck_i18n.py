"""Copy para la landing deck de Revenue Management fraccional."""

from __future__ import annotations


def get_fractional_revenue_deck_copy(lang: str) -> dict:
    if lang not in ("es", "en"):
        lang = "es"
    return _COPY[lang]


_COPY = {
    "es": {
        "meta_title": "Revenue Management fraccional para hoteles — DRAGONNÉ",
        "meta_description": (
            "Revenue Management fraccional para hoteles: estrategia comercial, tarifas, demanda y mezcla de canales "
            "con criterio senior, sin cargar una estructura de tiempo completo."
        ),
        "breadcrumb_name": "Revenue Management fraccional",
        "skip": "Saltar al contenido",
        "scroll_hint": "Sigue bajando",
        "nav_lang_en": "EN",
        "nav_lang_es": "ES",
        "nav_back_hotels": "Volver a Hotelería",
        "nav_schedule_meeting": "Agendar reunión",
        "contact_title": "Hablemos",
        "contact_email": "jorge@dragonne.co",
        "contact_kicker": "Siguiente paso",
        "contact_copy": (
            "Si esto hizo sentido para tu hotel, conversemos sobre alcance, ritmo de trabajo y si el modelo fraccional "
            "realmente encaja con tu propiedad."
        ),
        "contact_primary_label": "Agendar reunión",
        "contact_secondary_label": "Solicitar información",
        "contact_secondary_href": "mailto:hefzi@dragonne.co?subject=Revenue%20Management%20fraccional",
        "cta_calendar": "Agendar reunión",
        "cta_pdf": "Descargar PDF",
        "cta_contact": "Solicitar información",
        "close_primary_mode": "link",
        "close_primary_label": "Agendar reunión",
        "close_primary_target": "_blank",
        "close_secondary_label": "Hablemos",
        "close_secondary_target": "_self",
        "floating_cta_label": "Agendar reunión",
        "floating_cta_href": "",  # se sobreescribe con la URL de Cal.com en routes/consulting.py
        "floating_cta_target": "_blank",
        "footer_note": "DRAGONNÉ · criterio comercial y revenue para equipos hoteleros.",
        "contact_signature_name": "Jorge Flores",
        "contact_signature_role": "Head of Hospitality · DRAGONNÉ",
        "contact_signature_email": "jorge@dragonne.co",
        "contact_signature_avatar": "/static/team/jorge-flores.jpg",
        "slides": [
            {
                "variant": "hero",
                "kicker": "Servicio",
                "title": "Tu hotel quizá no necesita un revenue manager de tiempo completo. Pero sí necesita revenue management.",
                "lead": (
                    "Estrategia comercial, análisis y acompañamiento experto para mejorar tarifa, ocupación y rentabilidad "
                    "sin cargar una estructura de tiempo completo."
                ),
            },
            {
                "variant": "light",
                "step": 1,
                "kicker": "Realidad operativa",
                "title": "La operación se come el análisis.",
                "body": (
                    "En muchos hoteles, las decisiones comerciales se toman entre pendientes, urgencias y operación diaria. "
                    "Se revisan tarifas. Se corrigen canales sobre la marcha. Se responde a lo inmediato. "
                    "Pero no siempre hay tiempo, estructura o criterio suficiente para leer el negocio con profundidad."
                ),
            },
            {
                "variant": "dark",
                "step": 2,
                "kicker": "Rentabilidad",
                "title": "Llenar habitaciones no basta si se venden mal.",
                "body": (
                    "Ocupar no siempre significa vender bien. "
                    "Y vender bien no depende solo de tener demanda. También depende de cuándo ajustar, qué canal empujar, "
                    "qué tarifa sostener, qué comisiones aceptar y qué negocio conviene más. "
                    "Cuando eso no se gestiona con claridad, la rentabilidad se erosiona."
                ),
            },
            {
                "variant": "light",
                "step": 3,
                "kicker": "Estrategia",
                "title": "El problema no siempre es el mercado.",
                "body": (
                    "A veces el hotel sí tiene demanda. Lo que falta es estrategia. "
                    "Falta lectura comercial. Falta seguimiento. Falta disciplina para tomar mejores decisiones "
                    "sobre tarifas, canales, inventario y ritmo de reservas."
                ),
            },
            {
                "variant": "dark",
                "step": 4,
                "kicker": "Modelo",
                "title_lines": [
                    "No todos los hoteles necesitan",
                    "un full-time interno.",
                ],
                "body": (
                    "Pero muchos sí necesitan dirección comercial experta. "
                    "Para un hotel independiente, boutique o un grupo pequeño, contratar una posición interna de tiempo completo "
                    "no siempre tiene sentido. Eso no elimina la necesidad. Solo cambia la forma más inteligente de resolverla."
                ),
                "body_compact": True,
            },
            {
                "variant": "light",
                "step": 5,
                "kicker": "Revenue Management fraccional",
                "title": "Ahí entra el Revenue Management fraccional.",
                "wide": True,
                "body": (
                    "Un modelo flexible para acceder a estrategia, análisis y seguimiento comercial sin sumar una estructura fija completa. "
                    "No se trata de tercerizar tarifas. Se trata de incorporar criterio experto para vender mejor, "
                    "con más claridad y mejor rentabilidad."
                ),
                "bullets": [
                    {
                        "icon": "radar",
                        "title": "Estrategia tarifaria",
                        "text": (
                            "Ajustes y recomendaciones tarifarias con base en demanda, ocupación, competencia, "
                            "ventanas de reserva y ritmo comercial."
                        ),
                    },
                    {
                        "icon": "mix",
                        "title": "Pronóstico y canales",
                        "text": (
                            "Lectura de históricos, tendencias y comportamiento de reservas para anticipar escenarios "
                            "y buscar una mezcla más sana entre OTAs, canal directo y otros canales."
                        ),
                    },
                    {
                        "icon": "revenue",
                        "title": "KPIs y competencia",
                        "text": (
                            "ADR, ocupación, RevPAR, pickup, ritmo de reservas, comisiones, mezcla de negocio y set competitivo "
                            "leídos con contexto, no como cifras aisladas."
                        ),
                    },
                    {
                        "icon": "users",
                        "title": "Acompañamiento estratégico",
                        "text": (
                            "Seguimiento real para interpretar la información, sostener mejores decisiones comerciales "
                            "y evitar que revenue se quede solo en un reporte."
                        ),
                    },
                ],
            },
            {
                "variant": "dark",
                "step": 6,
                "kicker": "Impacto",
                "title": "Más claridad comercial. Menos improvisación.",
                "body": (
                    "Este servicio busca ayudar al hotel a mejorar tarifa promedio, ocupación sana, RevPAR, rentabilidad, "
                    "mix de canales, venta directa y visibilidad real del negocio. "
                    "Porque el objetivo no es solo vender más. Es vender mejor."
                ),
                "chips": [
                    "ADR",
                    "Ocupación sana",
                    "RevPAR",
                    "Rentabilidad",
                ],
            },
            {
                "variant": "light",
                "step": 7,
                "kicker": "Forma de trabajo",
                "title": "No es solo entregar un documento.",
                "body": (
                    "Se trabaja con lectura periódica del desempeño, análisis de información, recomendaciones accionables y seguimiento continuo. "
                    "La intención no es llenar al hotel de teoría. Es acompañarlo con criterio, contexto y foco comercial, "
                    "en lenguaje de hotel y con decisiones que sí puedan aterrizarse."
                ),
            },
            {
                "variant": "dark",
                "step": 8,
                "kicker": "Eficiencia",
                "title": "No todos los hoteles necesitan más nómina. Muchos necesitan mejores decisiones.",
                "body": (
                    "Cuando la estructura fija no se justifica, el modelo fraccional tiene sentido. "
                    "En lugar de absorber la carga completa de una contratación interna, el hotel accede a experiencia especializada "
                    "en un formato más flexible: menos costo fijo, más criterio y una inversión más enfocada en resultados."
                ),
            },
            {
                "variant": "services",
                "step": 9,
                "kicker": "Perfil ideal",
                "title": "Tiene sentido para hoteles que sí necesitan revenue, aunque no requieran una estructura completa.",
                "wide": True,
                "body": (
                    "Especialmente para propiedades con operación en marcha, poco tiempo para analizar, "
                    "sin un revenue manager interno sólido y con necesidad real de mejorar ocupación, ADR y rentabilidad "
                    "sin aumentar demasiado su estructura fija."
                ),
                "services": [
                    {"icon": "hotel", "label": "Hoteles independientes"},
                    {"icon": "boutique", "label": "Boutique y grupos pequeños"},
                    {"icon": "operators", "label": "Operadoras y comercializadoras"},
                    {"icon": "management", "label": "Gerencia y dirección general"},
                ],
            },
            {"variant": "lead", "kicker": "", "title": ""},
            {
                "variant": "close",
                "kicker": "Conversación",
                "title": "Si tu hotel no necesita una estructura completa, pero sí necesita Revenue Management, esto puede tener mucho sentido.",
            },
        ],
    },
    "en": {
        "meta_title": "Fractional Revenue Management for Hotels — DRAGONNÉ",
        "meta_description": (
            "Fractional revenue management for independent and boutique hotels: pricing, demand, channel mix, ADR and "
            "RevPAR with senior judgment—without a full-time revenue manager hire."
        ),
        "breadcrumb_name": "Fractional Revenue Management",
        "skip": "Skip to content",
        "scroll_hint": "Keep scrolling",
        "nav_lang_en": "EN",
        "nav_lang_es": "ES",
        "nav_back_hotels": "Back to Hospitality",
        "nav_schedule_meeting": "Schedule a meeting",
        "contact_title": "Let's talk",
        "contact_email": "hefzi@dragonne.co",
        "cta_calendar": "Book a meeting",
        "cta_pdf": "Download PDF",
        "cta_contact": "Request information",
        "close_primary_mode": "link",
        "close_primary_label": "Book a meeting",
        "close_primary_target": "_blank",
        "close_secondary_label": "Request information",
        "close_secondary_target": "_self",
        "floating_cta_label": "Book a meeting",
        "floating_cta_href": "",  # overridden with Cal.com in routes/consulting.py
        "floating_cta_target": "_blank",
        "footer_note": "DRAGONNÉ · commercial judgment and revenue support for hotel teams.",
        "slides": [
            {
                "variant": "hero",
                "kicker": "Fractional Revenue Management for Hotels",
                "title": "Your hotel may not need a full-time revenue manager. But it does need revenue management.",
                "lead": (
                    "Not every hotel has the scale, structure, or moment to absorb a full-time position. "
                    "That does not remove the need for pricing judgment, demand reading, commercial discipline, and timely decisions."
                ),
            },
            {
                "variant": "light",
                "step": 1,
                "kicker": "The problem",
                "title": "Many hotels are not losing only on price.",
                "body": (
                    "They lose because revenue is reviewed late, without method, or in between operational gaps. "
                    "Management handles guests, staff, payments, OTAs, and daily issues; deep analysis on pickup, booking pace, "
                    "windows, channels, and competitive pressure rarely gets the attention it deserves."
                ),
            },
            {
                "variant": "dark",
                "step": 2,
                "kicker": "The common mistake",
                "title": "Full rooms are not enough if they are sold the wrong way.",
                "body": (
                    "Healthy occupancy can hide weak rate, excessive commission exposure, poor timing, "
                    "and a channel mix that erodes profit. Selling more nights does not always mean selling better."
                ),
            },
            {
                "variant": "light",
                "step": 3,
                "kicker": "Structure",
                "title": "There are hotels where a full-time hire still does not make sense.",
                "body": (
                    "Because of size, stage, or complexity, a fixed senior headcount is not always the right move. "
                    "But operating without revenue management is not either. The gap gets filled with instinct, urgency, or isolated decisions."
                ),
            },
            {
                "variant": "dark",
                "step": 4,
                "kicker": "The model",
                "title_lines": [
                    "More commercial judgment.",
                    "Less improvisation.",
                ],
                "body": (
                    "A fractional model puts experience, analysis, and follow-through on the table without carrying a full structure. "
                    "It is not cheap outsourcing or abstract consulting: it is smart access to specialized commercial direction."
                ),
                "body_compact": True,
            },
            {
                "variant": "light",
                "step": 5,
                "kicker": "What the service does",
                "title": "Revenue management with a real hotel rhythm.",
                "wide": True,
                "body": (
                    "The point is not to send a pretty file once a month. It is to read the business, "
                    "adjust with judgment, and sustain better decisions across pricing, demand, distribution, and commercial performance."
                ),
                "bullets": [
                    {
                        "icon": "radar",
                        "title": "Dynamic pricing",
                        "text": (
                            "Periodic rate review based on demand, occupancy, comp set, booking windows, pickup, "
                            "and commercial pace. Rate stops moving by inertia."
                        ),
                    },
                    {
                        "icon": "mix",
                        "title": "Demand and channels",
                        "text": (
                            "Forecasting, historical reading, and channel mix analysis across OTAs, direct, and other sources "
                            "to improve timing and reduce commission dependence."
                        ),
                    },
                    {
                        "icon": "revenue",
                        "title": "KPIs that matter",
                        "text": (
                            "ADR, occupancy, RevPAR, pickup, pace, business mix, and profitability read in context, "
                            "not just reported as isolated numbers."
                        ),
                    },
                    {
                        "icon": "users",
                        "title": "Strategic follow-through",
                        "text": (
                            "Ongoing work with management and team to interpret signals, correct course, and sustain commercial discipline "
                            "without leaving revenue isolated from operations."
                        ),
                    },
                ],
            },
            {
                "variant": "dark",
                "step": 6,
                "kicker": "What it aims to improve",
                "title": "A better read on the business. Better decisions for the hotel.",
                "body": (
                    "The objective is not to move a rate for the sake of it. It is to push ADR when the market allows, "
                    "protect healthy occupancy, improve RevPAR, strengthen direct sales, clean up the channel mix, and restore commercial clarity."
                ),
                "chips": ["ADR", "Healthy occupancy", "RevPAR", "Channel mix", "Direct sales", "Profitability"],
            },
            {
                "variant": "light",
                "step": 7,
                "kicker": "How we work",
                "title": "Continuous follow-through, not a one-off opinion.",
                "body": (
                    "We work through recurring sessions, data review, actionable recommendations, and real follow-up. "
                    "The point is not to deliver more reports. It is to help the hotel understand what is happening and why acting now matters."
                ),
            },
            {
                "variant": "dark",
                "step": 8,
                "kicker": "Economic logic",
                "title": "Turning fixed structure into expert support is also a smart decision.",
                "body": (
                    "For many independent hotels, boutiques, or small groups, a fractional model gives access to senior experience "
                    "without absorbing the full cost of an internal hire. More flexibility, more judgment, and a better-aligned investment."
                ),
            },
            {
                "variant": "services",
                "step": 9,
                "kicker": "Fit",
                "title": "Built for hotels that do need revenue, even if they do not need a full structure.",
                "wide": True,
                "body": (
                    "It usually fits independent properties, boutique hotels, small groups, operators, or teams "
                    "where commercial direction exists but there is no strong internal revenue figure today."
                ),
                "services": [
                    {"icon": "globe", "label": "Independent hotels"},
                    {"icon": "users", "label": "Boutique and small groups"},
                    {"icon": "mix", "label": "Operators and marketers"},
                    {"icon": "revenue", "label": "General management"},
                ],
            },
            {"variant": "lead", "kicker": "", "title": ""},
            {
                "variant": "close",
                "kicker": "Closing",
                "title": "If your hotel does not need a full structure, but it does need commercial strategy, this service may fit.",
            },
        ],
    },
}
