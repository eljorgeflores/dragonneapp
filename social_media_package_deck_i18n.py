"""Copy para la landing tipo deck: Social Media Management & Content Creation (página independiente)."""

from __future__ import annotations


def get_social_media_package_deck_copy(lang: str) -> dict:
    if lang not in ("es", "en"):
        lang = "es"
    return _COPY[lang]


_COPY = {
    "es": {
        "meta_title": "Servicio mensual de redes para hospitalidad - DRAGONNÉ",
        "meta_description": (
            "Estrategia y calendarización, publicación en hasta tres redes, reglas de atención y automatización para dirigir a reserva o acción, "
            "reels, carruseles y posts en volumen fijo, idea y copy alineados a la marca, presentación de resultados."
        ),
        "breadcrumb_name": "Gestión de redes sociales",
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
            "Si esto hizo sentido para tu hotel o restaurante, conversemos sobre alcance, ritmo de trabajo y si el servicio de "
            "gestión de redes realmente encaja con tu operación."
        ),
        "contact_signature_name": "Jorge Flores",
        "contact_signature_role": "Head of Hospitality",
        "contact_signature_email": "jorge@dragonne.co",
        "contact_signature_avatar": "/static/team/jorge-flores.jpg",
        "contact_primary_label": "Agendar reunión",
        "contact_secondary_label": "Solicitar información",
        "contact_secondary_href": "mailto:jorge@dragonne.co?subject=Servicio%20de%20redes%20sociales",
        "cta_calendar": "Agendar reunión",
        "cta_pdf": "Descargar PDF",
        "cta_contact": "Contáctanos",
        "close_secondary_label": "Escríbenos",
        "close_secondary_target": "_self",
        "floating_cta_label": "Agendar reunión",
        "floating_cta_href": "",
        "floating_cta_target": "_blank",
        "footer_note": "DRAGONNÉ · criterio editorial y operación de redes para hospitalidad.",
        "slides": [
            {
                "variant": "hero",
                "kicker": "Servicio",
                "title_lines": [
                    "Gestión de redes y contenido",
                    "para hospitalidad, con criterio.",
                ],
                "lead": (
                    "Estrategia y calendarización, publicación en hasta tres redes, reglas de atención y automatización, "
                    "y presentación de resultados."
                ),
            },
            {
                "variant": "light",
                "step": 1,
                "kicker": "Operación",
                "title": "La operación se come la consistencia.",
                "body": (
                    "En hotelería y restaurantes, lo urgente manda. "
                    "Cuando redes queda para “si alcanza”, el canal se vuelve irregular y la respuesta se retrasa."
                ),
            },
            {
                "variant": "dark",
                "step": 2,
                "kicker": "Percepción",
                "title": "La cuenta es parte de la experiencia.",
                "body": (
                    "Si el tono y lo visual no sostienen un estándar, se percibe inconsistencia. "
                    "Y si la conversación no se atiende con orden, se pierde intención comercial y confianza."
                ),
            },
            {
                "variant": "light",
                "step": 3,
                "kicker": "Ejecución",
                "title": "No es solo publicar. Es sostener el canal.",
                "body": (
                    "Estrategia, ejecución, reglas para atención y cierre con lectura de resultados. "
                    "Un sistema simple para operar redes sin improvisación."
                ),
            },
            {
                "variant": "dark",
                "step": 4,
                "kicker": "Modelo",
                "title_lines": [
                    "El problema no es el contenido.",
                    "Es operar el canal con orden.",
                ],
                "body": (
                    "Este servicio pone ritmo, criterio editorial y operación: calendarización, publicación, reglas para atención "
                    "y cierre con resultados. Para que redes no dependa de ratos libres."
                ),
                "body_compact": True,
            },
            {
                "variant": "light",
                "step": 5,
                "kicker": "Qué incluye",
                "title_lines": [
                    "Social Media Management",
                    "& Content Creation",
                ],
                "wide": True,
                "body": (
                    "Estrategia y calendarización. Publicación en hasta tres redes. Reglas de atención y automatización. "
                    "Reels, carruseles y posts en volumen fijo. Idea creativa, copy y coherencia de marca. Presentación de resultados."
                ),
                "bullets": [
                    {
                        "icon": "social",
                        "title": "Gestión de la cuenta",
                        "text": (
                            "Calendarización y publicación en hasta tres redes y lineamientos claros para sostener el estándar."
                        ),
                    },
                    {
                        "icon": "rocket",
                        "title": "Reels, carruseles y posts",
                        "text": (
                            "Formato vertical, carrusel y post fijo. Enfocado en experiencia, servicio y propuesta del lugar."
                        ),
                    },
                    {
                        "icon": "megaphone",
                        "title": "Idea creativa, copy y coherencia de marca",
                        "text": (
                            "Idea y redacción por publicación. Tono consistente y mensajes alineados a la propuesta del lugar."
                        ),
                    },
                    {
                        "icon": "revenue",
                        "title": "Resultados",
                        "text": (
                            "Presentación de resultados y siguientes ajustes para sostener un mejor ritmo."
                        ),
                    },
                ],
            },
            {
                "variant": "services",
                "step": 6,
                "kicker": "Quién lo hace",
                "title_lines": [
                    "Lo lleva un creator de contenido",
                    "en travel y hospitalidad.",
                ],
                "wide": True,
                "body": (
                    "Sabe convertir espacio, servicio y propuesta del lugar en contenido que se entiende y se antoja. "
                    "Si te interesa, también están disponibles servicios de pauta en Meta/Google y creación de UGC en propiedad."
                ),
                "services": [
                    {"icon": "globe", "label": "Contenido travel"},
                    {"icon": "social", "label": "UGC en propiedad"},
                    {"icon": "meta_brand", "label": "Meta Ads"},
                    {"icon": "google_brand", "label": "Google Ads"},
                ],
            },
            {
                "variant": "dark",
                "step": 7,
                "kicker": "Impacto",
                "title": "Más claridad. Menos improvisación.",
                "body": (
                    "Presencia sostenida, reglas de atención y un cierre mensual con lectura de resultados. "
                    "El objetivo no es “publicar más”. Es operar mejor el canal."
                ),
                "chips": [
                    "Calendarización",
                    "Hasta 3 redes",
                    "Reglas de atención",
                    "Resultados",
                ],
            },
            {
                "variant": "light",
                "step": 8,
                "kicker": "Condiciones",
                "title": "Para que el servicio corra, se necesita orden interno.",
                "body": (
                    "Accesos, lineamientos y una vía clara para autorización. "
                    "Eso evita fricción y mantiene el ritmo de publicación."
                ),
            },
            {
                "variant": "dark",
                "step": 9,
                "kicker": "Precio",
                "title": "Un solo monto al mes. Sin cobros por separado.",
                "body": (
                    "Presupuesto claro y alcance definido. "
                    "Sin cotizar cada ajuste ni separar por entregable."
                ),
            },
            {
                "variant": "services",
                "step": 10,
                "kicker": "Para quién",
                "title": "Hoteles, restaurantes y turismo: cuando el perfil pesa en la decisión.",
                "wide": True,
                "body": (
                    "Cuando entran consultas y no hay reglas claras para dirigir a reserva o a la acción. "
                    "Cuando el tema de redes se reparte entre varias personas y nunca queda cerrado."
                ),
                "services": [
                    {"icon": "hotel", "label": "Hoteles y alojamiento"},
                    {"icon": "boutique", "label": "Restaurantes y bares"},
                    {"icon": "globe", "label": "Tours y experiencias"},
                ],
            },
            {"variant": "lead", "kicker": "", "title": ""},
            {
                "variant": "close",
                "kicker": "Empecemos",
                "title": "Guardar en PDF o agendar reunión",
            },
        ],
    },
    "en": {
        "meta_title": "Social Media Management for Hospitality - DRAGONNÉ",
        "meta_description": (
            "Strategy and content calendar, publishing across up to three channels, messaging automation rules that route guests to booking or action, "
            "reels, carousels and posts on a fixed volume, brand-aligned copy, and a monthly performance readout."
        ),
        "breadcrumb_name": "Social Media Management",
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
            "If this made sense for your hotel or restaurant, let's align on scope, working cadence, and whether this service fits your operation."
        ),
        "contact_signature_name": "Jorge Flores",
        "contact_signature_role": "Head of Hospitality",
        "contact_signature_email": "jorge@dragonne.co",
        "contact_signature_avatar": "/static/team/jorge-flores.jpg",
        "contact_primary_label": "Schedule a meeting",
        "contact_secondary_label": "Request information",
        "contact_secondary_href": "mailto:jorge@dragonne.co?subject=Social%20Media%20Management%20Service",
        "cta_calendar": "Schedule a meeting",
        "cta_pdf": "Download PDF",
        "cta_contact": "Contact us",
        "close_secondary_label": "Email us",
        "close_secondary_target": "_self",
        "floating_cta_label": "Schedule a meeting",
        "floating_cta_href": "",
        "floating_cta_target": "_blank",
        "footer_note": "DRAGONNÉ · editorial judgment and social ops for hospitality teams.",
        "slides": [
            {
                "variant": "hero",
                "kicker": "Service",
                "title_lines": [
                    "Social media + content,",
                    "run like an operating system.",
                ],
                "lead": (
                    "Built for hospitality: calendar + publishing, inbox automation rules, and a monthly performance readout "
                    "so your profile stays on-standard without constant internal chasing."
                ),
            },
            {
                "variant": "light",
                "step": 1,
                "kicker": "Reality",
                "title": "Hospitality teams don't get uninterrupted time.",
                "body": (
                    "Front desk, floor, kitchen, guests. Social becomes “later”. "
                    "Later turns into gaps, rushed posts, and inconsistent responses."
                ),
            },
            {
                "variant": "dark",
                "step": 2,
                "kicker": "Brand",
                "title": "Your profile sets expectations before anyone arrives.",
                "body": (
                    "If the feed looks off-brand or the tone shifts week to week, it reads as inconsistency. "
                    "In hospitality, that shows up as hesitation to book."
                ),
            },
            {
                "variant": "light",
                "step": 3,
                "kicker": "System",
                "title": "The job is the loop: plan, publish, route, review.",
                "body": (
                    "A calendar is not the point. Execution is. "
                    "You need a repeatable loop that keeps the channel moving."
                ),
            },
            {
                "variant": "dark",
                "step": 4,
                "kicker": "Model",
                "title_lines": [
                    "Content isn't the bottleneck.",
                    "Operating the channel is.",
                ],
                "body": (
                    "We bring rhythm, editorial judgment, and execution: calendar + publishing, messaging rules, "
                    "and a monthly close with results."
                ),
                "body_compact": True,
            },
            {
                "variant": "light",
                "step": 5,
                "kicker": "What's included",
                "title_lines": [
                    "Social Media Management",
                    "& Content Creation",
                ],
                "wide": True,
                "body": (
                    "Strategy + calendar. Publishing across up to three channels. Inbox automation rules. "
                    "Reels, carousels and posts on a fixed volume. Brand-aligned copy. Monthly performance readout."
                ),
                "bullets": [
                    {
                        "icon": "social",
                        "title": "Account management",
                        "text": (
                            "Calendar and publishing across up to three channels, with clear guidelines that protect the brand standard."
                        ),
                    },
                    {
                        "icon": "rocket",
                        "title": "Reels, carousels and posts",
                        "text": (
                            "Short-form video, carousels and static posts built around experience, service, and what makes the property worth the stay."
                        ),
                    },
                    {
                        "icon": "megaphone",
                        "title": "Creative + copy",
                        "text": (
                            "Creative direction and copy per post, written to match the property's voice and guest expectations."
                        ),
                    },
                    {
                        "icon": "revenue",
                        "title": "Results",
                        "text": (
                            "A monthly readout: what's working, what isn't, and what we change next."
                        ),
                    },
                ],
            },
            {
                "variant": "services",
                "step": 6,
                "kicker": "Who runs it",
                "title_lines": [
                    "Led by a travel content creator,",
                    "with hospitality operator context.",
                ],
                "wide": True,
                "body": (
                    "A creator's eye for what plays on camera, plus an operator's sense of what matters on-property. "
                    "Meta/Google ads and on-property UGC are also available."
                ),
                "services": [
                    {"icon": "globe", "label": "Travel content"},
                    {"icon": "social", "label": "On-property UGC"},
                    {"icon": "meta_brand", "label": "Meta Ads"},
                    {"icon": "google_brand", "label": "Google Ads"},
                ],
            },
            {
                "variant": "dark",
                "step": 7,
                "kicker": "Impact",
                "title": "More control. Less scrambling.",
                "body": (
                    "An on-standard presence, routing rules for inquiries, and a monthly close with results. "
                    "You stop guessing, and you stop doing social at the end of the day."
                ),
                "chips": [
                    "Calendar",
                    "Up to 3 channels",
                    "Routing rules",
                    "Readout",
                ],
            },
            {
                "variant": "light",
                "step": 8,
                "kicker": "Inputs",
                "title": "We just need clean access and a fast approval lane.",
                "body": (
                    "Account access, brand guidelines, and one point of contact. "
                    "That keeps the calendar moving and avoids rework."
                ),
            },
            {
                "variant": "dark",
                "step": 9,
                "kicker": "Pricing",
                "title": "A monthly retainer with defined scope.",
                "body": (
                    "Predictable budget and clear deliverables. "
                    "No surprise line items, no per-tweak quoting."
                ),
            },
            {
                "variant": "services",
                "step": 10,
                "kicker": "Fit",
                "title": "For hospitality brands where social influences booking.",
                "wide": True,
                "body": (
                    "When inquiries come in and there's no consistent way to route to booking or action. "
                    "When social is spread across the team and never truly owned."
                ),
                "services": [
                    {"icon": "hotel", "label": "Hotels"},
                    {"icon": "boutique", "label": "Restaurants & bars"},
                    {"icon": "globe", "label": "Tours & experiences"},
                ],
            },
            {"variant": "lead", "kicker": "", "title": ""},
            {
                "variant": "close",
                "kicker": "Let's begin",
                "title": "Save as PDF or book a meeting",
            },
        ],
    },
}

