# Copy completo: landing Pullso MVP

Origen: `routes/pullso_mvp_landing_i18n.py` + meta/SEO de `routes/marketing.py` (`_pullso_mvp_home_preview_response`).  
Rutas: `/pullso-mvp` (EN), `/pullso-mvp/es` (ES).

El `<h2 class="sr-only">` de la página repite `meta_description` (SEO), no hay clave i18n aparte.

---

## SEO y meta (no están en el diccionario i18n)

### Español (`es`)

| Campo | Texto |
|-------|--------|
| `meta_title` | Pullso, briefs de revenue en WhatsApp \| DRAGONNÉ |
| `meta_description` | Pullso es un agente de revenue con IA: lee PMS, channel manager y pickup, razona con lógica hotelera y envía a WhatsApp un brief accionable para dirección y revenue. La base para automatizar flujos comerciales manuales sin perder el criterio humano. |
| `twitter_title` | Pullso, briefs de revenue en WhatsApp |
| `robots_meta` | noindex, nofollow |

### English (`en`)

| Campo | Texto |
|-------|--------|
| `meta_title` | Pullso — Hotel revenue briefs in WhatsApp \| DRAGONNÉ |
| `meta_description` | Pullso is an AI-native hotel revenue agent: it ingests PMS and channel-manager signals, reasons with hospitality-grade logic, and posts an actionable brief to WhatsApp for GMs and hybrid commercial teams, with a roadmap to retire manual revenue glue work. |
| `twitter_title` | Pullso — Revenue briefs in WhatsApp |
| `robots_meta` | noindex, nofollow |

---

## Texto fijo en plantilla (mock del teléfono / nav, no i18n)

- Marca nav: **Pullso**
- Reloj status bar: **9:41**
- Título app mock: **Pullso Brief**
- Timestamp mensaje escrito: **09:42**
- Duración nota de voz: **24s**

---

## Inglés (EN)

### Navegación y accesibilidad

- **nav_brand_aria:** Pullso home  
- **nav_sections_aria:** Page sections  
- **nav_why:** Why  
- **nav_product:** Product  
- **nav_vision:** Vision  
- **nav_faq:** FAQ  
- **nav_cta:** Send your details  
- **lang_switch_label:** Español  
- **lang_switch_href:** /pullso-mvp/es  
- **lang_switch_aria:** Ver versión en español  

### Hero

- **hero_section_aria:** Introduction  
- **hero_tag:** An AI revenue analyst in your existing thread  
- **hero_h1_line1:** Hotel revenue intelligence  
- **hero_h1_line2:** that reasons like your best RM.  
- **hero_h1_accent:** Delivered in WhatsApp.  
- **hero_pullso:** Pullso  
- **hero_lede_a:** connects to the signals you already own (PMS, channel manager, pickups, exports) and, using models trained on hotel commercial logic, ships  
- **hero_lede_strong:** one brief your team can execute  
- **hero_lede_b:** in WhatsApp: situation, chain of thought, recommended move, as text, voice, or short clip. It is not a consumer chatbot. It is a scoped agent that reads revenue the way your stack actually behaves, in the vocabulary leadership already expects.  
- **hero_cta1:** Send your details  
- **hero_cta2:** What you get  

**Hero stats**

- **hero_s1t:** One thread  
- **hero_s1b:** One persistent thread the agent remembers, so you stop re-briefing the same story.  
- **hero_s2t:** Grounded reasoning  
- **hero_s2b:** Pace, BAR, mix, compression, argued the way an experienced RM would, not a horizontal “insights” box.  
- **hero_s3t:** Text · voice · clip  
- **hero_s3b:** The same analyst, packaged the way owners and GMs actually consume updates.  

**Tarjetas flotantes**

- **float_a:** Fewer raw numbers  
- **float_a_mid:** →  
- **float_a_end:** clearer meaning  
- **float_b_pre:** One suggested  
- **float_b_em:** action  
- **float_b_post:** at a time  

### Mock WhatsApp

- **device_aria:** Pullso Brief: text, voice, video in WhatsApp  
- **app_badge_live:** Live  
- **app_sub:** End-to-end encrypted · WhatsApp  
- **msg_kicker:** Written brief  
- **msg_title:** Weekend demand is stronger than your public rate suggests.  
- **msg_body:** Raise your best public rate in two steps and protect rooms for direct bookings—demand is there now.  
- **msg_meta:** Hotel logic, not templates  
- **voice_kicker:** Voice  
- **voice_meta:** Bookings · rate · channels  
- **clip_label:** Clip  
- **clip_sub:** 1:12 · rates · channel pressure  

