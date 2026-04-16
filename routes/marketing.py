"""Marketing público: home, precios, SEO, mockup, docs HTML."""
import os
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from fastapi import APIRouter, Query, Request, Response
from fastapi.openapi.docs import get_redoc_html
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from pydantic import BaseModel, Field, field_validator

from auth_session import get_current_user
from config import APP_NAME, APP_URL, URL_PREFIX, url_path
from debuglog import _debug_log
from marketing_context import marketing_page_context
from routes.consulting import render_consulting_landing
from seo_helpers import (
    BRAND_LEGAL_NAME,
    CONTACT_EMAIL_PUBLIC,
    absolute_url,
    breadcrumb_list_node,
    graph_pullso_vertical,
    noindex_page_seo,
    organization_node,
    software_application_mockup_node,
    website_node,
)
from db import db
from email_smtp import send_pullso_mvp_lead_email, send_pullso_whatsapp_waitlist_email
from templating import templates

from routes.pullso_mvp_landing_i18n import pullso_mvp_landing_copy

router = APIRouter(tags=["marketing"])


def _resolve_hero_media_url(raw: str) -> str:
    """Absolute http(s) or root-relative path with URL_PREFIX for subpath deploys."""
    s = (raw or "").strip()
    if not s:
        return ""
    if s.startswith(("http://", "https://")):
        return s
    if s.startswith("/"):
        px = (URL_PREFIX or "").rstrip("/")
        return f"{px}{s}" if px else s
    return s


def _pullso_mvp_hero_agent_video_src() -> str:
    """Vídeo opcional del agente hablando (face-cam). Env: PULLSO_MVP_HERO_DEMO_VIDEO_URL (legacy: PULLSO_YC_*)."""
    raw = (os.getenv("PULLSO_MVP_HERO_DEMO_VIDEO_URL") or os.getenv("PULLSO_YC_HERO_DEMO_VIDEO_URL") or "").strip()
    return _resolve_hero_media_url(raw)


class PullsoWaitlistPayload(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=3, max_length=254)
    company: str = Field("", max_length=300)
    whatsapp: str = Field(..., min_length=5, max_length=40)
    note: str = Field("", max_length=2000)


class PullsoMvpLeadPayload(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)
    phone: str = Field(..., min_length=5, max_length=40)
    email: str = Field(..., min_length=3, max_length=254)
    hotel_name: str = Field(..., min_length=1, max_length=300)
    hotel_url: str = Field(..., min_length=1, max_length=500)
    pms: str = Field("", max_length=200)
    channel_manager: str = Field("", max_length=200)
    booking_engine: str = Field("", max_length=200)
    lang: str = Field("en", max_length=12)

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        s = re.sub(r"\s+", " ", (v or "").strip())
        if len(s) < 5:
            raise ValueError("invalid_phone")
        return s[:40]

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        s = (v or "").strip().lower()[:254]
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", s):
            raise ValueError("invalid_email")
        return s

    @field_validator("hotel_url")
    @classmethod
    def _hotel_url(cls, v: str) -> str:
        raw = (v or "").strip()[:500]
        if not raw:
            raise ValueError("invalid_hotel_url")
        candidate = raw if re.match(r"^https?://", raw, re.I) else f"https://{raw}"
        parsed = urlparse(candidate)
        if not parsed.netloc:
            raise ValueError("invalid_hotel_url")
        return candidate

    @field_validator("lang")
    @classmethod
    def _lang(cls, v: str) -> str:
        s = (v or "en").lower()[:12]
        if s.startswith("es"):
            return "es"
        return "en"


