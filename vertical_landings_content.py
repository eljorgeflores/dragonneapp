"""Copy y metadatos para landings de verticales DRAGONNÉ (p. ej. /hoteles, /hotels, /consultoria/...)."""

from __future__ import annotations

VERTICAL_SLUGS = frozenset({"hospitality", "startups", "smbs", "medios"})

_CALENDAR = (
    "https://calendar.google.com/calendar/appointments/schedules/"
    "AcZssZ387VmTo3CquOrVY76jpM5FK7oKH8yMolIRGL0PiAiY7nZwhr_maqZacHRTN3jy6Dgc-V53No5J?gv=true"
)


def calendar_url() -> str:
    return _CALENDAR


def _pair(title: str, body: str) -> dict:
    return {"title": title, "body": body}


def _faq(q: str, a: str) -> dict:
    return {"q": q, "a": a}


_PAGES: dict[str, dict[str, dict]] = {
    "hospitality": {
        "es": {
            "meta_title": "Consultoría hospitality · hoteles independientes y boutique | DRAGONNÉ",
            "meta_description": (
                "Firma de consultoría para hoteles independientes y boutique: viabilidad, preapertura y operación en curso. "
                "Identificamos brechas comerciales, operativas y tecnológicas; priorizamos, estructuramos, implementamos y acompañamos."
            ),
            "breadcrumb_name": "Hospitalidad",
            "eyebrow": "HOSPITALITY · HOTELES INDEPENDIENTES Y BOUTIQUE",
            "hero_title": "Más claridad para decidir.\nMás orden para operar.\nMás margen para crecer.",
            "hero_sub": (
                "Ayudamos a hoteles independientes y boutique a fortalecer su gestión comercial, operativa y tecnológica desde la "
                "viabilidad y la preapertura hasta el día a día del hotel."
            ),
            "cta_primary_label": "Agendar reunión",
            "cta_secondary_label": "Hablemos",
            "problem_deck_link_label": "Presentación →",
            "sales_deck_popup_label": "¿Encaja con tu hotel?",
            "sales_deck_popup_aria": "Abrir la presentación comercial y ver si encaja con tu hotel",
            "vl_cta_hero_secondary_kicker": "SIN COMPROMISO",
            "vl_cta_hero_secondary_title": "Diagnóstico gratis y presentación",
            "vl_cta_hero_secondary_intro": (
                "Si aún no quieres una reunión, descubre cuánto dinero podrías ahorrarte en comisiones y el ingreso adicional "
                "que podría estar generando tu hotel con una estrategia optimizada."
            ),
            "vl_cta_hero_deck": "Presentación",
            "vl_cta_bottom_lead": "Presentación o diagnóstico gratis (comisiones y margen de mejora).",
            "vl_cta_bottom_deck": "Abrir presentación",
            "vl_cta_bottom_diag": "Abrir diagnóstico gratis",
            "diag_cta_open": "Diagnóstico gratis",
            "diag_title": "Diagnóstico gratis para tu hotel",
            "diag_subtitle": (
                "Puedes añadir ciudad y tipo de propiedad (opcional, para contexto). Con habitaciones, ADR, ocupación, mix OTAs y comisiones "
                "armamos un primer diagnóstico numérico sin costo: ahorro potencial en comisiones y un rango de mejora comercial. "
                "Cifras orientativas para conversar; el análisis fino viene con tus datos reales."
            ),
            "diag_close": "Cerrar",
            "diag_calc": "Ver estimación",
            "diag_back": "Ajustar datos",
            "diag_book": "Agendar para revisar estos números",
            "diag_disclaimer": (
                "Cifras ilustrativas (no constituyen promesa de resultados)."
            ),
            "diag_l_hotel": "Nombre del hotel",
            "diag_l_rooms": "Número de habitaciones",
            "diag_l_adr": "Tarifa promedio (ADR) por noche, moneda local",
            "diag_l_occ": "Ocupación anual estimada (%)",
            "diag_l_occ_ph": "Tu % anual estimado (1–100)",
            "diag_l_numotas": "¿Cuántas OTAs tienes conectadas?",
            "diag_l_ota_block": "OTAs y comisión (%) que pagas a cada una",
            "diag_l_ota_name": "OTA (ej. Booking, Expedia…)",
            "diag_l_ota_comm": "Comisión %",
            "diag_l_add_ota": "+ Agregar otra OTA",
            "diag_l_has_web": "¿Tienen sitio web propio?",
            "diag_l_web_be": "¿El sitio tiene motor de reservas?",
            "diag_l_pay_online": "¿Aceptan pagos en línea (tarjeta/TPV en web)?",
            "diag_l_pms": "¿Qué PMS usan?",
            "diag_l_cm": "¿Qué channel manager usan?",
            "diag_l_pct_ota": "% de ventas del hotel que vienen por OTAs (sobre 100% ventas totales)",
            "diag_l_pct_direct": "% de ventas online que vienen del sitio web oficial (directo, sobre 100% ventas online)",
            "diag_l_pct_direct_ph": "Si no tienes el dato, estima o deja en blanco",
            "diag_opt_yes": "Sí",
            "diag_opt_no": "No",
            "diag_opt_unsure": "No estoy seguro",
            "diag_res_savings_title": "1. Ahorro anual estimado en comisiones OTAs",
            "diag_res_savings_body": (
                "Si migraran al canal directo (web con motor y pagos en línea) la mitad del volumen que hoy venden por OTAs, "
                "dejarían de pagar comisión sobre esa fracción. Usamos el promedio de las comisiones que indicaste por OTA."
            ),
            "diag_res_growth_title": "2. Potencial de crecimiento en ventas totales",
            "diag_res_growth_body": (
                "Combinamos tu mix OTAs vs. directo online con reglas de sensibilidad tipo revenue management: "
                "más dependencia de OTAs y menos venta directa online implica mayor techo de mejora con estrategia y ejecución; "
                "si ya vendes bien en directo, el margen adicional se acerca al piso del rango (pero sigue siendo relevante por eficiencia de mix)."
            ),
            "highlights": [
                "Viabilidad, preapertura y operación en curso",
                "Diagnóstico comercial, operativo y tecnológico",
                "Implementación con procesos, tecnología y talento",
            ],
            "sec_problems_label": "RETOS",
            "sec_problems_title": "Problemas que no siempre se ven a tiempo, pero sí pegan en margen, ritmo y control",
            "sec_problems_lead": (
                "Los hoteleros independientes suelen competir con menos tiempo de dirección y sin el talento experto en comercial, "
                "revenue y operación que hoy exige exprimir al máximo el activo frente a cadenas y vecinos bien resueltos. "
                "El síntoma es margen, ritmo o control; la raíz, muchas veces, es capacidad y foco."
            ),
            "problems": [
                _pair(
                    "Capacidad y foco frente al comp set",
                    "Sin horas de dirección ni perfiles senior en comercial y revenue, el hotel no opera a su techo: se reacciona, "
                    "se copia lo obvio y la propiedad deja dinero sobre la mesa frente a competidores con más estructura.",
                ),
                _pair(
                    "Operación desalineada",
                    "Comercial, operación y sistemas avanzan con criterios distintos. "
                    "Eso genera fricción, retrabajo, malas decisiones y desgaste innecesario para el equipo.",
                ),
                _pair(
                    "Preaperturas sin marco suficiente",
                    "El proyecto avanza, pero faltan estructura, prioridades, procesos y criterios claros para abrir con mayor control y menor riesgo operativo.",
                ),
                _pair(
                    "Tecnología que no está ayudando de verdad",
                    "Se contratan herramientas, pero no siempre están bien conectadas al negocio ni adoptadas por el equipo. "
                    "El resultado: más complejidad y poco impacto real.",
                ),
            ],
            "sec_offer_label": "QUÉ HACEMOS",
            "sec_offer_title": "Diagnosticamos dónde se pierde valor y ayudamos a corregirlo con criterio y ejecución",
            "sec_offer_support": (
                "Detectamos fugas, corregimos desalineaciones y aterrizamos mejoras que sí impactan ingresos, control y rentabilidad."
            ),
            "sec_offer_lead": (
                "Nuestro trabajo combina consultoría estratégica e implementación práctica. Entramos para entender el contexto del hotel, "
                "identificar brechas reales y acompañar cambios concretos en comercial, operación, tecnología y equipo."
            ),
            "offers": [
                _pair(
                    "Diagnóstico ejecutivo del negocio",
                    "Identificamos gaps comerciales, operativos y tecnológicos que afectan ingresos, margen, coordinación o capacidad de ejecución.",
                ),
                _pair(
                    "Priorización de palancas",
                    "No todo se resuelve al mismo tiempo. Ayudamos a distinguir qué sí mueve el negocio, qué debe corregirse primero y qué puede esperar.",
                ),
                _pair(
                    "Implementación de procesos y tecnología",
                    "Aterrizamos cambios en flujos, herramientas, operación y seguimiento para que la mejora no se quede en recomendaciones.",
                ),
                _pair(
                    "Talento y capacitación donde haga falta",
                    "Si falta capacidad, sumamos talento y capacitación para ejecutar y sostener el cambio.",
                ),
            ],
            "sec_stages_label": "ALCANCE",
            "sec_stages_title": "Entramos en momentos donde una mala decisión cuesta caro",
            "sec_stages_lead": (
                "No trabajamos solo con hoteles que ya están operando. También intervenimos cuando el activo todavía se está definiendo o preparando."
            ),
            "stages": [
                _pair(
                    "Viabilidad",
                    "Para proyectos que necesitan validar supuestos, dimensionar riesgos, ordenar criterios y tomar decisiones con más sustento antes de comprometer capital.",
                ),
                _pair(
                    "Preapertura",
                    "Para hoteles que requieren estructura, procesos, tecnología y claridad operativa antes de abrir, evitando improvisación en una etapa crítica.",
                ),
                _pair(
                    "Operación en curso",
                    "Para propiedades que ya están operando pero necesitan corregir fugas, alinear áreas, profesionalizar decisiones o mejorar resultados.",
                ),
            ],
            "stage_outcomes": [
                "Decisiones con más sustento antes de comprometer capital.",
                "Apertura con estructura y menor riesgo operativo.",
                "Fugas corregidas y áreas alineadas en la operación.",
            ],
            "sec_process_label": "METODOLOGÍA",
            "sec_process_title": "Del diagnóstico a la implementación, sin dejar todo en un deck",
            "process": [
                _pair(
                    "Entendemos el contexto",
                    "Etapa del activo, presión principal, estructura actual y síntomas visibles.",
                ),
                _pair(
                    "Detectamos brechas reales",
                    "Comercial, operación, tecnología y capacidades del equipo.",
                ),
                _pair(
                    "Priorizamos lo que sí mueve el negocio",
                    "Definimos focos de acción con lógica de impacto y viabilidad.",
                ),
                _pair(
                    "Acompañamos la ejecución",
                    "Procesos, herramientas, entrenamiento y seguimiento para que el cambio sí se sostenga.",
                ),
            ],
            "sec_results_label": "IMPACTO ESPERADO",
            "sec_results_title": "Lo que buscamos no es solo ordenar: es mejorar la capacidad del hotel para decidir y ejecutar",
            "results": [
                _pair(
                    "Mayor claridad comercial",
                    "Más visibilidad de dónde se gana, dónde se pierde y qué decisiones tienen más impacto.",
                ),
                _pair(
                    "Operación más alineada",
                    "Menos fricción entre áreas, más criterio compartido y mejor coordinación del día a día.",
                ),
                _pair(
                    "Tecnología al servicio del negocio",
                    "Herramientas mejor conectadas a la operación, con foco en uso, adopción y utilidad real.",
                ),
                _pair(
                    "Mejor base para crecer",
                    "Más estructura para abrir, operar o corregir rumbo con menos improvisación y más control.",
                ),
            ],
            "sec_icp_label": "PARA QUIÉN ES",
            "sec_icp_title": "Trabajamos mejor con hoteles que necesitan criterio, estructura y acompañamiento real",
            "icp_microlead": (
                "No somos para quien solo busca un diagnóstico. Trabajamos mejor con equipos dispuestos a ordenar, decidir e implementar cambios reales."
            ),
            "icp_cards": [
                _pair(
                    "Hoteles independientes y boutique",
                    "Propiedades donde el resultado depende de decisiones más finas y de una operación bien coordinada.",
                ),
                _pair(
                    "Proyectos en desarrollo o preapertura",
                    "Activos que todavía están tomando decisiones clave y necesitan llegar a operación con mejor base.",
                ),
                _pair(
                    "Equipos con presión en resultados",
                    "Hoteles que ya operan, pero cargan fricciones en comercial, operación, sistemas o estructura del equipo.",
                ),
                _pair(
                    "Propiedades que quieren profesionalizar su ejecución",
                    "Negocios que no buscan solo diagnóstico, sino apoyo para aterrizar cambios reales.",
                ),
            ],
            "faq_title": "Preguntas frecuentes",
            "faq": [
                _faq(
                    "¿Solo trabajan con hoteles que ya están operando?",
                    "No. También participamos en etapas de viabilidad y preapertura, cuando ordenar criterios y decisiones a tiempo puede evitar errores costosos más adelante.",
                ),
                _faq(
                    "¿Su trabajo se queda en recomendaciones?",
                    "No. Combinamos diagnóstico con implementación, acompañamiento y aterrizaje operativo para que las mejoras realmente se ejecuten.",
                ),
                _faq(
                    "¿Incluyen tecnología dentro del alcance?",
                    "Sí. Podemos ayudar a identificar brechas tecnológicas, recomendar herramientas y acompañar su integración en la operación.",
                ),
                _faq(
                    "¿También apoyan con talento?",
                    "Sí, cuando la necesidad lo amerita. Podemos participar en búsqueda, selección o capacitación de perfiles estratégicos para áreas relevantes del negocio.",
                ),
                _faq(
                    "¿Trabajan revenue management?",
                    "Sí, dentro de una visión más amplia de estructura comercial, operación y rentabilidad, no como un esfuerzo aislado.",
                ),
            ],
            "final_cta_title": "Si tu hotel necesita más claridad para decidir y más estructura para ejecutar, conversemos.",
            "final_cta_lead": (
                "Cuéntanos en qué etapa estás —viabilidad, preapertura o operación— y dónde sientes mayor presión. "
                "A partir de ahí podemos evaluar encaje, prioridades y siguiente paso."
            ),
            "final_cta_btn_primary": "Agendar reunión",
            "final_cta_btn_secondary": "Escríbenos",
        },
        "en": {
            "meta_title": "Hospitality consulting · independent & boutique hotels | DRAGONNÉ",
            "meta_description": (
                "Consulting firm for independent and boutique hotels—feasibility, pre-opening, and operations. "
                "We identify commercial, operational, and technology gaps; prioritize, structure, implement, and stay with you."
            ),
            "breadcrumb_name": "Hospitality",
            "eyebrow": "HOSPITALITY · INDEPENDENT & BOUTIQUE HOTELS",
            "hero_title": "More clarity to decide. More order to run. More margin to grow.",
            "hero_sub": (
                "We help independent and boutique hotels strengthen commercial, operational, and technology management from feasibility "
                "and pre-opening through the hotel's day-to-day."
            ),
            "cta_primary_label": "Book a meeting",
            "cta_secondary_label": "Write to us",
            "problem_deck_link_label": "Presentation →",
            "sales_deck_popup_label": "See if it fits your hotel",
            "sales_deck_popup_aria": "Open the commercial presentation to see if it fits your hotel",
            "vl_cta_hero_secondary_kicker": "NO COMMITMENT YET",
            "vl_cta_hero_secondary_title": "Free diagnosis & presentation",
            "vl_cta_hero_secondary_intro": (
                "Not ready to meet? The diagnosis turns size, occupancy, and OTA mix into two clear reads (commission margin and direct upside) "
                "and emails you a branded summary—or open the presentation for strategic context."
            ),
            "vl_cta_hero_deck": "Presentation",
            "vl_cta_bottom_lead": "Presentation or free diagnosis (commissions and upside range).",
            "vl_cta_bottom_deck": "Open presentation",
            "vl_cta_bottom_diag": "Open free diagnosis",
            "diag_cta_open": "Free diagnosis",
            "diag_title": "Free diagnosis for your hotel",
            "diag_subtitle": (
                "You can add city and property type (optional, for context). From rooms, ADR, occupancy, OTA mix, and commissions we generate "
                "a first numeric diagnosis at no cost: potential commission savings and a commercial improvement range. "
                "Directional figures to discuss; deep analysis uses your real data."
            ),
            "diag_close": "Close",
            "diag_calc": "See estimate",
            "diag_back": "Edit inputs",
            "diag_book": "Book a call to review",
            "diag_disclaimer": (
                "Illustrative numbers (not a guarantee). They are meant to discuss with a DRAGONNÉ revenue manager "
                "and validate assumptions with your real data."
            ),
            "diag_l_hotel": "Hotel name",
            "diag_l_rooms": "Number of rooms",
            "diag_l_adr": "Average daily rate (ADR) per night, local currency",
            "diag_l_occ": "Estimated annual occupancy (%)",
            "diag_l_occ_ph": "Your estimated annual % (1–100)",
            "diag_l_numotas": "How many OTAs are you connected to?",
            "diag_l_ota_block": "OTAs and commission (%) you pay each",
            "diag_l_ota_name": "OTA (e.g. Booking, Expedia…)",
            "diag_l_ota_comm": "Commission %",
            "diag_l_add_ota": "+ Add another OTA",
            "diag_l_has_web": "Do you have your own website?",
            "diag_l_web_be": "Does the site have a booking engine?",
            "diag_l_pay_online": "Do you accept online payments on the web?",
            "diag_l_pms": "Which PMS do you use?",
            "diag_l_cm": "Which channel manager do you use?",
            "diag_l_pct_ota": "% of hotel sales from OTAs (of 100% total hotel sales)",
            "diag_l_pct_direct": "% of online sales from the official website (direct, of 100% online sales)",
            "diag_l_pct_direct_ph": "If unknown, estimate or leave blank",
            "diag_opt_yes": "Yes",
            "diag_opt_no": "No",
            "diag_opt_unsure": "Not sure",
            "diag_res_savings_title": "1. Estimated annual OTA commission savings",
            "diag_res_savings_body": (
                "If half of today’s OTA volume moved to your direct channel (site with booking engine and online payments), "
                "you would stop paying commission on that slice. We use the average commission you entered per OTA."
            ),
            "diag_res_growth_title": "2. Potential uplift in total hotel sales",
            "diag_res_growth_body": (
                "We combine your OTA vs. direct-online mix with revenue-style sensitivity rules: "
                "higher OTA dependence and lower direct-online share implies a higher upside range with strategy and execution; "
                "if you already sell well direct, the incremental % moves toward the lower bound (still meaningful via mix efficiency)."
            ),
            "highlights": [
                "Feasibility, pre-opening, and ongoing operations",
                "Commercial, operational, and technology diagnosis",
                "Implementation with processes, technology, and talent",
            ],
            "sec_problems_label": "CHALLENGES",
            "sec_problems_title": "Problems you don’t always see in time—but they hit margin, pace, and control",
            "sec_problems_lead": (
                "Independent hoteliers often compete with less leadership time and without the expert commercial, revenue, and operations talent "
                "needed to run the asset at full potential against chains and sharp local competitors. The symptom is margin, pace, or control; "
                "the root cause is often capacity and focus."
            ),
            "problems": [
                _pair(
                    "Capacity and focus vs. the comp set",
                    "Without leadership bandwidth and senior commercial/revenue profiles, the hotel does not run at its ceiling: it reacts, copies the obvious, "
                    "and leaves money on the table versus competitors with stronger structure.",
                ),
                _pair(
                    "Misaligned operations",
                    "Commercial, operations, and systems move with different criteria. That creates friction, rework, poor decisions, and unnecessary wear on the team.",
                ),
                _pair(
                    "Pre-openings without enough frame",
                    "The project moves forward, but structure, priorities, processes, and clear criteria are missing to open with more control and lower operational risk.",
                ),
                _pair(
                    "Technology that is not really helping",
                    "Tools are bought, but they are not always well connected to the business or adopted by the team. "
                    "The result: more complexity and little real impact.",
                ),
            ],
            "sec_offer_label": "WHAT WE DO",
            "sec_offer_title": "We diagnose where value is lost and help correct it with judgment and execution",
            "sec_offer_support": (
                "We spot leaks, fix misalignment, and land improvements that move revenue, control, and profitability."
            ),
            "sec_offer_lead": (
                "Our work combines strategic consulting and practical implementation. We enter to understand the hotel’s context, identify real gaps, "
                "and support concrete change across commercial, operations, technology, and the team."
            ),
            "offers": [
                _pair(
                    "Executive business diagnosis",
                    "We identify commercial, operational, and technology gaps that affect revenue, margin, coordination, or execution capacity.",
                ),
                _pair(
                    "Prioritization of levers",
                    "Not everything can be fixed at once. We help distinguish what actually moves the business, what must be fixed first, and what can wait.",
                ),
                _pair(
                    "Process and technology implementation",
                    "We land change in workflows, tools, operations, and follow-up so improvement does not stop at recommendations.",
                ),
                _pair(
                    "Talent and training where needed",
                    "When capacity is missing, we add talent and training to execute and sustain the change.",
                ),
            ],
            "sec_stages_label": "SCOPE",
            "sec_stages_title": "We engage when a bad decision is expensive",
            "sec_stages_lead": (
                "We do not only work with hotels already operating. We also step in when the asset is still being defined or prepared."
            ),
            "stages": [
                _pair(
                    "Feasibility",
                    "For projects that need to validate assumptions, size risk, align criteria, and make decisions with stronger grounding before committing capital.",
                ),
                _pair(
                    "Pre-opening",
                    "For hotels that need structure, processes, technology, and operational clarity before opening—avoiding improvisation in a critical phase.",
                ),
                _pair(
                    "Ongoing operations",
                    "For properties already running that need to fix leaks, align areas, professionalize decisions, or improve results.",
                ),
            ],
            "stage_outcomes": [
                "Stronger decisions before committing capital.",
                "Opening with structure and lower operational risk.",
                "Leaks addressed and functions aligned in day-to-day operations.",
            ],
            "sec_process_label": "METHODOLOGY",
            "sec_process_title": "From diagnosis to implementation—not everything in a deck",
            "process": [
                _pair(
                    "We understand the context",
                    "Asset stage, main pressure, current structure, and visible symptoms.",
                ),
                _pair(
                    "We detect real gaps",
                    "Commercial, operations, technology, and team capabilities.",
                ),
                _pair(
                    "We prioritize what actually moves the business",
                    "We define action focus with impact and feasibility logic.",
                ),
                _pair(
                    "We accompany execution",
                    "Processes, tools, training, and follow-up so change actually holds.",
                ),
            ],
            "sec_results_label": "EXPECTED IMPACT",
            "sec_results_title": "We are not only aiming to tidy up—we improve the hotel’s ability to decide and execute",
            "results": [
                _pair(
                    "Stronger commercial clarity",
                    "More visibility on where you win, where you lose, and which decisions matter most.",
                ),
                _pair(
                    "Better-aligned operations",
                    "Less friction across areas, more shared criteria, and smoother day-to-day coordination.",
                ),
                _pair(
                    "Technology in service of the business",
                    "Tools better connected to operations, focused on use, adoption, and real utility.",
                ),
                _pair(
                    "A stronger base to grow",
                    "More structure to open, operate, or course-correct with less improvisation and more control.",
                ),
            ],
            "sec_icp_label": "WHO IT’S FOR",
            "sec_icp_title": "We work best with hotels that need judgment, structure, and real accompaniment",
            "icp_microlead": (
                "We're not for teams that only want a diagnosis. We work best with organizations ready to get organized, decide, and implement real change."
            ),
            "icp_cards": [
                _pair(
                    "Independent and boutique hotels",
                    "Properties where outcomes depend on finer decisions and a well-coordinated operation.",
                ),
                _pair(
                    "Projects in development or pre-opening",
                    "Assets still making key decisions and needing to reach operations on a stronger base.",
                ),
                _pair(
                    "Teams under results pressure",
                    "Hotels already operating but carrying friction in commercial, operations, systems, or team structure.",
                ),
                _pair(
                    "Properties that want to professionalize execution",
                    "Businesses seeking not only diagnosis but support to land real change.",
                ),
            ],
            "faq_title": "Frequently asked questions",
            "faq": [
                _faq(
                    "Do you work only with hotels that are already operating?",
                    "No. We also engage in feasibility and pre-opening—when aligning criteria and decisions in time can prevent costly mistakes later.",
                ),
                _faq(
                    "Does your work stop at recommendations?",
                    "No. We combine diagnosis with implementation, accompaniment, and operational landing so improvements are actually executed.",
                ),
                _faq(
                    "Is technology within scope?",
                    "Yes. We can help identify technology gaps, recommend tools, and support their integration into operations.",
                ),
                _faq(
                    "Do you also support talent?",
                    "Yes, when the need warrants it. We can participate in search, selection, or training of strategic profiles for relevant areas of the business.",
                ),
                _faq(
                    "Do you do revenue management?",
                    "Yes, within a broader view of commercial structure, operations, and profitability—not as an isolated effort.",
                ),
            ],
            "final_cta_title": "If your hotel needs more clarity to decide and more structure to execute, let’s talk.",
            "final_cta_lead": (
                "Tell us what stage you are in—feasibility, pre-opening, or operations—and where you feel the most pressure. "
                "From there we can assess fit, priorities, and next steps."
            ),
            "final_cta_btn_primary": "Book a meeting",
            "final_cta_btn_secondary": "Write to us",
        },
    },
    "startups": {
        "es": {
            "meta_title": "Startups — Consultoría DRAGONNÉ",
            "meta_description": (
                "De la improvisación al escalamiento ordenado: talento estratégico, procesos comerciales, BD y operación para founders en crecimiento."
            ),
            "breadcrumb_name": "Startups",
            "eyebrow": "Vertical · Startups",
            "hero_title": "Del caos operativo al escalamiento que se puede repetir",
            "hero_sub": (
                "Ayudamos a founders y equipos en crecimiento a contratar mejor, documentar lo crítico y profesionalizar comercial y Customer Success "
                "sin apagar el fuego que te hizo llegar hasta aquí."
            ),
            "cta_primary_label": "Agendar sesión",
            "cta_secondary_label": "Escribirnos",
            "highlights": [
                "Talento comercial y CS con criterio de etapa",
                "Playbooks y documentación mínima viable pero seria",
                "Ritmo de negocio alineado con inversores y producto",
            ],
            "sec_problems_label": "Contexto",
            "sec_problems_title": "Problemas habituales en esta etapa",
            "sec_problems_lead": (
                "Cuando el conocimiento vive en pocas cabezas y cada decisión pasa por el founder, "
                "el crecimiento castiga al equipo antes que al mercado."
            ),
            "hero_outcome_segments": ("Talento", "Proceso", "Escala"),
            "problems": [
                _pair(
                    "Todo depende de dos personas",
                    "El conocimiento vive en chats; cada contratación nueva tarda semanas en ser productiva.",
                ),
                _pair(
                    "Pipeline ingobernable",
                    "Oportunidades sin etapas claras, forecast incierto y talento comercial con poco a qué agarrarse.",
                ),
                _pair(
                    "CS reactivo",
                    "La retención se apaga incendios en lugar de procesos; el producto y ventas no comparten la misma lectura del cliente.",
                ),
                _pair(
                    "Documentación inexistente o obsoleta",
                    "Cada pitch, onboarding o negociación se reinventa; escalas esfuerzo, no resultado.",
                ),
            ],
            "sec_offer_label": "Oferta",
            "sec_offer_title": "Qué hacemos contigo",
            "sec_offer_lead": "Priorizamos lo mínimo indispensable para que el equipo venda, entregue y aprenda en loop—sin metodología de agencia genérica.",
            "offers": [
                _pair(
                    "Talento estratégico",
                    "Perfiles de ventas, operaciones y CS; entrevistas, scorecards y briefings de onboarding.",
                ),
                _pair(
                    "Comercial y BD",
                    "Secuencias, criterios de ICP, etapas de oportunidad y handoff producto–ventas–CS.",
                ),
                _pair(
                    "Operación y escalamiento funcional",
                    "Rituales, decisión y documentación para que un equipo de 15 se comporte mejor que uno de 50 desordenado.",
                ),
            ],
            "sec_process_label": "Forma de trabajo",
            "sec_process_title": "Cómo trabajamos",
            "process": [
                _pair("Diagnóstico", "Mapa de riesgos: gente, proceso y mensaje. Qué frena el siguiente salto de ARR o retención."),
                _pair("Estrategia", "Plan de 30–90 días con entregables y dueños internos."),
                _pair("Implementación", "Sesiones de trabajo, hiring support y ajustes según tracción real."),
                _pair("Acompañamiento", "Seguimiento hasta que el playbook corre sin supervisión constante."),
            ],
            "sec_results_label": "Impacto",
            "sec_results_title": "Qué buscamos generar",
            "results": [
                _pair(
                    "Menos improvisación diaria",
                    "Equipos que saben qué hacer el lunes sin esperar al founder en cada decisión.",
                ),
                _pair(
                    "Forecast más honesto",
                    "Pipeline con definiciones compartidas y responsables claros.",
                ),
                _pair(
                    "Base para financiamiento o siguiente ronda",
                    "Historia operativa creíble: proceso, talento y métricas alineadas.",
                ),
            ],
            "sec_icp_label": "Alineación",
            "sec_icp_title": "Para quién es",
            "icp_intro": "Encaja si eres o lideras en:",
            "icp_bullets": [
                "Startup post product–market fit o en aceleración temprana",
                "Fundador, cofundador, CEO u ops lidiando con hiring y comercial al mismo tiempo",
                "Equipos B2B o híbridos con complejidad de onboarding o éxito del cliente",
            ],
            "faq_title": "Preguntas frecuentes",
            "faq": [
                _faq(
                    "¿Son una aceleradora o reemplazan al COO?",
                    "No somos aceleradora ni reemplazo permanente. Entramos con entregables, transferimos criterio y salimos cuando el sistema corre.",
                ),
                _faq(
                    "¿Trabajan remoto?",
                    "Sí. Combinamos sesiones profundas en vivo y seguimiento remoto según zona horaria y etapa.",
                ),
                _faq(
                    "¿Cuánto dura un encargo típico?",
                    "Depende del punto de partida; arrancamos con un alcance acotado y extendemos solo si aporta valor neto.",
                ),
            ],
            "final_cta_title": "Si escalas con presión en el equipo, hablemos",
            "final_cta_lead": "Cuéntanos etapa, modelo de negocio y el cuello de botella actual. Te respondemos con alcance y forma de trabajo claros.",
            "pullso_card_title": "",
            "pullso_card_body": "",
            "pullso_card_cta": "",
        },
        "en": {
            "meta_title": "Startups — DRAGONNÉ consulting",
            "meta_description": (
                "From improvisation to orderly scaling: strategic talent, commercial process, BD, and operations for growing founders."
            ),
            "breadcrumb_name": "Startups",
            "eyebrow": "Vertical · Startups",
            "hero_title": "From operational chaos to repeatable scaling",
            "hero_sub": (
                "We help founders and growth-stage teams hire with judgment, document what matters, and professionalize sales and Customer Success "
                "without killing the spark that built the company."
            ),
            "cta_primary_label": "Schedule a session",
            "cta_secondary_label": "Message us",
            "highlights": [
                "Commercial and CS talent with stage-appropriate bar",
                "Lean-but-serious playbooks and documentation",
                "Operating cadence aligned with product and investors",
            ],
            "sec_problems_label": "Context",
            "sec_problems_title": "Common pain at this stage",
            "sec_problems_lead": (
                "When knowledge sits in a few heads and every call runs through the founder, "
                "growth strains the team before it strains the market."
            ),
            "hero_outcome_segments": ("Talent", "Process", "Scale"),
            "problems": [
                _pair(
                    "Everything hinges on two people",
                    "Knowledge lives in DMs; every new hire takes weeks to become productive.",
                ),
                _pair(
                    "Ungovernable pipeline",
                    "Opportunities without crisp stages, weak forecast, and sales talent with little to hold onto.",
                ),
                _pair(
                    "Reactive CS",
                    "Retention fights fires; product and sales don’t share one customer read.",
                ),
                _pair(
                    "Missing or stale documentation",
                    "Every pitch, onboarding, or negotiation is reinvented—you scale effort, not outcomes.",
                ),
            ],
            "sec_offer_label": "Offer",
            "sec_offer_title": "What we do with you",
            "sec_offer_lead": "We prioritize the minimum viable rigor so the team can sell, deliver, and learn in loop—no generic agency theater.",
            "offers": [
                _pair(
                    "Strategic talent",
                    "Sales, ops, and CS profiles; interviews, scorecards, onboarding briefings.",
                ),
                _pair(
                    "Commercial and BD",
                    "Sequences, ICP criteria, opportunity stages, and product–sales–CS handoffs.",
                ),
                _pair(
                    "Operations and functional scaling",
                    "Rituals, decisions, and documentation so a team of 15 outperforms a sloppy 50.",
                ),
            ],
            "sec_process_label": "How we work",
            "sec_process_title": "Our process",
            "process": [
                _pair("Diagnosis", "People, process, and narrative risks—what blocks the next ARR or retention step-change."),
                _pair("Strategy", "30–90 day plan with owners and deliverables."),
                _pair("Implementation", "Working sessions, hiring support, and tuning to real traction."),
                _pair("Support", "Cadence until the playbook runs without constant oversight."),
            ],
            "sec_results_label": "Outcomes",
            "sec_results_title": "What we aim to produce",
            "results": [
                _pair(
                    "Less daily improvisation",
                    "Teams that know Monday’s priorities without the founder in every decision.",
                ),
                _pair(
                    "More honest forecasting",
                    "Pipeline with shared definitions and accountable owners.",
                ),
                _pair(
                    "A credible operating story",
                    "For financing or the next round—process, talent, and metrics aligned.",
                ),
            ],
            "sec_icp_label": "Fit",
            "sec_icp_title": "Who this is for",
            "icp_intro": "A fit if you are or lead at:",
            "icp_bullets": [
                "A post-PMF startup or early acceleration phase",
                "A founder, co-founder, CEO, or ops lead juggling hiring and revenue",
                "B2B or hybrid teams with real onboarding or customer-success complexity",
            ],
            "faq_title": "FAQ",
            "faq": [
                _faq(
                    "Are you an accelerator or a fractional COO?",
                    "Neither. We enter with deliverables, transfer judgment, and exit when the system runs.",
                ),
                _faq(
                    "Do you work remotely?",
                    "Yes—deep live sessions plus remote follow-through across time zones.",
                ),
                _faq(
                    "How long is a typical engagement?",
                    "It depends on the starting point; we scope tightly first and extend only if net value is clear.",
                ),
            ],
            "final_cta_title": "If scaling is straining the team, let’s talk",
            "final_cta_lead": "Share stage, model, and the current bottleneck. We’ll reply with crisp scope and how we’d work.",
            "pullso_card_title": "",
            "pullso_card_body": "",
            "pullso_card_cta": "",
        },
    },
    "smbs": {
        "es": {
            "meta_title": "SMBs y pymes — Consultoría DRAGONNÉ",
            "meta_description": (
                "Profesionaliza operación y comercial: procesos, capacitación, documentación y crecimiento con orden para dueños y directores."
            ),
            "breadcrumb_name": "SMBs",
            "eyebrow": "Vertical · SMBs / Pymes",
            "hero_title": "Operación y crecimiento con menos dependencia del improvisado",
            "hero_sub": (
                "Para pymes que ya facturan pero sienten que el negocio pesa en pocas personas. Estructura comercial, servicio y backoffice "
                "sin convertir la empresa en burocracia."
            ),
            "cta_primary_label": "Agendar sesión",
            "cta_secondary_label": "Escribirnos",
            "highlights": [
                "Procesos que el equipo entiende y usa",
                "Commercial y servicio alineados a la promesa",
                "Capacitación con resultados medibles",
            ],
            "sec_problems_label": "Realidad",
            "sec_problems_title": "Dolores frecuentes en pymes",
            "sec_problems_lead": (
                "La pyme que ya factura pero opera con demasiada improvisación: menos margen, más fricción interna y una experiencia de cliente impredecible."
            ),
            "hero_outcome_segments": ("Orden", "Cliente", "Margen"),
            "problems": [
                _pair(
                    "El dueño en todo",
                    "Aprobaciones, quejas y ventas importantes pasan por una sola cabeza; escalar cansancio, no margen.",
                ),
                _pair(
                    "Calidad de servicio inconsistente",
                    "El cliente no sabe qué esperar según quien atienda o qué sucursal toque.",
                ),
                _pair(
                    "Comercial informal",
                    "Seguimiento en hojas sueltas, descuentos sin criterio y cartera que crece más rápido que el cobro.",
                ),
                _pair(
                    "Capacitación evento único",
                    "Taller que nadie aterriza; tres meses después todo volvió al statu quo.",
                ),
            ],
            "sec_offer_label": "Oferta",
            "sec_offer_title": "Qué ofrecemos",
            "sec_offer_lead": "Diseño práctico de estándares, rutinas y roles. Pensado para empresas que necesitan rigor sin perder cercanía.",
            "offers": [
                _pair(
                    "Estructura operativa",
                    "Flujos entre administración, operación y comercial; tableros simples de seguimiento.",
                ),
                _pair(
                    "Organización comercial",
                    "Embudo claro, políticas de precio y descuento, y ritmo de revisión con dirección.",
                ),
                _pair(
                    "Capacitación y alineación",
                    "Programas cortos con práctica en el puesto de trabajo y material vivo, no solo slides.",
                ),
            ],
            "sec_process_label": "Forma de trabajo",
            "sec_process_title": "Cómo trabajamos",
            "process": [
                _pair("Diagnóstico", "Entrevistas y observación: dónde se pierde tiempo, dinero o confianza del cliente."),
                _pair("Estrategia", "Prioridades por trimestre y responsables; entregables que caben en tu realidad."),
                _pair("Implementación", "Pilotos por área, ajustes con feedback del equipo y estándares publicados."),
                _pair("Acompañamiento", "Coaching a mandos medios hasta que los nuevos hábitos se sostienen."),
            ],
            "sec_results_label": "Impacto",
            "sec_results_title": "Resultados tangibles",
            "results": [
                _pair(
                    "Menos fricción interna",
                    "Decisiones más rápidas con la misma cabeza humana.",
                ),
                _pair(
                    "Clientes más satisfechos",
                    "Experiencia predecible que protege margen y referidos.",
                ),
                _pair(
                    "Crecimiento más sano",
                    "Menos improvisación en ofertas y cobros; más base para financiamiento o nuevas líneas.",
                ),
            ],
            "sec_icp_label": "Alineación",
            "sec_icp_title": "Para quién es",
            "icp_intro": "Si encajas en uno o más de estos perfiles:",
            "icp_bullets": [
                "Dueño, socia o director general de una pyme en crecimiento o transformación",
                "Líder comercial o de operaciones con presión por profesionalizar sin frenar ventas",
                "Negocios de servicios, distribución o retail con varias personas frente al cliente",
            ],
            "faq_title": "Preguntas frecuentes",
            "faq": [
                _faq(
                    "¿Esto es un ERP o software?",
                    "No. Trabajamos criterio, procesos y capacitación; si ya tienes sistemas, nos integramos a ellos.",
                ),
                _faq(
                    "¿Cuánto tiempo toma ver cambios?",
                    "Depende del tamaño y disciplina interna; buscamos wins visibles en semanas, no solo planes de tres años.",
                ),
                _faq(
                    "¿Trabajan con equipos familiares?",
                    "Sí, con sensibilidad a la dinámica y foco en reglas de juego claras y documentadas.",
                ),
            ],
            "final_cta_title": "Ordenar la operación sin apagar el negocio",
            "final_cta_lead": "Platícanos tamaño, industria y el dolor principal. Te proponemos una conversación inicial y, si hay match, un alcance claro.",
            "pullso_card_title": "",
            "pullso_card_body": "",
            "pullso_card_cta": "",
        },
        "en": {
            "meta_title": "SMBs — DRAGONNÉ consulting",
            "meta_description": (
                "Professionalize operations and commercial: process, training, documentation, and orderly growth for owners and directors."
            ),
            "breadcrumb_name": "SMBs",
            "eyebrow": "Vertical · SMBs",
            "hero_title": "Operate and grow with less heroics",
            "hero_sub": (
                "For businesses already revenue-positive but overly dependent on a few people. Commercial structure, service, and back office—"
                "without turning the company into bureaucracy."
            ),
            "cta_primary_label": "Schedule a session",
            "cta_secondary_label": "Message us",
            "highlights": [
                "Processes teams actually adopt",
                "Commercial and service aligned to the promise",
                "Training with measurable behavior change",
            ],
            "sec_problems_label": "Reality",
            "sec_problems_title": "Typical SMB pains",
            "sec_problems_lead": (
                "Revenue-positive businesses still running too much on heroics: thinner margin, internal friction, and an unpredictable customer experience."
            ),
            "hero_outcome_segments": ("Order", "Customer", "Margin"),
            "problems": [
                _pair(
                    "The owner in everything",
                    "Approvals, escalations, and key deals flow through one person—you scale fatigue, not margin.",
                ),
                _pair(
                    "Inconsistent service",
                    "Customers don’t know what to expect depending on who answers.",
                ),
                _pair(
                    "Informal commercial motion",
                    "Tracking on scraps, discounts without rules, receivables growing faster than collections.",
                ),
                _pair(
                    "One-off training events",
                    "A workshop that never lands; three months later, status quo returns.",
                ),
            ],
            "sec_offer_label": "Offer",
            "sec_offer_title": "What we offer",
            "sec_offer_lead": "Practical standards, rituals, and roles—rigor that preserves closeness, not corporate theater.",
            "offers": [
                _pair(
                    "Operating structure",
                    "Flows across admin, operations, and commercial; simple dashboards.",
                ),
                _pair(
                    "Commercial organization",
                    "Clear funnel, pricing/discount policy, and leadership review cadence.",
                ),
                _pair(
                    "Training and alignment",
                    "Short programs with on-the-job practice and living materials—not slides alone.",
                ),
            ],
            "sec_process_label": "How we work",
            "sec_process_title": "Our process",
            "process": [
                _pair("Diagnosis", "Interviews and observation—where time, money, or trust leaks."),
                _pair("Strategy", "Quarterly priorities with owners; deliverables that fit reality."),
                _pair("Implementation", "Area pilots, team feedback loops, published standards."),
                _pair("Support", "Middle-manager coaching until new habits stick."),
            ],
            "sec_results_label": "Outcomes",
            "sec_results_title": "Tangible outcomes",
            "results": [
                _pair(
                    "Less internal friction",
                    "Faster decisions with the same headcount.",
                ),
                _pair(
                    "Happier customers",
                    "Predictable experience protecting margin and referrals.",
                ),
                _pair(
                    "Healthier growth",
                    "Less improvisation in offers and collections; more foundation for financing or new lines.",
                ),
            ],
            "sec_icp_label": "Fit",
            "sec_icp_title": "Who this is for",
            "icp_intro": "A fit if you are:",
            "icp_bullets": [
                "An owner, partner, or GM of a growing or transforming SMB",
                "A commercial or ops lead pressured to professionalize without pausing sales",
                "Service, distribution, or retail with many customer-facing people",
            ],
            "faq_title": "FAQ",
            "faq": [
                _faq(
                    "Is this an ERP?",
                    "No. We work on judgment, process, and training; if you have systems, we align to them.",
                ),
                _faq(
                    "How fast will we see change?",
                    "Depends on size and discipline; we aim for visible wins in weeks—not a three-year binder.",
                ),
                _faq(
                    "Do you work with family businesses?",
                    "Yes—with sensitivity to dynamics and clear, documented rules of the game.",
                ),
            ],
            "final_cta_title": "Tighten operations without stalling the business",
            "final_cta_lead": "Share size, industry, and the main pain. We’ll propose an initial conversation and, if there’s fit, crisp scope.",
            "pullso_card_title": "",
            "pullso_card_body": "",
            "pullso_card_cta": "",
        },
    },
    "medios": {
        "es": {
            "meta_title": "Posicionamiento en medios — DRAGONNÉ",
            "meta_description": (
                "Visibilidad, reputación y autoridad pública para marcas y ejecutivos. Estrategia narrativa y acompañamiento ejecutivo "
                "— no agencia de PR tradicional."
            ),
            "breadcrumb_name": "Medios",
            "eyebrow": "Vertical · Posicionamiento en medios",
            "hero_title": "Visibilidad creíble y discurso que sostiene con quién eres",
            "hero_sub": (
                "Para empresas y líderes que necesitan estar en la conversación correcta, con mensaje disciplinado y voceros preparados. "
                "Trabajo estratégico y premium: narrativa, medios y presencia pública sin humo de comunicación."
            ),
            "cta_primary_label": "Agendar sesión",
            "cta_secondary_label": "Escribirnos",
            "highlights": [
                "Narrativa ejecutiva y mensajes por audiencia",
                "Estrategia de presencia en medios alineada a negocio",
                "Perfilamiento de voceros y manejo de reputación",
            ],
            "sec_problems_label": "Presión",
            "sec_problems_title": "Lo que resolvemos",
            "sec_problems_lead": (
                "Cada aparición pública suma o resta credibilidad: el mensaje necesita disciplina y voceros preparados, no volumen por volumen."
            ),
            "hero_outcome_segments": ("Narrativa", "Credibilidad", "Control"),
            "problems": [
                _pair(
                    "Ruido sin dirección",
                    "Notas y entrevistas que no refuerzan la tesis del negocio ni protegen al líder.",
                ),
                _pair(
                    "Miedo a hablar en público",
                    "Oportunidades perdidas porque el discurso no está ensayado ni alineado al riesgo real.",
                ),
                _pair(
                    "Confundir actividad con autoridad",
                    "Muchos comunicados, poco posicionamiento: la marca no gana espacio en la conversación que importa.",
                ),
                _pair(
                    "Crisis mal anticipadas",
                    "Respuestas tardías o incoherentes que erosionan confianza con clientes e inversionistas.",
                ),
            ],
            "sec_offer_label": "Oferta",
            "sec_offer_title": "Qué ofrecemos",
            "sec_offer_lead": (
                "Pensamos como asesores de dirección, no como agencia de volumen. El objetivo es relevancia y credibilidad, no solo apariciones."
            ),
            "offers": [
                _pair(
                    "Narrativa y mensajes",
                    "Historia corporativa, pilares y prueba social alineados a la estrategia comercial y de talento.",
                ),
                _pair(
                    "Estrategia de medios",
                    "Dónde conviene estar, con qué ángulo y con qué ritmo; priorización por impacto, no por ego.",
                ),
                _pair(
                    "Perfilamiento de ejecutivos",
                    "Preparación para entrevistas, conferencias y conversaciones difíciles, con coherencia de marca.",
                ),
                _pair(
                    "Reputación y momentos críticos",
                    "Anticipación de riesgos, líneas rojas y protocolos mínimos ante escenarios sensibles.",
                ),
            ],
            "sec_process_label": "Forma de trabajo",
            "sec_process_title": "Cómo lo hacemos",
            "process": [
                _pair("Diagnóstico", "Lectura de marca, stakeholders y exposición actual: qué dicen de ustedes y qué deberían decir."),
                _pair("Estrategia", "Mapa narrativo, segmentos de medios y calendario de iniciativas creíbles."),
                _pair("Implementación", "Briefings, entrenamiento de voceros y coordinación con socios de prensa cuando aplica."),
                _pair("Acompañamiento", "Ajuste según resultados y conversación del mercado; foco en construcción sostenida."),
            ],
            "sec_results_label": "Impacto",
            "sec_results_title": "Qué cambiamos",
            "results": [
                _pair(
                    "Más autoridad percibida",
                    "Líderes y marca asociados a ideas claras, no a titulares olvidables.",
                ),
                _pair(
                    "Mejores conversaciones con socios",
                    "Inversionistas, clientes corporativos y talento senior entienden hacia dónde van.",
                ),
                _pair(
                    "Menos sorpresas públicas",
                    "Roles, mensajes y protocolos listos antes del momento caliente.",
                ),
            ],
            "sec_icp_label": "Alineación",
            "sec_icp_title": "Para quién es",
            "icp_intro": "Encaja si representas:",
            "icp_bullets": [
                "Empresa o marca en expansión que debe solidificar reputación corporativa",
                "Fundadores, CEOs o directivos que serán rostro público del negocio",
                "Organizaciones que buscan presencia selectiva en medios, no ruido masivo",
            ],
            "faq_title": "Preguntas frecuentes",
            "faq": [
                _faq(
                    "¿Son una agencia de prensa tradicional?",
                    "No prometemos volumen por volumen. Priorizamos narrativa, credibilidad y voceros sólidos; coordinamos con tu equipo o socios cuando el canal lo requiere.",
                ),
                _faq(
                    "¿Garantizan portadas o notas?",
                    "No hay garantías éticas en medios; trabajamos historias y posicionamiento que hagan más probable la cobertura relevante.",
                ),
                _faq(
                    "¿Atienden crisis 24/7?",
                    "Diseñamos anticipación y protocolo; para activación intensiva se define alcance y disponibilidad por proyecto.",
                ),
                _faq(
                    "¿Esto incluye redes sociales?",
                    "Cuando es coherente con la estrategia; el foco típico es narrativa ejecutiva y medios que construyen autoridad.",
                ),
            ],
            "final_cta_title": "Construyamos presencia pública con criterio",
            "final_cta_lead": (
                "Si necesitas claridad sobre qué decir, a quién y con qué ritmo, agenda una conversación inicial. Evaluamos encaje con honestidad."
            ),
            "pullso_card_title": "",
            "pullso_card_body": "",
            "pullso_card_cta": "",
        },
        "en": {
            "meta_title": "Media positioning — DRAGONNÉ",
            "meta_description": (
                "Visibility, reputation, and public authority for brands and executives. Narrative strategy and senior counsel—not a traditional PR shop."
            ),
            "breadcrumb_name": "Media",
            "eyebrow": "Vertical · Media positioning",
            "hero_title": "Credible visibility and a story that matches who you are",
            "hero_sub": (
                "For companies and leaders who need to be in the right conversations—with disciplined messaging and prepared spokespeople. "
                "Strategic, executive-grade work: narrative, media presence, and reputation without communications fluff."
            ),
            "cta_primary_label": "Schedule a session",
            "cta_secondary_label": "Message us",
            "highlights": [
                "Executive narrative and audience-specific messages",
                "Media strategy aligned to business outcomes",
                "Spokesperson readiness and reputation design",
            ],
            "sec_problems_label": "Pressure",
            "sec_problems_title": "What we solve",
            "sec_problems_lead": (
                "Every public moment adds or erodes credibility: messaging needs discipline and prepared spokespeople—not activity for its own sake."
            ),
            "hero_outcome_segments": ("Narrative", "Credibility", "Control"),
            "problems": [
                _pair(
                    "Noise without direction",
                    "Coverage and interviews that don’t reinforce the business thesis or protect the leader.",
                ),
                _pair(
                    "Public-speaking risk",
                    "Missed opportunities because messaging isn’t rehearsed or aligned to real downside.",
                ),
                _pair(
                    "Mistaking activity for authority",
                    "Many releases, little positioning—the brand doesn’t earn space in the conversation that matters.",
                ),
                _pair(
                    "Poorly anticipated crises",
                    "Slow or incoherent responses that erode trust with customers and investors.",
                ),
            ],
            "sec_offer_label": "Offer",
            "sec_offer_title": "What we offer",
            "sec_offer_lead": (
                "We think like senior advisors, not a volume shop. The goal is relevance and credibility—not vanity appearances."
            ),
            "offers": [
                _pair(
                    "Narrative and messaging",
                    "Corporate story, pillars, and proof points aligned to commercial and talent strategy.",
                ),
                _pair(
                    "Media strategy",
                    "Where to play, with which angle, and at what pace—prioritized for impact, not ego.",
                ),
                _pair(
                    "Executive profiling",
                    "Preparation for interviews, stages, and hard conversations—brand-consistent.",
                ),
                _pair(
                    "Reputation and critical moments",
                    "Risk anticipation, red lines, and minimum viable protocols under sensitive scenarios.",
                ),
            ],
            "sec_process_label": "How we work",
            "sec_process_title": "Our process",
            "process": [
                _pair("Diagnosis", "Brand read, stakeholders, and current exposure—what’s said and what should be."),
                _pair("Strategy", "Narrative map, media segments, and a credible initiative calendar."),
                _pair("Implementation", "Briefings, spokesperson coaching, press partner coordination when relevant."),
                _pair("Support", "Tune to outcomes and market conversation—built for durability."),
            ],
            "sec_results_label": "Outcomes",
            "sec_results_title": "What shifts",
            "results": [
                _pair(
                    "Greater perceived authority",
                    "Leaders and brand tied to clear ideas—not forgettable headlines.",
                ),
                _pair(
                    "Better stakeholder conversations",
                    "Investors, enterprise buyers, and senior talent understand the trajectory.",
                ),
                _pair(
                    "Fewer public surprises",
                    "Roles, messages, and protocols ready before the heat rises.",
                ),
            ],
            "sec_icp_label": "Fit",
            "sec_icp_title": "Who this is for",
            "icp_intro": "A fit if you represent:",
            "icp_bullets": [
                "A growing company or brand that must harden corporate reputation",
                "Founders, CEOs, or executives who will be the public face",
                "Organizations seeking selective media presence—not mass noise",
            ],
            "faq_title": "FAQ",
            "faq": [
                _faq(
                    "Are you a traditional PR agency?",
                    "We don’t sell volume for volume. We prioritize narrative, credibility, and strong spokespeople; we coordinate with your team or partners when distribution matters.",
                ),
                _faq(
                    "Do you guarantee placements?",
                    "Ethically, no one should guarantee editorial outcomes—we build stories and positioning that make relevant coverage more likely.",
                ),
                _faq(
                    "Do you handle 24/7 crises?",
                    "We design anticipation and protocol; intensive activation is scoped per project with clear availability.",
                ),
                _faq(
                    "Does this include social media?",
                    "When aligned to strategy; the typical focus is executive narrative and authority-building media.",
                ),
            ],
            "final_cta_title": "Build public presence with judgment",
            "final_cta_lead": (
                "If you need clarity on what to say, to whom, and when—book an initial conversation. We’ll be direct about fit."
            ),
            "pullso_card_title": "",
            "pullso_card_body": "",
            "pullso_card_cta": "",
        },
    },
}


def get_vertical_landing_copy(slug: str, lang: str) -> dict:
    """Devuelve el dict de copy para la plantilla; lanza KeyError si slug/idioma inválido."""
    if slug not in VERTICAL_SLUGS:
        raise KeyError(slug)
    if lang not in ("es", "en"):
        raise KeyError(lang)
    return _PAGES[slug][lang]