### Carrusel (marquee)

agent, revenue AI, bookings, average rate, occupancy, channels, whatsapp, public rate, automation  

### Prueba social

- **proof_aria:** Who Pullso is for  
- **proof_label:** Designed for  
- **proof_pills:**  
  - Independent hotels & resorts  
  - Small & medium portfolios  
  - Hybrid revenue / e-commerce roles  
  - Groups standardizing commercial rhythm  

### Wedge (problema)

- **wedge_kicker:** Why this exists  
- **wedge_h2:** Revenue still runs on manual glue. AI can retire the grind, not the judgment.  
- **wedge_c1t:** Fragmented signal  
- **wedge_c1p:** PMS, CM, pickup, comps—by the time the picture is assembled, the night may already be mispriced.  
- **wedge_c2t:** Brittle continuity  
- **wedge_c2p:** People change properties; context walks out. Data stays, the story does not.  
- **wedge_c3t:** Charts ≠ decision  
- **wedge_c3p:** Dashboards show history. Owners need one paragraph: what to change *today* on rate and mix.  

### Visión

- **vision_section_aria:** Product vision  
- **vision_kicker:** Where this goes  
- **vision_h2:** From today’s brief to an autonomous commercial operating layer.  
- **vision_p:** Right now Pullso collapses the manual loop: export, pivot, email blast, meeting. Next we extend the same agent backbone across more of that loop with your guardrails: routing, approvals, simulations, so people spend time on judgment, not rebuilding context from five systems every morning.  

### Producto

- **product_kicker:** What the agent delivers  
- **product_h2:** The brief: situation, why it matters, what to do next.  
- **product_lede:** Under the hood, models reason across pace, BAR, mix, and direct-channel pressure with priors built for hotels, not a generic assistant. The output lands where your commercial team already decides, with no new dashboard habit to adopt.  
- **outcomes_h3:** In every drop  
- **o1t:** Situation  
- **o1b:** OCC, ADR, pace—in your team’s vocabulary.  
- **o2t:** Rate & channel read  
- **o2b:** BAR, mix, OTA vs. direct—what’s fragile right now.  
- **o3t:** One primary move  
- **o3b:** Single recommended action so execution isn’t a meeting.  
- **o4t:** Voice / clip  
- **o4b:** Same logic when nobody will open a sheet on mobile.  
- **product_cta:** Send your details  

### Bento (cómo funciona)

- **bento_kicker:** Agent plus your data  
- **bento_h2:** Structured hotel data in; a grounded revenue brief out, same WhatsApp thread.  
- **bento_intro:** Five steps every deployment follows so the agent can keep absorbing more of the manual revenue stack you run today, always auditable and with explicit human checkpoints.  
- **b1k:** Step 1 · Context  
- **b1t1:** One thread,  
- **b1t2:** full memory.  
- **b1s:** Scrollable history: why Tuesday’s rate call happened, not only Wednesday’s PMS delta.  
- **b2k:** Step 2 · Connect  
- **b2t:** Wire up live hotel data  
- **b2s:** Exports and feeds you authorize—refreshed to match how fast you actually move rates.  
- **b3k:** Step 3 · Explain  
- **b3t:** Explained the way your revenue lead would  
- **b3s:** Compression, BAR ladder, and channel mix, narrated with the judgment of a senior analyst, not a chart title pasted into chat.  
- **b4k:** Step 4 · Deliver  
- **b4mono:** Action first  
- **b4s:** Situation, reasoning, move—in text or the same as voice / capsule.  
- **b5k:** Step 5 · Scale  
- **b5t:** Brief becomes operating layer  
- **b5s:** Approvals, routing, escalations, what-if runs: same thread, same agent memory, expanding how much manual process you retire without bolting on another front-office stack.  

### FAQ

- **faq_kicker:** Diligence  
- **faq_h2:** Common questions  
- **faq_intro:** Landing stays short; expanding an item is optional.  

1. **Q:** Is this a chatbot in WhatsApp?  
   **A:** No. Pullso behaves like a scheduled commercial analyst backed by models: it ingests structured hotel data, reasons with property-specific logic, and posts a concise brief (text, optional voice, optional video). You are not expected to prompt it like a consumer chat; it pushes the readout your team agreed to receive, every cycle.  

2. **Q:** What systems do we need connected?  
   **A:** We start from what you already export or can share today—PMS or channel-manager reports, pickup, rate shopping snapshots, and similar. Longer term the same model attaches to live feeds as you grant them. The demo maps your exact source files or APIs.  