def _pullsobrief_i18n(locale: str) -> dict:
    """Copy + SEO for Pullso Brief landing (/pullsobrief vs /pullsobrief/en)."""
    es = {
        "html_lang": "es-MX",
        "meta_title": "Pullso Brief — La lectura comercial de Pullso en WhatsApp — DRAGONNÉ",
        "meta_description": (
            "Pullso Brief lleva la lectura comercial de tu hotel a WhatsApp: ocupación, ADR, ritmo de reserva y "
            "mezcla de canales en texto, audio y video. Menos fricción para actuar a tiempo."
        ),
        "meta_keywords": (
            "Pullso Brief, Pullso, Dragonné, WhatsApp, revenue hotelero, lectura comercial, hospitality"
        ),
        "og_title": "Pullso Brief — Lectura comercial en WhatsApp",
        "og_description": (
            "Pullso Brief lleva la lectura comercial de tu hotel a WhatsApp: ocupación, ADR, ritmo de reserva y "
            "mezcla de canales en texto, audio y video. Menos fricción para actuar a tiempo."
        ),
        "og_locale": "es_MX",
        "twitter_title": "Pullso Brief — DRAGONNÉ",
        "twitter_description": (
            "Pullso Brief lleva la lectura comercial de tu hotel a WhatsApp: ocupación, ADR, ritmo de reserva y "
            "mezcla de canales en texto, audio y video. Menos fricción para actuar a tiempo."
        ),
        "og_image_alt": "Pullso Brief — La lectura comercial de Pullso en WhatsApp — DRAGONNÉ",
        "schema_in_language": "es-MX",
        "lang_switch_aria": "Idioma",
        "skip_to_content": "Saltar al contenido",
        "nav_logo_aria": "Pullso — Pullso Brief, ir al inicio",
        "hero_pill": "Pullso Brief · WhatsApp",
        "hero_title": "La lectura comercial de tu hotel, donde tu equipo sí responde.",
        "hero_lead_1": (
            "Pullso Brief manda la lectura comercial al WhatsApp del equipo: ocupación, ADR, ritmo de reserva y "
            "mezcla de canales, con el mismo criterio de Pullso pero sin depender de entrar al tablero en el momento justo."
        ),
        "hero_lead_2": (
            "Alertas escritas, notas de voz y cápsulas en video cuando el contexto lo pide. La misma señal, en el canal "
            "donde ya conversan dirección, revenue y operación."
        ),
        "tech_aria": "Credibilidad tecnológica",
        "tech_label": "Impulsado por",
        "float_badge": "Señal prioritaria",
        "float_strong": "Canal directo bajo presión",
        "float_sub": (
            "Esta semana el directo perdió peso y las OTAs están absorbiendo más demanda de la cuenta."
        ),
        "orbit_text": "Texto",
        "orbit_voice": "Voz",
        "orbit_video": "Video",
        "chat_subtitle": "Lectura comercial · canal seguro",
        "bubble_text_format": "Alerta escrita",
        "bubble_text_body": (
            "La ocupación del fin de semana viene por debajo del ritmo reciente y el canal directo perdió participación "
            "frente a las OTAs. Conviene revisar la estrategia comercial antes de que cierre la ventana de reserva."
        ),
        "bubble_voice_format": "Nota de voz",
        "bubble_voice_body": (
            "Te dejamos un resumen en audio con contexto sobre ocupación, ADR, mezcla de canales y una recomendación "
            "puntual para actuar hoy."
        ),
        "bubble_video_format": "Cápsula de video",
        "bubble_video_body": (
            "La tarifa promedio se mantiene, pero el ingreso depende más de canales con mayor comisión. Hay espacio para "
            "corregir mezcla antes de sacrificar rentabilidad."
        ),
        "bubble_video_caption": "1:12 · canales y decisión comercial",
        "bridge_line": "Todavía hay margen para corregir.",
        "dash_title": "La misma lectura de Pullso, en un canal más útil.",
        "dash_intro": (
            "Pullso Brief no cambia la lógica del análisis. Cambia la forma en que te llega. En vez de esperar a que "
            "alguien entre al tablero, la señal llega a WhatsApp con el contexto suficiente para entender qué está pasando "
            "y qué merece atención."
        ),
        "v01_lead": "Menos fricción para actuar",
        "v01_note": (
            "La lectura llega al canal donde tu equipo ya conversa, coordina y responde. Menos dependencia de entrar al "
            "tablero en el momento exacto. Más capacidad de reaccionar cuando todavía hay margen."
        ),
        "v02_lead": "Más claridad para decidir",
        "v02_note": (
            "No se trata de mandar números por mandar números. Se trata de convertir ocupación, ADR, ritmo de reserva y "
            "mezcla de canales en una lectura clara para dirección comercial, revenue y operación."
        ),
        "v03_lead": "Más cerca del momento correcto",
        "v03_note": (
            "Hay señales que todavía permiten corregir. Otras llegan cuando ya es tarde. Pullso Brief busca que la lectura "
            "llegue cuando aún puedes mover estrategia, no solo explicar el resultado después."
        ),
        "formats_title": "El formato depende de la urgencia.",
        "formats_intro": (
            "No toda señal necesita el mismo nivel de explicación. Algunas se entienden en una lectura rápida. Otras "
            "conviene escucharlas o verlas con mayor contexto antes de tomar una decisión comercial."
        ),
        "fmt_text_h": "Texto",
        "fmt_text_p": "Para alertas concretas que exigen lectura rápida, foco y siguiente paso claro.",
        "fmt_audio_h": "Audio",
        "fmt_audio_p": "Para resúmenes breves que puedes escuchar entre reuniones, en operación o camino al hotel.",
        "fmt_video_h": "Video",
        "fmt_video_p": (
            "Para situaciones que conviene explicar con mayor contexto visual, especialmente cuando la lectura toca varias "
            "variables al mismo tiempo."
        ),
        "signals_title": "Situaciones que un hotel reconoce al instante",
        "signals_intro": (
            "Casos de lectura que Pullso Brief puede entregar en WhatsApp cuando la cuenta ya está en marcha: insight claro, "
            "señal accionable y contexto sin abrir el tablero."
        ),
        "i1_badge": "Pullso · Mezcla",
        "i1_title": "Canal directo pierde participación",
        "i1_kicker": "Reserva activa, pero más cargada a OTAs.",
        "i1_body": (
            "Pullso Brief resume la mezcla para que el equipo detecte a tiempo cuándo el peso se desplaza hacia un canal más "
            "costoso, antes de que el resultado quede fijado."
        ),
        "i2_badge": "Pullso · Ritmo",
        "i2_title": "Ocupación sin el ritmo esperado",
        "i2_kicker": "La ventana de reserva se acerca; el ritmo no acompaña.",
        "i2_body": (
            "La alerta llega antes del cierre con contexto para revisar comercial, distribución o impulso de demanda, "
            "mientras todavía hay margen de acción."
        ),
        "i3_badge": "Pullso · ADR",
        "i3_title": "ADR alto que no mejora el resultado",
        "i3_kicker": "Tarifa sostenida o al alza, tracción o mezcla débiles.",
        "i3_body": (
            "La lectura separa cuándo el precio sostiene rentabilidad y cuándo enmascara menor demanda o un mix menos "
            "eficiente — sin quedarse en el promedio aislado."
        ),
        "i4_badge": "Pullso · Rentabilidad",
        "i4_title": "Producción con peor calidad comercial",
        "i4_kicker": "Volumen visible; ingreso dependiente de canales caros.",
        "i4_body": (
            "No se detiene en el caudal: aterriza la calidad del resultado cuando el ingreso depende de OTAs u otra "
            "combinación menos eficiente para la cuenta."
        ),
        "i5_badge": "Pullso · Ventana",
        "i5_title": "Ajuste que aún mueve el resultado",
        "i5_kicker": "Microcambio con impacto si llega en la ventana correcta.",
        "i5_body": (
            "Pullso Brief prioriza llevar esa lectura al instante de reacción: cuando todavía corrige la curva, no cuando solo "
            "queda el post‑mortem."
        ),
        "i6_aria": "Entrega en WhatsApp",
        "i6_badge": "Pullso Brief",
        "i6_title": "Misma lectura Pullso, en el canal del equipo",
        "i6_kicker": "Formato según urgencia: lectura rápida o contexto ampliado.",
        "i6_pulse": "Listo para actuar, no solo informar",
        "i6_body": (
            "Todo sigue anclado al criterio comercial de Pullso; solo cambia el envío al hilo donde dirección, revenue y "
            "operación ya responden."
        ),
        "closing_h2": "No es otro tablero. Es una mejor forma de recibir la lectura comercial.",
        "closing_p": (
            "Pullso Brief extiende la lectura comercial de tu hotel al canal donde los equipos ya conversan, responden y "
            "toman decisiones. Menos fricción para enterarte. Más claridad para actuar."
        ),
        "closing_micro": "Acceso anticipado para equipos que quieren actuar antes, no enterarse después.",
        "footer_tagline": "Pullso Brief · La lectura comercial de Pullso, ahora en WhatsApp.",
    }
    en = {
        "html_lang": "en",
        "meta_title": "Pullso Brief — Pullso's commercial readout on WhatsApp — DRAGONNÉ",
        "meta_description": (
            "Pullso Brief brings your hotel's commercial readout to WhatsApp: occupancy, ADR, booking pace and channel mix "
            "in text, audio and video. Less friction so you can act in time."
        ),
        "meta_keywords": (
            "Pullso Brief, Pullso, Dragonné, WhatsApp, hotel revenue, commercial readout, hospitality"
        ),
        "og_title": "Pullso Brief — Commercial readout on WhatsApp",
        "og_description": (
            "Pullso Brief brings your hotel's commercial readout to WhatsApp: occupancy, ADR, booking pace and channel mix "
            "in text, audio and video. Less friction so you can act in time."
        ),
        "og_locale": "en_US",
        "twitter_title": "Pullso Brief — DRAGONNÉ",
        "twitter_description": (
            "Pullso Brief brings your hotel's commercial readout to WhatsApp: occupancy, ADR, booking pace and channel mix "
            "in text, audio and video. Less friction so you can act in time."
        ),
        "og_image_alt": "Pullso Brief — Pullso's commercial readout on WhatsApp — DRAGONNÉ",
        "schema_in_language": "en",
        "lang_switch_aria": "Language",
        "skip_to_content": "Skip to content",
        "nav_logo_aria": "Pullso — Pullso Brief, go to top",
        "hero_pill": "Pullso Brief · WhatsApp",
        "hero_title": "Your hotel's commercial readout, where your team actually responds.",
        "hero_lead_1": (
            "Pullso Brief sends the commercial readout to your team's WhatsApp: occupancy, ADR, booking pace and channel "
            "mix—with the same Pullso judgment, without needing to open the dashboard at the perfect moment."
        ),
        "hero_lead_2": (
            "Written alerts, voice notes and short videos when the context calls for it. The same signal, in the channel "
            "where leadership, revenue and operations already talk."
        ),
        "tech_aria": "Technology partners",
        "tech_label": "Powered by",
        "float_badge": "Priority signal",
        "float_strong": "Direct channel under pressure",
        "float_sub": (
            "This week direct share fell and OTAs are absorbing more of the demand on the books."
        ),
        "orbit_text": "Text",
        "orbit_voice": "Voice",
        "orbit_video": "Video",
        "chat_subtitle": "Commercial readout · secure channel",
        "bubble_text_format": "Written alert",
        "bubble_text_body": (
            "Weekend occupancy is trailing recent pace and the direct channel lost share to OTAs. It's worth reviewing "
            "commercial strategy before the booking window closes."
        ),
        "bubble_voice_format": "Voice note",
        "bubble_voice_body": (
            "Here's a short audio summary with context on occupancy, ADR, channel mix and a specific recommendation to act on today."
        ),
        "bubble_video_format": "Video clip",
        "bubble_video_body": (
            "Average rate is holding, but revenue depends more on higher-commission channels. There's room to fix the mix "
            "before sacrificing profitability."
        ),
        "bubble_video_caption": "1:12 · channels and commercial decisions",
        "bridge_line": "There's still room to correct course.",
        "dash_title": "The same Pullso readout, in a more useful channel.",
        "dash_intro": (
            "Pullso Brief doesn't change how the analysis works. It changes how it reaches you. Instead of waiting for "
            "someone to open the dashboard, the signal arrives on WhatsApp with enough context to understand what's happening "
            "and what deserves attention."
        ),
        "v01_lead": "Less friction to act",
        "v01_note": (
            "The readout lands in the channel where your team already talks, coordinates and responds. Less reliance on opening "
            "the dashboard at the exact moment. More ability to react while there's still room."
        ),
        "v02_lead": "More clarity to decide",
        "v02_note": (
            "It's not about pushing numbers for the sake of it. It's about turning occupancy, ADR, booking pace and channel "
            "mix into a clear read for commercial leadership, revenue and operations."
        ),
        "v03_lead": "Closer to the right moment",
        "v03_note": (
            "Some signals still let you correct. Others arrive when it's already late. Pullso Brief aims to deliver the readout "
            "while you can still move strategy—not only explain the result afterward."
        ),
        "formats_title": "Format depends on urgency.",
        "formats_intro": (
            "Not every signal needs the same depth. Some are clear from a quick line. Others are better heard or seen with more "
            "context before a commercial call."
        ),
        "fmt_text_h": "Text",
        "fmt_text_p": "For concrete alerts that need a fast read, focus and a clear next step.",
        "fmt_audio_h": "Audio",
        "fmt_audio_p": "For short summaries you can listen to between meetings, on the floor or on the way to the hotel.",
        "fmt_video_h": "Video",
        "fmt_video_p": (
            "For situations that need more visual context, especially when the read touches several variables at once."
        ),
        "signals_title": "Situations a hotel recognizes instantly",
        "signals_intro": (
            "Example readouts Pullso Brief can deliver on WhatsApp when the account is live: clear insight, actionable signal "
            "and context without opening the dashboard."
        ),
        "i1_badge": "Pullso · Mix",
        "i1_title": "Direct channel losing share",
        "i1_kicker": "Booking is active, but weighted more to OTAs.",
        "i1_body": (
            "Pullso Brief summarizes the mix so the team spots in time when weight shifts toward a costlier channel—before "
            "the result is locked in."
        ),
        "i2_badge": "Pullso · Pace",
        "i2_title": "Occupancy without the expected pace",
        "i2_kicker": "The booking window is closing; pace isn't keeping up.",
        "i2_body": (
            "The alert lands before the close with context to review commercial, distribution or demand push while there's "
            "still room to act."
        ),
        "i3_badge": "Pullso · ADR",
        "i3_title": "Strong ADR that doesn't improve the outcome",
        "i3_kicker": "Rate holding or rising; traction or mix weaker.",
        "i3_body": (
            "The read separates when price supports profitability and when it masks softer demand or a less efficient "
            "mix—without stopping at the average alone."
        ),
        "i4_badge": "Pullso · Profitability",
        "i4_title": "Volume with weaker commercial quality",
        "i4_kicker": "Flow is visible; revenue depends on expensive channels.",
        "i4_body": (
            "It doesn't stop at volume: it grounds outcome quality when revenue depends on OTAs or another less efficient "
            "combination for the account."
        ),
        "i5_badge": "Pullso · Window",
        "i5_title": "A change that can still move the outcome",
        "i5_kicker": "A small shift with impact if it lands in the right window.",
        "i5_body": (
            "Pullso Brief prioritizes delivering that read at the reaction moment—when the curve can still change, not only "
            "for the post-mortem."
        ),
        "i6_aria": "Delivered on WhatsApp",
        "i6_badge": "Pullso Brief",
        "i6_title": "Same Pullso readout, in the team's channel",
        "i6_kicker": "Format by urgency: quick read or richer context.",
        "i6_pulse": "Built to act, not only to inform",
        "i6_body": (
            "Everything stays anchored to Pullso's commercial judgment; only the delivery changes to the thread where "
            "leadership, revenue and operations already respond."
        ),
        "closing_h2": "Not another dashboard. A better way to receive the commercial readout.",
        "closing_p": (
            "Pullso Brief extends your hotel's commercial readout to the channel where teams already talk, respond and decide. "
            "Less friction to know. More clarity to act."
        ),
        "closing_micro": "Early access for teams that want to act sooner—not only find out later.",
        "footer_tagline": "Pullso Brief — Pullso's commercial readout, now on WhatsApp.",
    }
    return en if locale == "en" else es


