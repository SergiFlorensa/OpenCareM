# ADR-0175: Scheduling por ventanas para MinerU en CPU

## Estado

Aprobado

## Contexto

MinerU por CLI ya estaba operativo en local, pero algunos PDF clinicos densos
en CPU monopolizaban el equipo durante demasiados minutos. En un portatil eso
genera dos problemas:

- la ingesta de un documento grande bloquea el avance del lote completo;
- el parser compite de forma agresiva con Ollama, frontend y otros procesos
  locales.

La documentacion oficial y el `--help` real del binario muestran soporte para:

- rangos de pagina (`-s/--start`, `-e/--end`);
- backend `pipeline` con `device=cpu`;
- control de entorno para timeout de render e hilos en versiones recientes.

## Decision

Se introduce una politica adaptativa para MinerU en CPU:

- si el PDF supera un umbral de paginas configurable, se parsea por ventanas de
  paginas en lugar de una unica ejecucion monolitica;
- cada ventana usa el CLI oficial con `-s` y `-e`;
- el parser fusiona los bloques resultantes y corrige el offset de paginas,
  porque MinerU reinicia `page_idx` dentro de cada subproceso;
- se exponen limites de contencion local:
  - `CLINICAL_CHAT_PDF_MINERU_RENDER_TIMEOUT_SECONDS`
  - `CLINICAL_CHAT_PDF_MINERU_CPU_INTRA_OP_THREADS`
  - `CLINICAL_CHAT_PDF_MINERU_CPU_INTER_OP_THREADS`
- se mantienen defaults conservadores para portatil:
  - `windowed=true`
  - `threshold_pages=24`
  - `window_size_pages=12`
  - `intra_op_threads=2`
  - `inter_op_threads=1`

## Consecuencias

Positivas:

- los PDF grandes dejan de ser una sola operacion de larga duracion;
- el equipo recupera control entre ventanas y la contencion con otros procesos
  baja;
- el mismo parser sirve para lotes incrementales sin exigir GPU.

Negativas:

- el tiempo total puede no bajar mucho en CPU; el objetivo principal es
  estabilidad operativa y no saturar el equipo;
- el merge por ventanas añade logica extra y requiere pruebas de offsets;
- si el documento es pequeno, la ventana no aporta beneficio y se evita por
  umbral.

## Validacion requerida

- tests unitarios para:
  - settings nuevos;
  - flags `-s/-e` en CLI;
  - activacion de modo windowed;
  - correccion de offset de pagina al fusionar bloques.
- smoke real con un PDF pequeno y otro PDF suficientemente grande.
