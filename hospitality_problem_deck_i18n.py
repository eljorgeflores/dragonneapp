"""Copy para la landing tipo diapositivas (sales deck): /hoteles/ventas, /hotels/sales."""

from __future__ import annotations


def get_hospitality_problem_deck_copy(lang: str) -> dict:
    if lang not in ("es", "en"):
        lang = "es"
    return _COPY[lang]


_COPY = {
    "es": {
        "meta_title": "El reto del hotel independiente — DRAGONNÉ",
        "meta_description": (
            "Por qué muchos hoteles independientes llenan pero no les rinde la cuenta, y cómo ordenar ventas, canales y operación."
        ),
        "breadcrumb_name": "Deck comercial",
        "skip": "Saltar al contenido",
        "scroll_hint": "Sigue bajando",
        "nav_lang_en": "EN",
        "nav_lang_es": "ES",
        "nav_back_hotels": "Volver a Hotelería",
        "nav_schedule_meeting": "Agendar reunión",
        "contact_title": "Contáctanos",
        "contact_email": "hefzi@dragonne.co",
        "cta_calendar": "Agendar reunión",
        "cta_pdf": "Descargar PDF",
        "cta_contact": "Que nos contacten",
        "footer_note": "DRAGONNÉ · consultoría estratégica para propiedades y equipos hoteleros.",
        "slides": [
            {
                "variant": "hero",
                "kicker": "Hospitalidad independiente y boutique",
                "title": "No pierdes solo por precio, sino por foco.",
                "lead": (
                    "Pierdes cuando el día se lo llevan las urgencias del lobby, del personal y del mantenimiento, "
                    "y casi no queda cabeza ni calendario para sentarse a ver si estás vendiendo bien: tarifas, "
                    "página web, agencias y grupos. Mientras, el hotel de la esquina o la cadena de dos calles "
                    "ya lleva rato con alguien que solo se dedica a eso."
                ),
            },
            {
                "variant": "light",
                "step": 1,
                "kicker": "Tiempo de la gerencia",
                "title": "El gerente vive apagando fuegos.",
                "body": (
                    "Recepción, housekeeping, quejas, proveedores, banco y permisos: todo es prioritario. "
                    "La reunión de ventas y tarifas se recorre o se hace apurada, y nadie revisa con calma "
                    "cuánto ya llevas vendido para las próximas semanas ni si el vecino bajó precio. "
                    "Así el hotel reacciona tarde y siempre a la defensiva."
                ),
            },
            {
                "variant": "dark",
                "step": 2,
                "kicker": "Quién mueve precios y canales",
                "title": "Llenar habitaciones no basta si se venden mal.",
                "body": (
                    "Hace falta alguien con criterio que mire tarifas mínimas, cierres de inventario, página propia "
                    "y comisiones que te deja cada agencia, no solo subir o bajar números en el sistema. "
                    "Si eso no lo cuida una mano experimentada, ves ocupación “bonita” en el reporte pero la utilidad "
                    "no acompaña al esfuerzo del equipo."
                ),
            },
            {
                "variant": "light",
                "step": 3,
                "kicker": "Vecinos y cadenas",
                "title": "Tu competencia no espera a que tengas tiempo.",
                "body": (
                    "Los que ya armaron un equipo comercial serio ajustan precios con información, "
                    "cuidan cuánto les cuesta vender por Booking o Expedia frente a la página del hotel, "
                    "y corrigen semana a semana. Tú compites contra eso: contra cómo les rinde a ellos la operación, "
                    "no solo contra el precio que publican en internet."
                ),
            },
            {
                "variant": "dark",
                "step": 4,
                "kicker": "Síntoma y causa",
                "title_lines": [
                    "«Todo entra por agencias»",
                    "Es una señal, no el diagnóstico.",
                ],
                "body": (
                    "Cuando se dice eso en el pasillo, rara vez basta con culpar solo al canal. "
                    "Muchas veces falta tiempo al calendario de lo ya vendido, recepción y ventas van despegados "
                    "y en la oficina casi nadie mira los reportes del hotel con intención. "
                    "Por eso la pantalla se ve holgada y la cuenta no cierra como esperabas."
                ),
                "body_compact": True,
            },
            {
                "variant": "light",
                "step": 5,
                "kicker": "Qué hace el equipo",
                "title": "Ordenamos lo comercial y lo operativo en lenguaje de hotel.",
                "wide": True,
                "body": (
                    "Nuestro equipo experto ha estado del lado del hotel: entendemos utilidad, ocupación, "
                    "tarifas y equipos de recepción. Empoderamos al equipo, identificamos áreas de oportunidad "
                    "y aterrizamos prioridades claras y rutinas que el hotel sí puede sostener."
                ),
                "bullets": [
                    {
                        "icon": "radar",
                        "title": "Lectura clara",
                        "text": (
                            "Vemos si tu tarifa media va en línea con hoteles parecidos, si dependes demasiado de "
                            "agencias y qué te cuestan en comisión, si la web aporta reservas directas y en qué "
                            "canal se te va el margen noche a noche."
                        ),
                    },
                    {
                        "icon": "mix",
                        "title": "Qué tocar primero",
                        "text": (
                            "Definimos si lo urgente es tarifario, inventario, web, convenios con empresas o gastos "
                            "que se comen la habitación, según dónde ganes más margen en cada noche que ya vendes y "
                            "con qué orden conviene actuar."
                        ),
                    },
                    {
                        "icon": "rocket",
                        "title": "Que se quede en el hotel",
                        "text": (
                            "Dejamos reuniones fijas entre gerencia, recepción y ventas, reglas simples para abrir o "
                            "cerrar tarifas y habitaciones, y rutas claras para que lo comercial se vea sin fricción "
                            "en el PMS y en el channel manager."
                        ),
                    },
                    {
                        "icon": "users",
                        "title": "Tu equipo o la nuestra",
                        "text": (
                            "Buscamos o formamos a quien cubra comercial o revenue en plantilla. Si hace falta, "
                            "ejecutamos un tiempo tarifas, canales y campañas hasta que respires o llegue la persona "
                            "adecuada para sostenerlo día a día."
                        ),
                    },
                ],
            },
            {
                "variant": "dark",
                "step": 6,
                "kicker": "Forma de trabajo",
                "title": "Sabemos ejecutar procesos, no solo hacer documentos bonitos.",
                "body": (
                    "Sesiones con dirección, ventas y operación; acuerdos por escrito; tableros que todos entienden. "
                    "Revisamos contigo cómo van las ventas para las semanas que vienen hasta que el ritmo se mantenga "
                    "sin que tengamos que estar encima del teléfono cada día."
                ),
                "chips": ["Revenue", "Comercial", "Operaciones", "Tech stack"],
            },
            {
                "variant": "light",
                "step": 7,
                "kicker": "A dónde vamos",
                "title": "Mayor claridad en el negocio, más utilidad para los dueños.",
                "body": (
                    "Buscamos que sepas en qué canal te conviene vender, que las reuniones dejen de ser improviso "
                    "y que quede utilidad para invertir en producto y en que el huésped te reserve directo, "
                    "sin pelearte solo a precio con el vecino."
                ),
            },
            {
                "variant": "services",
                "step": 8,
                "kicker": "Lo que podemos ejecutar",
                "title": "Distribución, revenue y voz digital, con los datos en la mano.",
                "wide": True,
                "body": (
                    "No solo dejamos el plan en la mesa: cuando toca, lo corremos contigo o lo operamos por un tiempo "
                    "para que el hotel avance mientras armamos o reforzamos a tu equipo."
                ),
                "services": [
                    {"icon": "globe", "label": "Distribución online"},
                    {"icon": "revenue", "label": "Revenue management"},
                    {"icon": "megaphone", "label": "Marketing digital"},
                    {"icon": "social", "label": "Redes sociales"},
                ],
            },
            {"variant": "lead", "kicker": "", "title": ""},
            {
                "variant": "close",
                "kicker": "Empecemos",
                "title": "Descarga o contáctanos",
            },
        ],
    },
    "en": {
        "meta_title": "The independent hotel challenge — DRAGONNÉ",
        "meta_description": (
            "Why many independent hotels fill rooms but profits lag—and how to organize sales, channels, and ops."
        ),
        "breadcrumb_name": "Sales deck",
        "skip": "Skip to content",
        "scroll_hint": "Keep scrolling",
        "nav_lang_en": "EN",
        "nav_lang_es": "ES",
        "nav_back_hotels": "Back to Hospitality",
        "nav_schedule_meeting": "Schedule a meeting",
        "contact_title": "Contact us",
        "contact_email": "hefzi@dragonne.co",
        "cta_calendar": "Book a meeting",
        "cta_pdf": "Download PDF",
        "cta_contact": "Request a callback",
        "footer_note": "DRAGONNÉ · strategy consulting for hotel teams and owners.",
        "slides": [
            {
                "variant": "hero",
                "kicker": "Independent & boutique",
                "title": "You don’t lose only on price, but on focus.",
                "lead": (
                    "You lose when the day is eaten by lobby fires, staffing, and maintenance—and there’s almost no "
                    "headspace or calendar left to ask whether you’re actually selling well: rates, website, OTAs, and groups. "
                    "Meanwhile the hotel around the corner—or two streets away—already has someone focused on that work."
                ),
            },
            {
                "variant": "light",
                "step": 1,
                "kicker": "Leadership time",
                "title": "The GM is mostly firefighting.",
                "body": (
                    "Front desk, housekeeping, complaints, vendors, banking, permits: everything feels urgent. "
                    "The sales and pricing meeting gets pushed or rushed, and nobody calmly checks how much is already on the books "
                    "for the next few weeks—or whether the neighbor cut rate. The hotel keeps reacting late, always on the back foot."
                ),
            },
            {
                "variant": "dark",
                "step": 2,
                "kicker": "Who owns pricing & channels",
                "title": "Full rooms aren’t enough if they’re sold the wrong way.",
                "body": (
                    "You need experienced judgment on minimum rates, inventory closures, your own website, and the commission each OTA really costs you—not only nudging numbers in the system. "
                    "Without that, occupancy can look “healthy” on the report while profit doesn’t match the team’s effort."
                ),
            },
            {
                "variant": "light",
                "step": 3,
                "kicker": "Neighbors & chains",
                "title": "Your competition won’t wait until you find time.",
                "body": (
                    "Operators who already built a serious commercial team adjust pricing with information, watch OTA cost vs. direct web, "
                    "and fix things week over week. You compete with that: how efficiently they run, not only the rate they show online."
                ),
            },
            {
                "variant": "dark",
                "step": 4,
                "kicker": "Symptom vs. cause",
                "title_lines": [
                    "“Everything comes from OTAs”",
                    "A signal, not the diagnosis.",
                ],
                "body": (
                    "When you hear that in the hallway, blaming the channel alone is rarely enough. "
                    "Often there’s no calm time for what’s already on the books, front desk and sales drift apart, "
                    "and nobody in the office really reads the hotel’s reports on purpose. "
                    "That’s why the screen looks busy while the account still doesn’t close the way you expected."
                ),
                "body_compact": True,
            },
            {
                "variant": "light",
                "step": 5,
                "kicker": "What the team does",
                "title": "We bring hotel language to commercial and ops noise.",
                "wide": True,
                "body": (
                    "Our team has deep hotel-side experience: we understand performance, occupancy, rates, and front-office reality. "
                    "We empower your staff, surface opportunities, and land clear priorities and routines the property can sustain."
                ),
                "bullets": [
                    {
                        "icon": "radar",
                        "title": "Plain-spoken read",
                        "text": (
                            "We check whether your average rate tracks similar hotels, what OTAs cost you in commission after net, "
                            "whether the website converts, and where margin walks out—night by night, channel by channel."
                        ),
                    },
                    {
                        "icon": "mix",
                        "title": "What to fix first",
                        "text": (
                            "We prioritize among pricing, inventory, the website, corporate deals, or variable costs eating the room—"
                            "we sequence fixes for the biggest profit lift per night you already sell, with named owners."
                        ),
                    },
                    {
                        "icon": "rocket",
                        "title": "It sticks on property",
                        "text": (
                            "We set a steady rhythm across leadership, front desk, and sales, simple rules for opening or closing rates and rooms, "
                            "and align commercial decisions so they show cleanly in PMS and channel manager."
                        ),
                    },
                    {
                        "icon": "users",
                        "title": "Your team or ours",
                        "text": (
                            "We hire or train whoever should own commercial or revenue on your team. When bandwidth is tight, "
                            "we run pricing, channels, and campaigns for a stretch until you catch your breath or land the right hire."
                        ),
                    },
                ],
            },
            {
                "variant": "dark",
                "step": 6,
                "kicker": "How we work",
                "title": "We know how to run processes—not just ship pretty documents.",
                "body": (
                    "Working sessions with leadership, sales, and operations; agreements in writing; boards everyone understands. "
                    "We review forward bookings with you until the rhythm holds without us on speed-dial every day."
                ),
                "chips": ["Revenue", "Commercial", "Operations", "Tech stack"],
            },
            {
                "variant": "light",
                "step": 7,
                "kicker": "Where we’re headed",
                "title": "Greater clarity in the business, more profit for owners.",
                "body": (
                    "We want you to know which channel actually pays, fewer improvised meetings, and enough margin to invest in the product "
                    "and in guests booking direct—without racing the neighbor on price alone."
                ),
            },
            {
                "variant": "services",
                "step": 8,
                "kicker": "What we can run",
                "title": "Distribution, revenue, and digital voice—with data in hand.",
                "wide": True,
                "body": (
                    "We don’t only leave the plan on the table: when needed, we run it with you—or operate it for a season—"
                    "while we build or strengthen your team."
                ),
                "services": [
                    {"icon": "globe", "label": "Online distribution"},
                    {"icon": "revenue", "label": "Revenue management"},
                    {"icon": "megaphone", "label": "Digital marketing"},
                    {"icon": "social", "label": "Social media"},
                ],
            },
            {"variant": "lead", "kicker": "", "title": ""},
            {
                "variant": "close",
                "kicker": "Let's begin",
                "title": "Download or get in touch",
            },
        ],
    },
}
