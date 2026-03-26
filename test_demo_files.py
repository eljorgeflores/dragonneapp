"""
Prueba real con los archivos demo: reporte_demo_dragonne.xls y Forecast and revenue..csv
"""
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import UploadFile
from starlette.datastructures import Headers

from services.analysis_core import parse_file, summarize_reports

# Rutas a los archivos demo (en Downloads del usuario)
DOWNLOADS = Path("/Users/jorgeflores/Downloads")
XLS_PATH = DOWNLOADS / "reporte_demo_dragonne.xls"
CSV_PATH = DOWNLOADS / "reporte_demo_dragonne.xls - Forecast and revenue..csv"


def make_upload(path: Path, filename: str = None) -> UploadFile:
    content = path.read_bytes()
    name = filename or path.name
    ct = "application/vnd.ms-excel" if path.suffix.lower() == ".xls" else "text/csv"
    return UploadFile(filename=name, file=io.BytesIO(content), headers=Headers({"content-type": ct}))


def main():
    print("=" * 60)
    print("PRUEBA CON ARCHIVOS DEMO REALES")
    print("=" * 60)

    # 1) CSV - Forecast and revenue
    if not CSV_PATH.exists():
        print(f"\n[ERROR] No encontrado: {CSV_PATH}")
    else:
        print(f"\n--- CSV: {CSV_PATH.name} ---")
        try:
            upload_csv = make_upload(CSV_PATH)
            sheets_csv = parse_file(upload_csv)
            print(f"  Hojas/archivo parseados: {len(sheets_csv)}")
            for name, df in sheets_csv:
                print(f"  - {name}: {len(df)} filas, columnas: {list(df.columns)[:8]}...")
            upload_csv = make_upload(CSV_PATH)  # de nuevo para summarize
            summary_csv = summarize_reports([upload_csv])
            print(f"  Resumen: reports_detected={summary_csv['reports_detected']}, "
                  f"total_files={summary_csv['total_files']}, "
                  f"overall_days_covered={summary_csv.get('overall_days_covered', 0)}")
            for i, rs in enumerate(summary_csv.get("report_summaries", [])[:2]):
                print(f"  Sheet {i+1}: rows={rs.get('rows')}, days_covered={rs.get('days_covered')}, "
                      f"date_range={rs.get('date_range')}")
            print("  [OK] CSV procesado correctamente.")
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()

    # 2) XLS - reporte_demo_dragonne.xls
    if not XLS_PATH.exists():
        print(f"\n[ERROR] No encontrado: {XLS_PATH}")
    else:
        print(f"\n--- XLS: {XLS_PATH.name} ---")
        try:
            upload_xls = make_upload(XLS_PATH)
            sheets_xls = parse_file(upload_xls)
            print(f"  Hojas parseadas: {len(sheets_xls)}")
            for name, df in sheets_xls:
                print(f"  - {name}: {len(df)} filas, columnas: {list(df.columns)[:8]}...")
            upload_xls = make_upload(XLS_PATH)
            summary_xls = summarize_reports([upload_xls])
            print(f"  Resumen: reports_detected={summary_xls['reports_detected']}, "
                  f"total_files={summary_xls['total_files']}, "
                  f"overall_days_covered={summary_xls.get('overall_days_covered', 0)}")
            for i, rs in enumerate(summary_xls.get("report_summaries", [])[:3]):
                print(f"  Sheet {i+1}: rows={rs.get('rows')}, days_covered={rs.get('days_covered')}")
            print("  [OK] XLS procesado correctamente.")
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()

    # 3) Ambos a la vez (como haría el usuario)
    if CSV_PATH.exists() and XLS_PATH.exists():
        print("\n--- Ambos archivos en un solo análisis ---")
        try:
            uploads = [make_upload(CSV_PATH), make_upload(XLS_PATH)]
            summary_both = summarize_reports(uploads)
            print(f"  reports_detected={summary_both['reports_detected']}, "
                  f"total_files={summary_both['total_files']}, "
                  f"overall_days_covered={summary_both.get('overall_days_covered', 0)}")
            print("  [OK] Análisis combinado listo para enviar a OpenAI.")
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
