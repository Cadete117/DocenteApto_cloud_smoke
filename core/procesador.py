from pathlib import Path


def generar_csv(df):

    output_path = Path("output")

    output_path.mkdir(exist_ok=True)

    ruta_csv = output_path / "inscripciones.csv"

    columnas = [
        "course_id",
        "user_id",
        "role",
        "status"
    ]

    df[columnas].to_csv(
        ruta_csv,
        index=False,
        encoding="utf-8"
    )

    return str(ruta_csv)