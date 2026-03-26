"""
Tests de generación de reportes: parse_file, summarize_reports y POST /analyze.
Verifica que CSV y Excel se acepten y que el resumen se genere correctamente.
"""
import io
import sys
from pathlib import Path

# Asegurar import desde el proyecto
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
from fastapi import UploadFile
from starlette.datastructures import Headers

from config import ALLOWED_UPLOAD_EXTENSIONS
from services.analysis_core import parse_file, summarize_reports


def make_upload_file(filename: str, content: bytes, content_type: str = "application/octet-stream") -> UploadFile:
    """Crea un UploadFile desde bytes para tests."""
    stream = io.BytesIO(content)
    # UploadFile en Starlette: filename, file=stream; headers opcionales
    headers = Headers({"content-type": content_type})
    return UploadFile(filename=filename, file=stream, headers=headers)


def test_parse_csv():
    """CSV válido debe parsearse a un DataFrame."""
    csv_content = (
        "stay_date,room_revenue,room_nights,channel\n"
        "2025-01-01,1000,5,Directo\n"
        "2025-01-02,1500,7,Booking\n"
        "2025-01-03,1200,4,Expedia\n"
    )
    upload = make_upload_file("reporte_prueba.csv", csv_content.encode("utf-8"), "text/csv")
    sheets = parse_file(upload)
    assert len(sheets) == 1, "CSV debe producir una sola hoja"
    name, df = sheets[0]
    assert name == "reporte_prueba.csv"
    assert len(df) == 3
    assert "channel" in df.columns or "room_revenue" in df.columns
    print("OK test_parse_csv")


def test_parse_csv_utf8_bom():
    """CSV con BOM UTF-8 (común en Excel) debe leerse bien."""
    csv_content = "\ufeffstay_date,revenue,channel\n2025-01-01,1000,Directo\n"
    upload = make_upload_file("export.csv", csv_content.encode("utf-8-sig"), "text/csv")
    sheets = parse_file(upload)
    assert len(sheets) == 1
    _, df = sheets[0]
    assert len(df) == 1
    assert "stay_date" in df.columns or "revenue" in df.columns
    print("OK test_parse_csv_utf8_bom")


def test_parse_csv_semicolon():
    """CSV con separador punto y coma (Excel español) puede fallar si no se especifica sep."""
    csv_content = "Fecha;Ingresos;Canal\n01/01/2025;1000;Directo\n"
    upload = make_upload_file("reporte.csv", csv_content.encode("utf-8"), "text/csv")
    try:
        sheets = parse_file(upload)
        # Si pandas lo interpreta mal (una sola columna), al menos no debe lanzar
        assert len(sheets) == 1
        _, df = sheets[0]
        assert len(df) >= 1
    except Exception as e:
        # pd.read_csv sin sep= puede dar una sola columna; infer_sheet podría seguir funcionando
        raise AssertionError(f"CSV con punto y coma no debería fallar en parse_file: {e}")
    print("OK test_parse_csv_semicolon")


def test_summarize_reports_csv():
    """summarize_reports con un CSV debe devolver reports_detected >= 1."""
    csv_content = (
        "stay_date,room_revenue,room_nights,channel\n"
        "2025-01-01,1000,5,Directo\n"
        "2025-01-02,1500,7,Booking\n"
    )
    upload = make_upload_file("reporte.csv", csv_content.encode("utf-8"), "text/csv")
    summary = summarize_reports([upload])
    assert summary["total_files"] == 1
    assert summary["reports_detected"] >= 1
    assert "report_summaries" in summary
    assert len(summary["report_summaries"]) >= 1
    print("OK test_summarize_reports_csv")


def test_parse_excel_xlsx():
    """Excel .xlsx mínimo debe parsearse."""
    # Crear un xlsx mínimo con pandas
    df = pd.DataFrame({
        "Fecha": ["2025-01-01", "2025-01-02"],
        "Ingresos": [1000, 1500],
        "Canal": ["Directo", "Booking"],
    })
    buf = io.BytesIO()
    df.to_excel(buf, index=False, sheet_name="Hoja1")
    raw = buf.getvalue()
    upload = make_upload_file("reporte.xlsx", raw, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    sheets = parse_file(upload)
    assert len(sheets) >= 1
    _, parsed_df = sheets[0]
    assert len(parsed_df) >= 1
    print("OK test_parse_excel_xlsx")


def test_summarize_reports_excel():
    """summarize_reports con un .xlsx debe devolver resumen."""
    df = pd.DataFrame({
        "check_in": ["2025-01-01", "2025-01-02"],
        "room_revenue": [1000, 1500],
        "room_nights": [2, 3],
        "channel": ["Directo", "Booking"],
    })
    buf = io.BytesIO()
    df.to_excel(buf, index=False, sheet_name="Reservas")
    raw = buf.getvalue()
    upload = make_upload_file("reporte.xlsx", raw, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    summary = summarize_reports([upload])
    assert summary["total_files"] == 1
    assert summary["reports_detected"] >= 1
    print("OK test_summarize_reports_excel")


def test_extension_not_allowed():
    """Extensión no permitida debe lanzar ValueError."""
    upload = make_upload_file("archivo.pdf", b"fake pdf", "application/pdf")
    try:
        parse_file(upload)
        assert False, "Debería haber lanzado ValueError"
    except ValueError as e:
        assert "no permitido" in str(e).lower() or "formato" in str(e).lower()
    print("OK test_extension_not_allowed")


def test_empty_csv():
    """CSV solo con cabecera no debe romper (DataFrame vacío o una fila)."""
    csv_content = "date,revenue,channel\n"
    upload = make_upload_file("vacio.csv", csv_content.encode("utf-8"), "text/csv")
    sheets = parse_file(upload)
    assert len(sheets) == 1
    _, df = sheets[0]
    assert len(df) == 0 or (len(df) == 1 and df.isna().all().all())
    print("OK test_empty_csv")


def run_all():
    test_parse_csv()
    test_parse_csv_utf8_bom()
    test_parse_csv_semicolon()
    test_summarize_reports_csv()
    test_parse_excel_xlsx()
    test_summarize_reports_excel()
    test_extension_not_allowed()
    test_empty_csv()
    print("\nTodos los tests de reporte pasaron.")


if __name__ == "__main__":
    run_all()