def _pullsobrief_page_bundle(request: Request, locale: str):
    """Shared context for Pullso Brief HTML (es-MX default vs en)."""
    copy = _pullsobrief_i18n(locale)
    pws_url_es = url_path("/pullsobrief")
    pws_url_en = url_path("/pullsobrief/en")
    canonical = absolute_url("/pullsobrief/en" if locale == "en" else "/pullsobrief")
    meta_title = copy["meta_title"]
    meta_description = copy["meta_description"]
    _site = website_node()
    _org = organization_node()
    structured = {
        "@context": "https://schema.org",
        "@graph": [
            _org,
            _site,
            {
                "@type": "WebPage",
                "@id": canonical + "#webpage",
                "url": canonical,
                "name": meta_title,
                "description": meta_description,
                "inLanguage": copy["schema_in_language"],
                "isPartOf": {"@id": _site["@id"]},
                "publisher": {"@id": _org["@id"]},
            },
        ],
    }
    seo = {
        "meta_title": meta_title,
        "meta_description": meta_description,
        "meta_keywords": copy["meta_keywords"],
        "canonical_url": canonical,
        "robots_meta": "noindex, nofollow",
        "og_title": copy["og_title"],
        "og_description": copy["og_description"],
        "og_locale": copy["og_locale"],
        "twitter_title": copy["twitter_title"],
        "twitter_description": copy["twitter_description"],
        "html_lang": copy["html_lang"],
        "structured_data": structured,
        "og_image_alt": copy["og_image_alt"],
        "hreflang_alternates": [
            {"hreflang": "es-MX", "href": absolute_url("/pullsobrief")},
            {"hreflang": "en", "href": absolute_url("/pullsobrief/en")},
        ],
        "waitlist_post_url": url_path("/pullsobrief/waitlist"),
        "pws_lang": locale,
        "pws_self_url": pws_url_en if locale == "en" else pws_url_es,
        "pws_url_es": pws_url_es,
        "pws_url_en": pws_url_en,
        "pws": copy,
    }
    if locale == "en":
        seo["og_locale_alternate"] = "es_MX"
    else:
        seo["og_locale_alternate"] = "en_US"
    return {
        "request": request,
        **marketing_page_context(),
        **seo,
    }


