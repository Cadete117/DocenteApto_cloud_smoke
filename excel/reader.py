import pandas as pd
from pathlib import Path

EXCEL_PATH = Path("data/solicitud_inscripciones_DA.xlsx")


def obtener_solicitudes_pendientes():

    df = pd.read_excel(
        EXCEL_PATH,
        sheet_name="Solicitudes"
    )

    # Limpiar textos
    for col in ["role", "status", "procesado"]:
        df[col] = (
            df[col]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )

    # Validaciones
    roles_validos = ["student", "teacher"]
    status_validos = ["active", "inactive", "delete"]

    pendientes = df[
        (df["procesado"] == "") &
        (df["role"].isin(roles_validos)) &
        (df["status"].isin(status_validos))
    ].copy()

    return pendientes