3. **Q:** Who is the reader—the GM, revenue manager, or owner?  
   **A:** You choose the distribution list. Most properties route the daily brief to whoever actually moves rates, with a lighter owner-facing version or voice note when the decision needs board-level visibility.  

4. **Q:** Does Pullso replace my RMS or revenue manager?  
   **A:** It does not replace professional judgment or an RMS. It reduces the time from signal to shared understanding so humans spend minutes deciding, not hours reconstructing context—and nobody misses the window because the spreadsheet lived on one laptop.  

5. **Q:** Does this replace our commercial team?  
   **A:** No. It replaces the repetitive glue: re-explaining the workbook, chasing schedules, manually rewriting the narrative each morning. The roadmap is fewer manual threads between the same systems, not fewer strategists.  

### CTA final (rail) + formulario

- **rail_kicker:** Next step  
- **rail_h2:** Tell us how your hotel runs.  
- **rail_p:** If you want Pullso’s agent on your stack, leave your details and the systems you run. We follow up personally. There is no calendar booking or free self-serve signup on this page.  
- **form_aria:** Request follow up from Pullso  
- **form_name_label:** Your name  
- **form_phone_label:** Phone (include country code)  
- **form_email_label:** Work email  
- **form_hotel_label:** Hotel name  
- **form_url_label:** Hotel link  
- **form_url_help:** Official website or OTA listing (Booking, Expedia, etc.)  
- **form_pms_label:** PMS  
- **form_cm_label:** Channel manager  
- **form_be_label:** Booking engine  
- **form_optional_hint:** Optional if not applicable yet  
- **form_submit:** Send my details  
- **form_sending:** Sending…  
- **form_success:** Thanks. We received your details and will contact you soon.  
- **form_error:** We could not send this. Check the fields and try again.  
- **form_error_contact:** If it keeps failing, email us at  

### Pie

- **footer_strong_line:** Pullso  
- **footer_tag:** · DRAGONNÉ · Commercial intelligence for hotels  
- **footer_sub:** AI-native revenue briefs today, plus the path to automating the manual commercial workflows you still run by hand.  
- **footer_why:** Why  
- **footer_product:** Product  
- **footer_vision:** Vision  
- **footer_how:** How it works  
- **footer_faq:** FAQ  
- **footer_demo:** Contact  

---

## Español (ES)

### Navegación y accesibilidad

- **nav_brand_aria:** Inicio Pullso  
- **nav_sections_aria:** Secciones de la página  
- **nav_why:** Por qué  
- **nav_product:** Producto  
- **nav_vision:** Visión  
- **nav_faq:** FAQ  
- **nav_cta:** Enviar mis datos  
- **lang_switch_label:** English  
- **lang_switch_href:** /pullso-mvp  
- **lang_switch_aria:** View English version  

### Hero

- **hero_section_aria:** Introducción  
- **hero_tag:** Un analista de revenue con IA en tu hilo  
- **hero_h1_line1:** Inteligencia de revenue hotelera  
- **hero_h1_line2:** que razona como tu mejor revenue manager.  
- **hero_h1_accent:** Te llega por WhatsApp.  
- **hero_pullso:** Pullso  
- **hero_lede_a:** se conecta a las señales que ya tienes (PMS, channel manager, pickup, exportaciones) y, con modelos entrenados en lógica comercial de hotel, envía  
- **hero_lede_strong:** un brief que tu equipo puede ejecutar  
- **hero_lede_b:** por WhatsApp: situación, cadena de razonamiento y movimiento recomendado, en texto, voz o clip corto. No es un chat de consumo. Es un agente acotado que lee el negocio como se comporta tu stack, en el vocabulario que ya espera dirección.  
- **hero_cta1:** Enviar mis datos  
- **hero_cta2:** Qué incluye  

**Hero stats**

- **hero_s1t:** Un solo hilo  
- **hero_s1b:** Un solo hilo con memoria del agente para no volver a contar la misma historia cada día.  
- **hero_s2t:** Razonamiento fundado  
- **hero_s2b:** Pace, BAR, mix y compresión, argumentados como lo haría un revenue senior, no como una caja horizontal de “insights”.  
- **hero_s3t:** Texto, voz o clip  
- **hero_s3b:** El mismo analista, en el formato que sí abre tu propietario o director general.  

**Tarjetas flotantes**

- **float_a:** Menos números sueltos,  
- **float_a_mid:** más  
- **float_a_end:** sentido comercial  
- **float_b_pre:** Solo una  
- **float_b_em:** acción  
- **float_b_post:** sugerida cada vez  

### Mock WhatsApp