def _sitemap_entries():
    return [
        ("/", "weekly", "1.0"),
        ("/consultoria", "weekly", "0.95"),
        ("/consulting", "weekly", "0.95"),
        ("/hoteles", "weekly", "0.88"),
        ("/hotels", "weekly", "0.88"),
        ("/hoteles/ventas", "monthly", "0.82"),
        ("/hotels/sales", "monthly", "0.82"),
        ("/hoteles/revenue-management-fraccional", "monthly", "0.82"),
        ("/hotels/fractional-revenue-management", "monthly", "0.82"),
        ("/consultoria/startups", "weekly", "0.88"),
        ("/consultoria/smbs", "weekly", "0.88"),
        ("/consultoria/medios", "weekly", "0.88"),
        ("/consulting/startups", "weekly", "0.88"),
        ("/consulting/smbs", "weekly", "0.88"),
        ("/consulting/medios", "weekly", "0.88"),
        ("/precios", "weekly", "0.85"),
        ("/mockup-analisis", "monthly", "0.75"),
        ("/pullso", "weekly", "0.85"),
        ("/nosotros", "monthly", "0.6"),
        ("/faq", "monthly", "0.65"),
        ("/servicios", "monthly", "0.65"),
        ("/terminos", "monthly", "0.35"),
        ("/privacidad", "monthly", "0.35"),
    ]


