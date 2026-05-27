# UTP Docente Apto Cloud Smoke Test

Repositorio sanitizado para probar GitHub Actions sin datos sensibles.

Objetivo:

- Validar si `https://class.utp.edu.pe` carga correctamente en un runner de GitHub Actions.
- Subir screenshot, HTML y trace como artefacto.
- Mantener la misma estructura critica del proyecto real, pero con data fake.

No contiene credenciales reales ni informacion de estudiantes/docentes.

## Prueba

Al subir este repositorio a GitHub, el workflow `UTP Cloud Smoke` se ejecuta en cada push relevante y tambien manualmente desde:

```text
Actions > UTP Cloud Smoke > Run workflow
```

El resultado queda en el artefacto:

```text
utp-cloud-smoke-diagnostics
```

Archivos clave:

- `inicio.png`
- `inicio.html`
- `trace.zip`

Si `inicio.png` sale en blanco, el problema no es el Excel ni las credenciales: es el entorno/IP/navegador de GitHub Actions frente a UTP+CLASS.