- **device_aria:** Pullso Brief: texto, voz y vídeo en WhatsApp  
- **app_badge_live:** En vivo  
- **app_sub:** Cifrado de extremo a extremo, WhatsApp  
- **msg_kicker:** Brief escrito  
- **msg_title:** La demanda de fin de semana está más fuerte de lo que sugiere tu tarifa pública.  
- **msg_body:** Ajusta tu BAR público en dos pasos y protege inventario para venta directa. La demanda está activa hoy.  
- **msg_meta:** Lógica hotelera, no plantillas  
- **voice_kicker:** Voz  
- **voice_meta:** Reservas, tarifa y canales  
- **clip_label:** Clip  
- **clip_sub:** 1:12, tarifas y presión de canales  

### Carrusel (marquee)

agente, IA revenue, reservas, tarifa media, ocupación, canales, whatsapp, automatización, tarifa pública  

### Prueba social

- **proof_aria:** Para quién es Pullso  
- **proof_label:** Pensado para  
- **proof_pills:**  
  - Hoteles y resorts independientes  
  - Portafolios pequeños y medianos  
  - Roles híbridos de revenue y e-commerce  
  - Cadenas que estandarizan su ritmo comercial  

### Wedge

- **wedge_kicker:** Por qué existe  
- **wedge_h2:** El revenue sigue apoyado en trabajo manual. La IA puede quitar lo repetible, no el criterio.  
- **wedge_c1t:** Señal fragmentada  
- **wedge_c1p:** PMS, CM, pickup y competencia están en distintos lados. Cuando terminas de armar el panorama, esa noche puede quedar ya mal tarifada.  
- **wedge_c2t:** Continuidad frágil  
- **wedge_c2p:** La gente cambia de propiedad; el contexto se pierde. Quedan datos, no la historia.  
- **wedge_c3t:** Un gráfico no es una decisión  
- **wedge_c3p:** Los tableros muestran historia. Dirección necesita un párrafo: qué cambiar *hoy* en tarifa y mix.  

### Visión

- **vision_section_aria:** Visión de producto  
- **vision_kicker:** Hacia dónde va esto  
- **vision_h2:** Del brief de hoy a una capa comercial que automatiza lo repetible.  
- **vision_p:** Ahora Pullso comprime el circuito manual: exportar, pivotear, mandar correos, reunir a todos. Mañana el mismo núcleo de agente puede extenderse a más de ese circuito bajo tus reglas: rutas, aprobaciones, simulaciones, para que el equipo invierta tiempo en el juicio comercial, no en rearmar contexto cada mañana desde cinco sistemas.  

### Producto

- **product_kicker:** Qué entrega el agente  
- **product_h2:** El brief: situación, por qué importa y cuál es el siguiente paso.  
- **product_lede:** Por debajo, modelos cruzan pace, BAR, mix y presión entre canales con prioridades pensadas para hotel, no un asistente genérico. La salida llega donde el equipo comercial ya decide, sin otro tablero que nadie adopta.  
- **outcomes_h3:** En cada envío  
- **o1t:** Situación  
- **o1b:** Ocupación, ADR y pace, con el vocabulario de tu propiedad.  
- **o2t:** Lectura de tarifa y canales  
- **o2b:** BAR, mix, OTA frente a directo. Qué está delicado en este momento.  
- **o3t:** Un movimiento principal  
- **o3b:** Una acción recomendada para que ejecutar no sea una reunión.  
- **o4t:** Voz o clip  
- **o4b:** La misma lógica cuando nadie va a abrir una hoja en el celular.  
- **product_cta:** Enviar mis datos  

### Bento

- **bento_kicker:** Agente más tus datos  
- **bento_h2:** Entran datos estructurados del hotel, sale un brief fundamentado, siempre en el mismo hilo de WhatsApp.  
- **bento_intro:** Cinco pasos en cada implementación para que el agente vaya absorbiendo más del stack manual de revenue que hoy opera tu propiedad, con trazabilidad y puntos explícitos de control humano.  
- **b1k:** Paso 1, contexto  
- **b1t1:** Un hilo,  
- **b1t2:** memoria completa.  
- **b1s:** Historial claro: por qué el martes se sugería mover tarifa, no solo el cambio que ves el miércoles en el PMS.  
- **b2k:** Paso 2, conexión  
- **b2t:** Datos vivos del hotel  
- **b2s:** Archivos y fuentes que el equipo autoriza, actualizados al ritmo en que de verdad mueven tarifas.  
- **b3k:** Paso 3, explicación  
- **b3t:** Explicado como tu revenue lo contaría  
- **b3s:** Compresión, escalera de BAR y mix, narrados con el juicio de un analista senior, no como el título de una gráfica en el chat.  
- **b4k:** Paso 4, entrega  
- **b4mono:** Acción primero  
- **b4s:** Situación, lectura y movimiento, en texto o en voz y cápsula.  
- **b5k:** Paso 5, escala  
- **b5t:** Del brief a capa operativa  
- **b5s:** Aprobaciones, rutas, escalamientos, escenarios: mismo hilo, misma memoria del agente, ampliando cuánto proceso manual retiras sin sumar otro stack de front office.  