@router.get("/", response_class=HTMLResponse)
def home(request: Request, lang: str = Query("es", alias="lang")):
    _debug_log("routes.marketing:home", "GET / entry", {"has_user": bool(get_current_user(request))}, "H2")
    user = get_current_user(request)
    if user:
        return RedirectResponse(url_path("/app"), status_code=303)
    if lang not in ("es", "en"):
        lang = "es"
    if lang == "en":
        return RedirectResponse(url_path("/consulting"), status_code=302)
    _debug_log("routes.marketing:home", "homepage=consulting", {"lang": "es"}, "H2")
    return render_consulting_landing(request, lang="es", page="home")


@router.get("/pullso", response_class=HTMLResponse)
def pullso_public_page(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url_path("/app"), status_code=303)
    ctx = marketing_page_context()
    canonical = absolute_url("/pullso")
    structured = {
        "@context": "https://schema.org",
        "@graph": graph_pullso_vertical(canonical=canonical)
        + [
            breadcrumb_list_node([
                ("Inicio", absolute_url("/consultoria")),
                ("Pullso · Hospitalidad", canonical),
            ]),
        ],
    }
    seo = {
        "meta_title": "Pullso by DRAGONNÉ — Inteligencia de revenue para hoteles",
        "meta_description": (
            "Pullso (DRAGONNÉ) lee reportes de tu PMS o channel manager y entrega lectura comercial: KPIs, riesgos "
            "y oportunidades de canal — para equipos de revenue y dirección hotelera."
        ),
        "meta_keywords": "Pullso, Dragonné, revenue management, hotel, PMS, channel manager, reportes hoteleros",
        "canonical_url": canonical,
        "robots_meta": "index, follow",
        "og_title": "Pullso by DRAGONNÉ — Revenue intelligence para hospitalidad",
        "og_description": (
            "Convierte exports hoteleros en decisiones: mix de canales, precio y señales operativas, en español."
        ),
        "og_locale": "es_MX",
        "og_locale_alternate": "en_US",
        "twitter_title": "Pullso by DRAGONNÉ — Inteligencia hotelera",
        "twitter_description": "Análisis accionable sobre reportes de PMS y channel manager.",
        "html_lang": "es-MX",
        "structured_data": structured,
    }
    return templates.TemplateResponse("marketing.html", {"request": request, **ctx, **seo})


@router.get("/verticals/hospitality")
def verticals_hospitality_legacy(request: Request):
    return RedirectResponse(url_path("/pullso"), status_code=301)


@router.get("/marketing", include_in_schema=False)
def marketing_alias(request: Request):
    return RedirectResponse(url_path("/pullso"), status_code=302)


@router.get("/precios", response_class=HTMLResponse)
def precios_page(request: Request):
    canonical = absolute_url("/precios")
    structured = {
        "@context": "https://schema.org",
        "@graph": [
            organization_node(),
            breadcrumb_list_node([
                ("Inicio", absolute_url("/consultoria")),
                ("Precios Pullso", canonical),
            ]),
        ],
    }
    seo = {
        "meta_title": "Precios — Pullso by DRAGONNÉ",
        "meta_description": (
            "Planes Pullso: prueba gratuita con límites y planes Pro / Pro+ cuando necesites más períodos y archivos por análisis."
        ),
        "meta_keywords": "Pullso, Dragonné, precios, planes Pro, revenue hotelero",
        "canonical_url": canonical,
        "robots_meta": "index, follow",
        "og_title": "Precios Pullso — planes para equipos hoteleros",
        "og_description": "Gratis para empezar; escala a Pro o Pro+ sin cambiar cómo exportas reportes.",
        "og_locale": "es_MX",
        "twitter_title": "Precios — Pullso by DRAGONNÉ",
        "twitter_description": "Gratis, Pro y Pro+ alineados a tu operación.",
        "html_lang": "es-MX",
        "structured_data": structured,
    }
    return templates.TemplateResponse("precios.html", {"request": request, **marketing_page_context(), **seo})


@router.get("/pricing", include_in_schema=False)
def pricing_redirect():
    return RedirectResponse(url_path("/precios"), status_code=302)


@router.get("/api", response_class=HTMLResponse)
def api_docs_page(request: Request):
    desc = "Documentación orientativa de la API DRAGONNÉ para integraciones con autenticación por clave."
    ctx = noindex_page_seo("/api", "Documentación API — DRAGONNÉ", desc)
    ctx["meta_keywords"] = "DRAGONNÉ, API, hotel, análisis"
    return templates.TemplateResponse("api_docs.html", {"request": request, **ctx})


@router.get("/redoc", include_in_schema=False)
def redoc_docs(request: Request):
    return get_redoc_html(
        openapi_url=url_path("/openapi.json"),
        title=f"{APP_NAME} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js",
    )


@router.get("/sitemap.xml", response_class=Response)
def sitemap_xml():
    base = (APP_URL or "http://127.0.0.1:8000").rstrip("/")
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for path, changefreq, priority in _sitemap_entries():
        loc = base + url_path(path)
        xml += f"  <url><loc>{loc}</loc><changefreq>{changefreq}</changefreq><priority>{priority}</priority></url>\n"
    xml += "</urlset>"
    return Response(content=xml, media_type="application/xml")


