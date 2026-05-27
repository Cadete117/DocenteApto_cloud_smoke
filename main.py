from excel.reader import obtener_solicitudes_pendientes
from core.procesador import generar_csv
from bot.bot_utp import subir_csv_inscripciones
from excel.writer import (
    marcar_como_procesado,
    agregar_reporte
)


def main():

    print("Leyendo solicitudes pendientes...")

    df = obtener_solicitudes_pendientes()

    if df.empty:
        print("No hay solicitudes pendientes")
        return

    print(f"Pendientes encontradas: {len(df)}")

    print("Generando CSV...")

    ruta_csv = generar_csv(df)

    print("Subiendo CSV a UTP+CLASS...")

    ruta_reporte = subir_csv_inscripciones(ruta_csv)

    print("Agregando reporte al Excel...")

    agregar_reporte(ruta_reporte)

    print("Marcando registros como procesados...")

    marcar_como_procesado(df.index)

    print("Proceso finalizado correctamente")


if __name__ == "__main__":
    main()