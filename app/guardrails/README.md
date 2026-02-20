# Configuracion NeMo Guardrails (local)

Este directorio define la configuracion base para `NeMo Guardrails`.

- Archivo principal: `config.yml`
- Motor por defecto: `ollama` local en `127.0.0.1:11434`

Notas:

- Esta capa es opcional y se activa con `CLINICAL_CHAT_GUARDRAILS_ENABLED=true`.
- Si falta dependencia/config y `CLINICAL_CHAT_GUARDRAILS_FAIL_OPEN=true`,
  el chat continua con la respuesta original.