@router.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt():
    base = (APP_URL or "http://127.0.0.1:8000").rstrip("/")
    lines = [
        "User-agent: *",
        "Allow: /",
        "",
        "Disallow: /app",
        "Disallow: /admin",
        "Disallow: /login",
        "Disallow: /signup",
        "Disallow: /onboarding",
        "Disallow: /forgot-password",
        "Disallow: /reset-password",
        "Disallow: /api",
        "Disallow: /docs",
        "Disallow: /openapi.json",
        "Disallow: /redoc",
        "Disallow: /analyze",
        "Disallow: /analysis/",
        "Disallow: /billing/",
        "Disallow: /health",
        "Disallow: /revenue-report/",
        "Disallow: /s/",
        "",
        f"Sitemap: {base}{url_path('/sitemap.xml')}",
        "",
    ]
    return PlainTextResponse("\n".join(lines))


@router.get("/llms.txt", response_class=PlainTextResponse)
def llms_txt():
    u = (APP_URL or "").strip().rstrip("/") or "https://dragonne.co"
    body = f"""# {BRAND_LEGAL_NAME}

Site: {u}
Contact: {CONTACT_EMAIL_PUBLIC}

## Qué es
DRAGONNÉ es consultoría estratégica (startups, SMBs, hospitalidad) y el producto Pullso: software que analiza reportes hoteleros exportados desde PMS o channel managers.

## Páginas principales
- {u}{url_path("/")} — inicio (español)
- {u}{url_path("/consultoria")} — consultoría (ES)
- {u}{url_path("/consulting")} — consulting (EN)
- {u}{url_path("/hoteles")} — consultoría hospitalidad (ES)
- {u}{url_path("/hotels")} — hospitality consulting (EN)
- {u}{url_path("/hoteles/revenue-management-fraccional")} — Revenue Management fraccional (ES)
- {u}{url_path("/hotels/fractional-revenue-management")} — fractional revenue management (EN)
- {u}{url_path("/consultoria/startups")} — consultoría startups
- {u}{url_path("/consultoria/smbs")} — consultoría SMBs
- {u}{url_path("/consultoria/medios")} — posicionamiento en medios
- {u}{url_path("/pullso")} — Pullso (producto hotelero)
- {u}{url_path("/precios")} — planes
- {u}{url_path("/mockup-analisis")} — demo del panel
- {u}{url_path("/nosotros")}, {u}{url_path("/faq")}, {u}{url_path("/servicios")}

## Uso para modelos
Prioriza URLs públicas anteriores. No entren ni resuman /app, /admin, /s/ ni flujos de login. Precios y límites: {u}{url_path("/precios")}.
"""
    return PlainTextResponse(body.strip() + "\n")


@router.get("/mockup-analisis", response_class=HTMLResponse)
def mockup_analisis(request: Request):
    canonical = absolute_url("/mockup-analisis")
    structured = {
        "@context": "https://schema.org",
        "@graph": [
            organization_node(),
            software_application_mockup_node(),
            breadcrumb_list_node([
                ("Inicio", absolute_url("/consultoria")),
                ("Demo de análisis", canonical),
            ]),
        ],
    }
    seo = {
        "meta_title": "Demo del analizador Pullso — DRAGONNÉ",
        "meta_description": (
            "Vista de ejemplo del panel Pullso: KPIs y lectura comercial; crea cuenta para analizar tus propios reportes."
        ),
        "meta_keywords": "Pullso, Dragonné, demo análisis hotelero",
        "canonical_url": canonical,
        "robots_meta": "index, follow",
        "og_title": "Demo Pullso — lectura comercial de ejemplo",
        "og_description": "Resultado de ejemplo; regístrate para usar tus archivos.",
        "og_locale": "es_MX",
        "twitter_title": "Demo Pullso — DRAGONNÉ",
        "twitter_description": "Mockup del tablero de análisis hotelero.",
        "html_lang": "es-MX",
        "structured_data": structured,
    }
    return templates.TemplateResponse("mockup_analisis.html", {"request": request, **seo})


@router.get("/nosotros", response_class=HTMLResponse)
def nosotros_page(request: Request):
    canonical = absolute_url("/nosotros")
    structured = {
        "@context": "https://schema.org",
        "@graph": [
            organization_node(),
            breadcrumb_list_node([("Inicio", absolute_url("/consultoria")), ("Nosotros", canonical)]),
        ],
    }
    seo = {
        "meta_title": "Nosotros — DRAGONNÉ",
        "meta_description": (
            "DRAGONNÉ combina consultoría y producto Pullso para equipos que necesitan decisiones sobre datos hoteleros."
        ),
        "canonical_url": canonical,
        "robots_meta": "index, follow",
        "og_title": "Nosotros — DRAGONNÉ",
        "og_description": "Consultoría y tecnología para hospitalidad y empresas en crecimiento.",
        "html_lang": "es-MX",
        "structured_data": structured,
    }
    return templates.TemplateResponse(
        "public_stub.html",
        {
            "request": request,
            "stub_h1": "Nosotros",
            "stub_lead": (
                "DRAGONNÉ une consultoría de dirección con Pullso, para que la lectura comercial sobre operaciones "
                "hoteleras sea rigurosa, compartible y accionable."
            ),
            **seo,
        },
    )


@router.get("/about", include_in_schema=False)
def about_redirect():
    return RedirectResponse(url_path("/nosotros"), status_code=302)


