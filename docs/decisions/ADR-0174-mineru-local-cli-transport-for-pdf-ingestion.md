# ADR-0174: MinerU local por CLI para ingesta PDF clinica

## Estado

Aprobado

## Contexto

La ingesta PDF del chat clinico soportaba `mineru`, pero solo mediante un endpoint
HTTP externo/local. En practica eso dejaba dos problemas:

- la configuracion local quedaba incompleta para un flujo "todo en local";
- cuando no existia el servicio HTTP, el sistema acababa degradando a `pypdf`
  aunque el usuario ya hubiera activado `backend=mineru`.

Para el corpus de `docs/pdf_raw`, la calidad de recuperacion depende de preservar
layout, tablas y orden de lectura mejor que con texto plano por pagina.

## Decision

Se introduce transporte configurable para MinerU:

- `CLINICAL_CHAT_PDF_MINERU_TRANSPORT=cli|http|auto`
- `CLINICAL_CHAT_PDF_MINERU_CLI_COMMAND`

El parser PDF:

- ejecuta `mineru` localmente cuando el transporte es `cli`;
- fija por defecto backend `pipeline` y dispositivo `cpu` para priorizar
  operatividad local en portatil;
- fija por defecto metodo `txt` para PDFs digitales, dejando `auto/ocr` como
  override explicito para corpus escaneados;
- desactiva formulas y mantiene tablas por defecto para reducir coste en corpus
  clinico, donde las tablas son utiles y las formulas rara vez son criticas;
- conserva soporte HTTP para despliegues que ya usen un servicio separado;
- mantiene `fail-open` hacia `pypdf` para no bloquear ingesta si MinerU no esta
  disponible.

Para compatibilidad con instalaciones anteriores, el resolver del ejecutable
acepta tambien el alias legacy `magic-pdf`.

La salida CLI se normaliza a bloques estructurados usando:

- JSON de salida de MinerU cuando esta disponible;
- Markdown generado por MinerU como respaldo estructural para chunking.

## Consecuencias

Positivas:

- flujo local sin coste por token ni dependencia obligatoria de otro servicio;
- mejor base estructural para chunking sobre `pdf_raw`;
- degradacion rapida a `pypdf` si el binario no esta instalado.
- timeout mas realista (`900s`) para absorber cold start, descarga inicial de modelos y PDFs densos durante la ingesta offline en CPU.

Negativas:

- MinerU sigue teniendo coste local de CPU/RAM/disco y descarga de modelos;
- no existe precision del 100% en parsing PDF complejo;
- el comportamiento CLI depende del binario `magic-pdf` instalado en el entorno.
- el comportamiento CLI depende del binario `mineru` instalado en el entorno
  (o `magic-pdf` en instalaciones legacy).

## Validacion requerida

- tests unitarios de `PDFParserService` para `cli`, `auto`, fallback y validacion;
- lint sobre parser/tests;
- reingesta del corpus y evaluacion retrieval por especialidad antes de considerar
  cerrada la mejora de calidad RAG.
