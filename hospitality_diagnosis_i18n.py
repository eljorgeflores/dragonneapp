"""Copy para la landing de diagnóstico hospitalidad (/hoteles/diagnostico, /hotels/diagnosis)."""

from __future__ import annotations


def get_hospitality_diagnosis_page(lang: str) -> dict:
    if lang == "es":
        return {
            "meta_title": "Diagnóstico inicial de posicionamiento online para tu hotel",
            "meta_description": (
                "Pocos pasos: lecturas orientativas de margen en OTAs y de potencial en venta directa. "
                "Resumen por correo al terminar."
            ),
            "breadcrumb_name": "Diagnóstico",
            "nav_back": "← Hotelería",
            "hero_kicker": "",
            "hero_title": "Diagnóstico inicial de posicionamiento online",
            "hero_lead": (
                "En 6 pasos obtienes 2 lecturas: comisiones OTAs y potencial en venta directa. "
                "Al enviar, te llega el resumen por correo."
            ),
            "wiz_total": 6,
            "wiz_step_word": "Paso",
            "wiz_of": "de",
            "wiz_progress_aria": "Progreso del diagnóstico",
            "btn_next": "Continuar",
            "btn_back": "Atrás",
            "help_aria": "Qué es este dato",
            "wiz_t1": "Tu hotel y contexto",
            "wiz_t2": "Números base",
            "wiz_t3": "OTAs y comisiones",
            "wiz_t4": "Mix de ventas",
            "wiz_t5": "Operación digital",
            "wiz_t6": "Generar diagnóstico",
            "lbl_hotel": "Hotel",
            "lbl_hotel_location": "Ciudad y país",
            "hotel_location_placeholder": "Ej. Mérida, México",
            "lbl_hotel_category": "Tipo de propiedad",
            "opt_cat_placeholder": "Elige una opción",
            "diag_facts_location": "Ciudad / país",
            "diag_facts_category": "Tipo de propiedad",
            "lbl_rooms": "Habitaciones",
            "lbl_adr": "ADR / noche",
            "lbl_occ": "Ocupación %",
            "occ_placeholder": "1–100",
            "lbl_numotas": "¿Con cuántas agencias trabajas?",
            "lbl_ota_name": "Canal",
            "lbl_ota_comm": "%",
            "btn_add_ota": "Añadir canal",
            "remove_ota_aria": "Quitar canal",
            "lbl_has_web": "Sitio web",
            "lbl_web_be": "Motor en web",
            "lbl_pay": "Pagos online",
            "lbl_pms": "PMS",
            "lbl_cm": "Channel manager",
            "lbl_pct_ota": "% ventas OTAs",
            "lbl_pct_direct": "% venta directa online",
            "lbl_name": "Nombre",
            "lbl_email": "Correo",
            "lbl_phone": "Teléfono",
            "lbl_phone_prefix": "Prefijo",
            "phone_placeholder": "Número local",
            "submit_label": "Generar diagnóstico",
            "submit_loading": "Enviando…",
            "privacy_note_before": "Al enviar aceptas los ",
            "privacy_link_terms": "términos y condiciones",
            "privacy_note_between": " y la ",
            "privacy_link_privacy": "política de privacidad",
            "privacy_note_after": ".",
            "success_title": "Diagnóstico enviado",
            "success_lead": "Te enviamos el resumen por correo.",
            "success_for_hotel_before": "Para ",
            "success_for_hotel_after": " — con los datos que compartiste, estas lecturas son tuyas.",
            "res_story_intro": (
                "Estas dos cifras responden a lo mismo desde ángulos distintos: cuánto margen suele quedar "
                "atrapado en comisiones OTAs con el mix que declaraste, y un techo ilustrativo si fortaleces "
                "directo y negociación de canales."
            ),
            "res_trust_line": (
                "En DRAGONNÉ trabajamos hoteles independientes y boutique: el mismo lenguaje que gerencia y recepción."
            ),
            "success_cta_note": (
                "Reunión breve (~30 min): validamos supuestos y te dejamos 2–3 palancas claras para margen y mix. Sin pitch largo."
            ),
            "success_inbox_aria": "Dónde ver el correo",
            "success_inbox_tip": (
                "Revisa tu bandeja de entrada y spam o promociones. "
                "A veces tarda unos minutos. Si no llega, escribe a hefzi@dragonne.co y lo reenviamos."
            ),
            "success_cta_calendar": "Agendar reunión",
            "res_savings_cap": "Comisión OTAs al año (orientativa)",
            "res_savings_badge": "Lectura principal · margen en comisiones",
            "res_savings_hook": (
                "Hay margen real en comisiones OTAs: la cifra es una foto prudente de esa oportunidad, "
                "no el total que pagas hoy. Con mejor negociación y mix de canales, el upside suele ampliarse."
            ),
            "res_savings_formula_label": "Tu ruta numérica (orientativa)",
            "res_growth_cap": "Más ingreso si mueves mix a directo (orientativo)",
            "res_growth_badge": "Lectura 2 · sin vender más noches",
            "res_growth_hook": (
                "En cristiano: hoy declaraste un % de venta directa. Si lo subes a un objetivo realista, "
                "y esa parte deja de entrar por OTAs, te quedas con más por pagar menos comisión."
            ),
            "res_growth_formula_label": "Cómo lo calculamos (y el escenario +20%)",
            "res_total_cap": "Crecimiento total del hotel (orientativo)",
            "res_total_badge": "Lectura 3 · estrategia optimizada",
            "res_total_hook": (
                "Esto es el upside por ejecutar bien: más conversión, mejor canal directo y mejor mix. "
                "Usamos +20% como referencia promedio cuando la estrategia está optimizada."
            ),
            "res_disclaimer_short": (
                "Reglas fijas, redondeos y escenarios prudentes pero alentadores; cifras ilustrativas. "
                "En una reunión revisamos supuestos contigo. No sustituye análisis contable ni promete resultados."
            ),
            "err_validation": "Revisa el paso actual: datos obligatorios, correo y teléfono válido (10+ dígitos con prefijo).",
            "err_ota_step": (
                "En «OTAs y comisiones»: completa al menos una fila con canal y comisión %, "
                "o deja vacías por completo las filas que no uses (sin mezclar vacío y a medias)."
            ),
            "err_server": "No pudimos completar el envío. Intenta más tarde.",
            "err_email_delivery": (
                "Guardamos tu solicitud; el correo no salió. Escríbenos a hefzi@dragonne.co o reintenta."
            ),
            "honeypot_label": "No llenar",
            # Tooltips (hover / foco / toque en «?»)
            "tp_hotel": "Nombre comercial o marca del hotel. Lo usamos para personalizar el correo y el contexto del diagnóstico.",
            "tp_location": "Opcional pero muy útil: mercado local y segmentación del seguimiento. No altera el cálculo automático.",
            "tp_category": "Describe el tipo de propiedad; no entra en las fórmulas del resumen.",
            "hotel_category_labels": {
                "boutique": "Hotel Boutique",
                "business": "Hotel de negocios",
                "city": "Hotel de Ciudad",
                "beach": "Hotel de Playa",
                "budget": "Budget Hotel",
                "all_inclusive": "Todo incluído",
                "luxury": "Luxury Hotel",
            },
            "tp_rooms": "Número de habitaciones vendibles. Con ADR y ocupación proyectamos ingresos base del año.",
            "tp_adr": "Tarifa promedio por noche en moneda local, antes de impuestos.",
            "tp_occ": "Ocupación anual estimada (0–100). Usa tu histórico, temporada o presupuesto.",
            "tp_numotas": "Cuenta las agencias con las que vendes de forma habitual (ej. Booking, Expedia, etc.).",
            "tp_ota": "Por cada canal: nombre aproximado y comisión % que pagas. Promediamos para estimar ahorro; si falta, usamos un supuesto estándar.",
            "tp_pct_ota": "Porcentaje de ventas totales del hotel que llegan vía OTAs.",
            "tp_pct_direct": "Qué porcentaje de las ventas online vienen a través de tu sitio web o motor de reservas.",
            "tp_web": "Si el hotel tiene sitio web propio (dominio del hotel), no solo perfil en OTAs.",
            "tp_be": "Si en el sitio el huésped puede reservar con motor de reservas integrado.",
            "tp_pay": "Si aceptan pago con tarjeta u otros medios a través de la web o motor.",
            "tp_pms": "Sistema de gestión (Opera, Cloudbeds, etc.).",
            "tp_cm": "Channel manager si aplica (Siteminder, RateGain, Omnibees, etc.).",
            "tp_name": "Persona de contacto para el envío del resumen y seguimiento comercial.",
            "tp_email": "Correo donde enviaremos el resumen con las cifras orientativas.",
            "tp_phone": "Prefijo de país y número (móvil o WhatsApp). Mínimo 10 dígitos en total para validar.",
        }
    return {
        "meta_title": "Initial online positioning diagnosis for your hotel",
        "meta_description": (
            "A few steps: indicative reads on OTA commission margin and room to grow direct. "
            "Email summary when you submit."
        ),
        "breadcrumb_name": "Diagnosis",
        "nav_back": "← Hospitality",
        "hero_kicker": "",
        "hero_title": "Initial online positioning diagnosis",
        "hero_lead": (
            "In 6 steps you get 2 reads: OTA commissions and direct-booking upside. "
            "When you submit, we email you the summary."
        ),
        "wiz_total": 6,
        "wiz_step_word": "Step",
        "wiz_of": "of",
        "wiz_progress_aria": "Diagnosis progress",
        "btn_next": "Continue",
        "btn_back": "Back",
        "help_aria": "What this field means",
        "wiz_t1": "Your hotel & context",
        "wiz_t2": "Base numbers",
        "wiz_t3": "OTAs & commission",
        "wiz_t4": "Sales mix",
        "wiz_t5": "Digital ops",
        "wiz_t6": "Generate diagnosis",
        "lbl_hotel": "Hotel",
        "lbl_hotel_location": "City & country",
        "hotel_location_placeholder": "e.g. Merida, Mexico",
        "lbl_hotel_category": "Property type",
        "opt_cat_placeholder": "Choose an option (optional)",
        "diag_facts_location": "City / country",
        "diag_facts_category": "Property type",
        "lbl_rooms": "Rooms",
        "lbl_adr": "ADR / night",
        "lbl_occ": "Occupancy %",
        "occ_placeholder": "1–100",
        "lbl_numotas": "How many agencies do you work with?",
        "lbl_ota_name": "Channel",
        "lbl_ota_comm": "%",
        "btn_add_ota": "Add channel",
        "remove_ota_aria": "Remove channel",
        "lbl_has_web": "Website",
        "lbl_web_be": "Web booking engine",
        "lbl_pay": "Online payments",
        "lbl_pms": "PMS",
        "lbl_cm": "Channel manager",
        "lbl_pct_ota": "% sales via OTAs",
        "lbl_pct_direct": "% online direct",
        "lbl_name": "Name",
        "lbl_email": "Email",
        "lbl_phone": "Phone",
        "lbl_phone_prefix": "Prefix",
        "phone_placeholder": "Local number",
        "submit_label": "Generate diagnosis",
        "submit_loading": "Sending…",
        "privacy_note_before": "By submitting you accept the ",
        "privacy_link_terms": "Terms and conditions",
        "privacy_note_between": " and the ",
        "privacy_link_privacy": "Privacy policy",
        "privacy_note_after": ".",
        "success_title": "Diagnosis sent",
        "success_lead": "We sent the summary to your email.",
        "success_for_hotel_before": "For ",
        "success_for_hotel_after": " — with the inputs you shared, these reads are yours.",
        "res_story_intro": (
            "These two figures answer the same question from two angles: typical margin trapped in OTA "
            "commissions with the mix you declared, and an illustrative ceiling if you strengthen direct "
            "and channel negotiation. If you added city or property type, it also helps us contextualize "
            "follow-up (it does not change the automated formulas)."
        ),
        "res_trust_line": (
            "At DRAGONNÉ we focus on independent and boutique hotels—the same language leadership and the front desk use."
        ),
        "success_cta_note": (
            "Short call (~30 min): we validate assumptions and leave you with 2–3 clear levers for margin and mix. No long pitch."
        ),
        "success_inbox_aria": "Where to find the email",
        "success_inbox_tip": (
            "Check your inbox and spam or promotions. It can take a few minutes. "
            "If it does not arrive, write hefzi@dragonne.co and we will resend."
        ),
        "success_cta_calendar": "Book a meeting",
        "res_savings_cap": "Estimated annual OTA commission (indicative)",
        "res_savings_badge": "Primary read · commission margin",
        "res_savings_hook": (
            "There is real margin in OTA commissions: this number is a prudent snapshot of that opportunity, "
            "not everything you pay today. With stronger channel mix and negotiation, upside usually grows."
        ),
        "res_savings_formula_label": "Your numeric path (indicative)",
        "res_growth_cap": "More revenue by shifting mix to direct (indicative)",
        "res_growth_badge": "Read 2 · without selling more nights",
        "res_growth_hook": (
            "Plain English: you reported a current direct share. If you move direct to a realistic target, "
            "and that share stops coming through OTAs, you keep more by paying less commission."
        ),
        "res_growth_formula_label": "How we calculate it (and the +20% scenario)",
        "res_total_cap": "Total hotel growth (indicative)",
        "res_total_badge": "Read 3 · optimized strategy",
        "res_total_hook": (
            "This is upside from execution: higher conversion, stronger direct channel, and better mix. "
            "We use +20% as an average reference when the strategy is optimized."
        ),
        "res_disclaimer_short": (
            "Fixed rules, rounding, and prudent but encouraging scenarios; illustrative numbers. "
            "In a meeting we walk through assumptions with you. Not accounting advice or a guarantee of outcomes."
        ),
        "err_validation": "Check this step: required fields, email, and a valid phone (10+ digits with prefix).",
        "err_ota_step": (
            "Under «OTAs & commission»: fill at least one row with channel and commission %, "
            "or leave unused rows completely blank (do not mix half-filled rows)."
        ),
        "err_server": "We could not complete the request. Try again later.",
        "err_email_delivery": (
            "We saved your request; the email did not send. Write hefzi@dragonne.co or retry."
        ),
        "honeypot_label": "Leave blank",
        "tp_hotel": "Commercial or brand name of the hotel. We use it to personalize the email and diagnosis context.",
        "tp_location": "Optional but valuable: local market context and follow-up segmentation. Does not change the automated math.",
        "tp_category": "Optional. How you position the property for guests; not used in the summary formulas.",
        "hotel_category_labels": {
            "boutique": "Boutique",
            "business": "Business hotel",
            "city": "City hotel",
            "resort": "Resort",
            "budget": "Budget / economy",
            "all_inclusive": "All-inclusive",
            "luxury": "Luxury",
            "other": "Other",
        },
        "tp_rooms": "Sellable room count. With ADR and occupancy we project base annual revenue.",
        "tp_adr": "Average rate per night in local currency, before taxes.",
        "tp_occ": "Estimated annual occupancy (0–100). Use your own history, season, or budget.",
        "tp_numotas": "Count the agencies you regularly sell through (e.g. Booking, Expedia, etc.).",
        "tp_ota": "For each channel: approximate name and commission % paid. We average to estimate savings; if missing, we use a default assumption.",
        "tp_pct_ota": "Share of total hotel sales that come through OTAs.",
        "tp_pct_direct": "What percentage of online sales come through your website or booking engine.",
        "tp_web": "Whether the hotel has its own website (hotel domain), not only OTA profiles.",
        "tp_be": "Whether guests can book on the site with an integrated booking engine.",
        "tp_pay": "Whether you accept card or other payments through the web or engine.",
        "tp_pms": "Property management system (Opera, Cloudbeds, etc.).",
        "tp_cm": "Channel manager if applicable (Siteminder, RateGain, Omnibees, etc.).",
        "tp_name": "Contact person for sending the summary and follow-up.",
        "tp_email": "Email where we send the summary with indicative figures.",
        "tp_phone": "Country prefix and number (mobile/WhatsApp). At least 10 digits total to validate.",
    }