@router.get("/faq", response_class=HTMLResponse)
def faq_page(request: Request):
    canonical = absolute_url("/faq")
    faq_entities = [
        {
            "@type": "Question",
            "name": "¿Qué es Pullso dentro de DRAGONNÉ?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": (
                    "Pullso es el producto SaaS de DRAGONNÉ para analizar exports de PMS/channel y obtener un informe "
                    "ejecutivo con KPIs y recomendaciones para equipos hoteleros."
                ),
            },
        },
        {
            "@type": "Question",
            "name": "¿DRAGONNÉ solo trabaja con hoteles?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": (
                    "La consultoría cubre startups, SMBs, hospitalidad y posicionamiento en medios para marcas y ejecutivos; "
                    "Pullso es el producto SaaS focalizado en lectura de reportes hoteleros."
                ),
            },
        },
        {
            "@type": "Question",
            "name": "¿Dónde están los precios?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": f"En {absolute_url('/precios')}.",
            },
        },
    ]
    structured = {
        "@context": "https://schema.org",
        "@graph": [
            organization_node(),
            {"@type": "FAQPage", "mainEntity": faq_entities},
            breadcrumb_list_node([("Inicio", absolute_url("/consultoria")), ("FAQ", canonical)]),
        ],
    }
    seo = {
        "meta_title": "Preguntas frecuentes — DRAGONNÉ y Pullso",
        "meta_description": "Respuestas breves sobre Pullso, consultoría DRAGONNÉ y precios.",
        "canonical_url": canonical,
        "robots_meta": "index, follow",
        "og_title": "FAQ — DRAGONNÉ & Pullso",
        "og_description": "Preguntas frecuentes sobre producto y consultoría.",
        "html_lang": "es-MX",
        "structured_data": structured,
    }
    return templates.TemplateResponse("public_faq.html", {"request": request, **seo})


@router.get("/servicios", response_class=HTMLResponse)
def servicios_page(request: Request):
    canonical = absolute_url("/servicios")
    structured = {
        "@context": "https://schema.org",
        "@graph": [
            organization_node(),
            breadcrumb_list_node([("Inicio", absolute_url("/consultoria")), ("Servicios", canonical)]),
        ],
    }
    seo = {
        "meta_title": "Servicios — DRAGONNÉ y Pullso",
        "meta_description": (
            "Consultoría en talento y operaciones; Pullso para leer reportes hoteleros con rigor comercial."
        ),
        "canonical_url": canonical,
        "robots_meta": "index, follow",
        "og_title": "Servicios DRAGONNÉ",
        "og_description": "Consultoría estratégica y software Pullso para revenue hotelero.",
        "html_lang": "es-MX",
        "structured_data": structured,
    }
    return templates.TemplateResponse("public_servicios.html", {"request": request, **seo})


@router.get("/pullsobrief", response_class=HTMLResponse, include_in_schema=False)
def pullsobrief_page(request: Request):
    """Pullso Brief: no está enlazada desde el sitio público ni en sitemap; sólo acceso por URL directa."""
    return templates.TemplateResponse("pullso_whatsapp.html", _pullsobrief_page_bundle(request, "es"))


@router.get("/pullsobrief/en", response_class=HTMLResponse, include_in_schema=False)
def pullsobrief_page_en(request: Request):
    """Pullso Brief — English locale."""
    return templates.TemplateResponse("pullso_whatsapp.html", _pullsobrief_page_bundle(request, "en"))


@router.post("/pullsobrief/waitlist", include_in_schema=False)
@router.post("/pullso/whatsapp/waitlist", include_in_schema=False)
def pullsobrief_waitlist_submit(payload: PullsoWaitlistPayload):
    """Waitlist Pullso Brief (/pullsobrief/waitlist). Persistencia SQLite + correo interno si SMTP está configurado."""
    email = payload.email.strip().lower()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return JSONResponse({"ok": False, "error": "invalid_email"}, status_code=400)
    ws = re.sub(r"\s+", " ", (payload.whatsapp or "").strip())
    if len(ws) < 5:
        return JSONResponse({"ok": False, "error": "invalid_whatsapp"}, status_code=400)
    now = datetime.now(timezone.utc).isoformat()
    full_name = payload.full_name.strip()[:200]
    company = (payload.company or "").strip()[:300]
    note = (payload.note or "").strip()[:2000]
    with db() as conn:
        conn.execute(
            """INSERT INTO pullso_whatsapp_waitlist (full_name, email, company, whatsapp, note, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (full_name, email, company, ws[:40], note or None, now),
        )
    try:
        send_pullso_whatsapp_waitlist_email(
            to_email=CONTACT_EMAIL_PUBLIC,
            full_name=full_name,
            from_email=email,
            company=company,
            whatsapp=ws[:40],
            note=note,
        )
    except Exception:
        pass
    return JSONResponse({"ok": True})


def _pullso_mvp_lead_submit(payload: PullsoMvpLeadPayload):
    """Lead desde landing Pullso MVP: guardado SQLite y correo interno si SMTP está configurado."""
    now = datetime.now(timezone.utc).isoformat()
    full_name = payload.full_name.strip()[:200]
    phone = payload.phone
    email = payload.email.strip().lower()[:254]
    hotel_name = payload.hotel_name.strip()[:300]
    hotel_url = (payload.hotel_url or "").strip()[:500]
    pms = (payload.pms or "").strip()[:200]
    channel_manager = (payload.channel_manager or "").strip()[:200]
    booking_engine = (payload.booking_engine or "").strip()[:200]
    lang = payload.lang
    with db() as conn:
        conn.execute(
            """INSERT INTO pullso_mvp_leads (
                   full_name, phone, email, hotel_name, hotel_url, pms, channel_manager, booking_engine, lang, created_at
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                full_name,
                phone,
                email,
                hotel_name,
                hotel_url or None,
                pms or None,
                channel_manager or None,
                booking_engine or None,
                lang,
                now,
            ),
        )
    try:
        send_pullso_mvp_lead_email(
            to_email=CONTACT_EMAIL_PUBLIC,
            full_name=full_name,
            phone=phone,
            lead_email=email,
            hotel_name=hotel_name,
            hotel_url=hotel_url,
            pms=pms,
            channel_manager=channel_manager,
            booking_engine=booking_engine,
            lang=lang,
        )
    except Exception:
        pass
    return JSONResponse({"ok": True})