### FAQ

- **faq_kicker:** Diligencia  
- **faq_h2:** Preguntas frecuentes  
- **faq_intro:** La página es breve; abrir cada pregunta es opcional.  

1. **Q:** ¿Es un chatbot en WhatsApp?  
   **A:** No. Pullso se comporta como un analista comercial programado sobre modelos: ingiere datos estructurados del hotel, razona con lógica de propiedad y publica un brief concreto (texto, voz o vídeo opcional). No esperamos que lo prompts como un chat de consumo: Pullso empuja la lectura que el equipo acordó recibir, en cada ciclo.  

2. **Q:** ¿Qué sistemas hay que conectar?  
   **A:** Empezamos por lo que ya exportan o pueden compartir: reportes de PMS o channel manager, pickup, capturas de rate shopping, etc. Más adelante el mismo modelo se acopla a fuentes en vivo según permisos. En la demo alineamos tus archivos o APIs reales.  

3. **Q:** ¿Quién lo lee: el director general, revenue o el propietario?  
   **A:** Define la lista (o el equipo comercial). En muchas propiedades el brief diario llega a quien de verdad mueve tarifas, con una versión más sencilla o una nota de voz hacia dirección cuando la decisión es de consejo o corporativo.  

4. **Q:** ¿Pullso reemplaza mi RMS o a mi revenue manager?  
   **A:** No reemplaza criterio humano ni un RMS. Acorta el camino de la señal al entendimiento compartido: la gente decide en minutos, no en horas rearmando contexto, y nadie pierde la ventana porque el Excel vivía en una sola laptop.  

5. **Q:** ¿Esto le quita trabajo a mi equipo comercial o de revenue?  
   **A:** No. Le quita trabajo repetitivo: volver a explicar el libro, perseguir juntas, reescribir la narrativa cada mañana. La apuesta es menos hilos manuales entre los mismos sistemas, no menos personas pensando la estrategia.  

### CTA final + formulario

- **rail_kicker:** Siguiente paso  
- **rail_h2:** Cuéntanos tu operación.  
- **rail_p:** Si quieres el agente de Pullso sobre tu stack, deja tus datos y los sistemas que corren en la propiedad. Damos seguimiento personal. En esta página no hay agenda en caliente ni registro gratis directo.  
- **form_aria:** Solicitud de seguimiento a Pullso  
- **form_name_label:** Nombre  
- **form_phone_label:** Teléfono (con lada)  
- **form_email_label:** Correo electrónico  
- **form_hotel_label:** Nombre del hotel  
- **form_url_label:** Enlace del hotel  
- **form_url_help:** Sitio web oficial o ficha en OTA (Booking, Expedia, etc.)  
- **form_pms_label:** PMS  
- **form_cm_label:** Channel manager  
- **form_be_label:** Motor de reservas  
- **form_optional_hint:** Opcional si aún no aplica  
- **form_submit:** Enviar mis datos  
- **form_sending:** Enviando…  
- **form_success:** Listo. Recibimos tus datos y te contactaremos pronto.  
- **form_error:** No se pudo enviar. Revisa los campos e intenta de nuevo.  
- **form_error_contact:** Si sigue fallando, escríbenos a  

### Pie

- **footer_strong_line:** Pullso  
- **footer_tag:** de DRAGONNÉ. Inteligencia comercial para hoteles  
- **footer_sub:** Briefs de revenue con IA hoy, y la ruta para automatizar los flujos comerciales manuales que aún haces a mano.  
- **footer_why:** Por qué  
- **footer_product:** Producto  
- **footer_vision:** Visión  
- **footer_how:** Cómo funciona  
- **footer_faq:** FAQ  
- **footer_demo:** Contacto  

---

*Generado para revisión de copy. Si editas textos, actualiza `routes/pullso_mvp_landing_i18n.py` y, si aplica, los meta en `routes/marketing.py`.*

</think>


<｜tool▁calls▁begin｜><｜tool▁call▁begin｜>
Grep