"""Perfil + bloque lectura_operativa en el resumen."""
from services.summary_profile_enrich import build_hotel_context_for_analysis, enrich_summary_with_hotel_profile


def test_build_hotel_context_includes_inventory_and_commissions():
    user = {
        "hotel_name": "Hotel X",
        "hotel_size": "pequeño (<=40 llaves)",
        "hotel_category": "boutique",
        "hotel_location": "MX",
        "hotel_stars": 4,
        "hotel_location_context": "centro",
        "hotel_room_count": 40,
        "hotel_ota_commissions_json": '{"booking":15,"expedia":20,"default":10}',
    }
    ctx = build_hotel_context_for_analysis(user)
    assert ctx["hotel_habitaciones_fisicas"] == 40
    assert ctx["hotel_comisiones_ota_pct_referencia"]["booking"] == 15.0
    assert ctx["hotel_comisiones_ota_pct_referencia"]["expedia"] == 20.0


def test_enrich_summary_occupancy_proxy_and_margin():
    user = {
        "hotel_name": "H",
        "hotel_size": "",
        "hotel_category": "",
        "hotel_location": "",
        "hotel_stars": 0,
        "hotel_room_count": 40,
        "hotel_ota_commissions_json": '{"booking":15,"expedia":20}',
    }
    hc = build_hotel_context_for_analysis(user)
    summary = {
        "overall_days_covered": 10,
        "report_summaries": [
            {
                "metrics": {
                    "room_nights": 200.0,
                    "revenue_total": 50000.0,
                    "top_canales_por_ingreso": [
                        {"canal": "BOOKING", "ingreso": 30000.0},
                        {"canal": "Expedia.com", "ingreso": 10000.0},
                    ],
                }
            }
        ],
    }
    enrich_summary_with_hotel_profile(summary, hc)
    lo = summary["lectura_operativa"]
    assert lo["estimaciones"]["ocupacion_proxy_pct"] == 50.0
    margins = {m["canal"]: m["pct_comision_perfil"] for m in lo["estimaciones"]["margen_por_canal_comision_perfil"]}
    assert margins["BOOKING"] == 15.0
    assert margins["Expedia.com"] == 20.0