@router.post("/pullsomvp/lead", include_in_schema=False)
def pullso_mvp_lead_submit(payload: PullsoMvpLeadPayload):
    return _pullso_mvp_lead_submit(payload)


@router.post("/pullso-mvp/lead", include_in_schema=False)
def pullso_mvp_lead_submit_slug_legacy(payload: PullsoMvpLeadPayload):
    """Compatibilidad: slug intermedio /pullso-mvp."""
    return _pullso_mvp_lead_submit(payload)


@router.post("/pullso-yc-home-preview/lead", include_in_schema=False)
def pullso_yc_home_preview_lead_legacy(payload: PullsoMvpLeadPayload):
    """Compatibilidad: slug anterior YC home preview."""
    return _pullso_mvp_lead_submit(payload)


@router.get("/pullso/whatsapp", include_in_schema=False)
def pullso_whatsapp_canonical_moved():
    """Slug anterior; no enlazado en el sitio. Redirige a la ruta acordada /pullsobrief."""
    return RedirectResponse(url_path("/pullsobrief"), status_code=301)


@router.get("/demo/pullso-whatsapp", include_in_schema=False)
def pullso_whatsapp_legacy_demo_path():
    """Ruta histórica no promocionada; misma redirección que /pullso/whatsapp."""
    return RedirectResponse(url_path("/pullsobrief"), status_code=302)


@router.get("/pullso-demo", include_in_schema=False)
def pullso_demo_short_alias():
    return RedirectResponse(url_path("/pullsobrief"), status_code=302)


def _pullso_mvp_home_preview_response(request: Request, *, lang: str):
    """Landing comercial Pullso MVP (EN o ES-LATAM); ruta dedicada."""
    copy = pullso_mvp_landing_copy(lang)
    if lang == "es":
        path = "/pullsomvp/es"
        canonical = absolute_url(path)
        meta_title = "Pullso · analista de revenue con IA para hoteles"
        meta_description = (
            "Analista de revenue con IA para hoteles. Lecturas claras y siguientes acciones en WhatsApp. Después, coordinación y contexto compartido."
        )
        html_lang = "es"
        og_locale = "es_MX"
        in_lang = "es-MX"
        twitter_title = "Pullso · analista de revenue con IA para hoteles"
    else:
        path = "/pullsomvp"
        canonical = absolute_url(path)
        meta_title = "Pullso · AI revenue analyst for hotels"
        meta_description = (
            "AI revenue analyst for hotels. Clear reads and next steps in WhatsApp. Then coordination, shared context, and less repetitive work."
        )
        html_lang = "en"
        og_locale = "en_US"
        in_lang = "en"
        twitter_title = "Pullso · AI revenue analyst for hotels"

    _site = website_node()
    _org = organization_node()
    structured = {
        "@context": "https://schema.org",
        "@graph": [
            _org,
            _site,
            {
                "@type": "WebPage",
                "@id": canonical + "#webpage",
                "url": canonical,
                "name": meta_title,
                "description": meta_description,
                "inLanguage": in_lang,
                "isPartOf": {"@id": _site["@id"]},
                "publisher": {"@id": _org["@id"]},
            },
        ],
    }
    seo = {
        "meta_title": meta_title,
        "meta_description": meta_description,
        "canonical_url": canonical,
        "robots_meta": "noindex, nofollow",
        "og_title": meta_title,
        "og_description": meta_description,
        "og_locale": og_locale,
        "twitter_title": twitter_title,
        "twitter_description": meta_description,
        "html_lang": html_lang,
        "structured_data": structured,
    }
    _poster = (
        (os.getenv("PULLSO_MVP_HERO_DEMO_VIDEO_POSTER_URL") or os.getenv("PULLSO_YC_HERO_DEMO_VIDEO_POSTER_URL") or "")
        .strip()
    )
    return templates.TemplateResponse(
        "pullso_mvp_home_preview.html",
        {
            "request": request,
            **marketing_page_context(),
            **seo,
            "contact_email": CONTACT_EMAIL_PUBLIC,
            "copy": copy,
            "pullso_lang": lang,
            "lead_post_url": url_path("/pullsomvp/lead"),
            "hero_agent_video_src": _pullso_mvp_hero_agent_video_src(),
            "hero_agent_video_poster_src": _resolve_hero_media_url(_poster),
        },
    )


@router.get("/pullsomvp", response_class=HTMLResponse, include_in_schema=False)
def pullso_mvp_home_preview(request: Request):
    return _pullso_mvp_home_preview_response(request, lang="en")


@router.get("/pullsomvp/es", response_class=HTMLResponse, include_in_schema=False)
def pullso_mvp_home_preview_es(request: Request):
    return _pullso_mvp_home_preview_response(request, lang="es")


@router.get("/pullso-mvp", response_class=HTMLResponse, include_in_schema=False)
def pullso_mvp_slug_redirect(request: Request):
    """Slug intermedio; canonical /pullsomvp."""
    return RedirectResponse(url_path("/pullsomvp"), status_code=301)


@router.get("/pullso-mvp/es", response_class=HTMLResponse, include_in_schema=False)
def pullso_mvp_slug_es_redirect(request: Request):
    return RedirectResponse(url_path("/pullsomvp/es"), status_code=301)


@router.get("/pullso-yc-home-preview", response_class=HTMLResponse, include_in_schema=False)
def pullso_yc_home_preview_redirect(request: Request):
    """Slug anterior; canonical /pullsomvp."""
    return RedirectResponse(url_path("/pullsomvp"), status_code=301)


@router.get("/pullso-yc-home-preview/es", response_class=HTMLResponse, include_in_schema=False)
def pullso_yc_home_preview_es_redirect(request: Request):
    return RedirectResponse(url_path("/pullsomvp/es"), status_code=301)
