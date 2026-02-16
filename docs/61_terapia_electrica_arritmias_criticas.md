# Terapia Electrica en Arritmias Criticas (Integracion Operativa)

## Objetivo

Convertir criterios de cardioversion/desfibrilacion en recomendaciones operativas
estructuradas dentro del endpoint de reanimacion:

- `POST /api/v1/care-tasks/{task_id}/resuscitation/recommendation`

No sustituye juicio clinico ni protocolos institucionales.

## Criterios operativos integrados

### 1) Tipo de terapia electrica

- `desfibrilacion no sincronizada`:
  - FV
  - TV sin pulso
  - TV polimorfica
- `cardioversion sincronizada`:
  - TSV/Flutter inestable con pulso
  - FA inestable con pulso
  - TV monomorfica inestable con pulso

### 2) Inestabilidad hemodinamica (disparador)

Se usa al menos un criterio:

- hipotension
- alteracion mental aguda
- signos de shock
- dolor toracico isquemico
- insuficiencia cardiaca aguda
- presion de pulso estrecha (si se informa PAS/PAD)

### 3) Energia sugerida por ritmo

- TSV/Flutter: 50-100 J (sincronizado)
- FA: 120-200 J bifasico (sincronizado)
- TV monomorfica con pulso: 100 J (sincronizado)
- TV polimorfica: desfibrilacion no sincronizada
- FV/TV sin pulso: desfibrilacion no sincronizada inmediata

### 4) Sedoanalgesia y seguridad

Se emiten bloques especificos:

- `sedoanalgesia_plan`
  - fentanilo (ventana previa)
  - etomidato como hipnotico de referencia
  - alternativa propofol con advertencia hemodinamica
- `pre_shock_safety_checklist`
  - verificacion de modo sync y onda R
  - retiro de fuente de oxigeno del campo
  - aviso de seguridad pre-descarga

## Campos de entrada relevantes

Ademas de campos previos del protocolo, se pueden informar:

- `systolic_bp_mm_hg`
- `diastolic_bp_mm_hg`

Con ambos campos, el motor puede alertar bajo gasto por presion de pulso estrecha.

## Validacion recomendada

```powershell
.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k cardioversion
.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py
```
