# Documentacion del Proyecto
Este directorio centraliza la documentacion tecnica y operativa del proyecto.

## Orden recomendado de lectura

1. `docs/01_current_state.md`
2. `docs/02_codex_cli_mcp_setup.md`
3. `docs/03_mcp_tools_reference.md`
4. `docs/04_agent_system.md`
5. `docs/05_roadmap.md`
6. `docs/06_quality_workflow.md`
7. `docs/07_docker_compose_workflow.md`
8. `docs/08_environment_strategy.md`
9. `docs/09_security_baseline.md`
10. `docs/10_auth_foundation.md`
11. `docs/11_auth_api_workflow.md`
12. `docs/12_bootstrap_admin_cli.md`
13. `docs/13_admin_rbac.md`
14. `docs/14_refresh_token_workflow.md`
15. `docs/15_mcp_smoke_runbook.md`
16. `docs/16_error_handling_workflow.md`
17. `docs/17_request_logging.md`
18. `docs/18_prometheus_metrics.md`
19. `docs/19_prometheus_compose_setup.md`
20. `docs/20_grafana_setup.md`
21. `docs/21_login_rate_limit.md`
22. `docs/22_ai_task_triage.md`
23. `docs/23_project_skills_playbook.md`
24. `docs/24_agent_run_foundation.md`
25. `docs/25_ai_triage_hybrid_mode.md`
26. `docs/26_agent_run_history_endpoints.md`
27. `docs/27_agent_run_history_filters.md`
28. `docs/28_agent_ops_summary.md`
29. `docs/29_agent_prometheus_grafana_metrics.md`
30. `docs/30_agent_alerts_baseline.md`
31. `docs/31_alertmanager_integration.md`
32. `docs/32_clinical_ops_pivot_phase1.md`
33. `docs/33_care_tasks_api_workflow.md`
34. `docs/34_castellanizacion_repositorio.md`
35. `docs/35_care_task_agent_triage_workflow.md`
36. `docs/36_care_task_triage_human_approval.md`
37. `docs/37_contexto_operaciones_clinicas_urgencias_es.md`
38. `docs/38_manchester_triage_levels.md`
39. `docs/39_triage_audit_logs.md`
40. `docs/40_motor_protocolo_respiratorio.md`
41. `docs/41_motor_humanizacion_pediatrica.md`
42. `docs/42_motor_screening_operativo_avanzado.md`
43. `docs/43_auditoria_calidad_screening.md`
44. `docs/44_soporte_interpretacion_rx_torax.md`
45. `docs/45_motor_medico_legal_urgencias.md`
46. `docs/46_auditoria_calidad_medico_legal.md`
47. `docs/47_motor_sepsis_urgencias.md`
48. `docs/48_flujo_extremo_a_extremo_episodio_urgencias.md`
49. `docs/49_motor_scasest_urgencias.md`
50. `docs/50_auditoria_calidad_scasest.md`
51. `docs/51_runbook_alertas_scasest.md`
52. `docs/52_scasest_alert_drill.md`
53. `docs/53_scorecard_calidad_ia_clinica.md`
54. `docs/54_runbook_alertas_calidad_global.md`
55. `docs/55_drill_alertas_calidad_global.md`
56. `docs/56_evaluacion_continua_gate_calidad_ia.md`
57. `docs/57_motor_riesgo_cardiovascular_urgencias.md`
58. `docs/58_motor_reanimacion_soporte_vital_urgencias.md`
59. `docs/59_runbook_alertas_reanimacion.md`
60. `docs/60_reanimacion_alert_drill.md`
61. `docs/61_terapia_electrica_arritmias_criticas.md`
62. `docs/62_bioetica_pediatrica_conflicto_autonomia_vida.md`
63. `docs/63_motor_diferencial_pitiriasis_urgencias.md`
64. `docs/64_motor_diferencial_acne_rosacea_urgencias.md`
65. `docs/65_motor_trauma_urgencias_trimodal.md`
66. `docs/66_motor_operativo_critico_transversal_urgencias.md`
67. `docs/67_motor_operativo_neurologia_urgencias.md`
68. `docs/68_motor_operativo_gastro_hepato_urgencias.md`
69. `docs/69_motor_operativo_reuma_inmuno_urgencias.md`
70. `docs/70_motor_operativo_psiquiatria_urgencias.md`
71. `docs/71_motor_operativo_hematologia_urgencias.md`
72. `docs/72_motor_operativo_endocrinologia_urgencias.md`
73. `docs/73_motor_operativo_nefrologia_urgencias.md`
74. `docs/74_motor_operativo_neumologia_urgencias.md`
75. `docs/75_motor_operativo_geriatria_fragilidad_urgencias.md`
76. `docs/76_motor_operativo_oncologia_urgencias.md`
77. `docs/77_motor_operativo_anestesiologia_reanimacion_urgencias.md`
78. `docs/78_motor_operativo_cuidados_paliativos_urgencias.md`
79. `docs/79_motor_operativo_urologia_urgencias.md`
80. `docs/80_motor_operativo_anisakis_urgencias.md`
81. `docs/81_motor_operativo_epidemiologia_clinica_urgencias.md`
82. `docs/82_motor_operativo_oftalmologia_urgencias.md`
83. `docs/83_motor_operativo_inmunologia_urgencias.md`
84. `docs/84_motor_operativo_recurrencia_genetica_oi_urgencias.md`
85. `docs/85_motor_operativo_ginecologia_obstetricia_urgencias.md`
86. `docs/86_motor_operativo_pediatria_neonatologia_urgencias.md`
87. `docs/87_chat_clinico_operativo_profesional.md`
88. `docs/88_chat_clinico_especialidad_contexto_longitudinal.md`
89. `docs/89_chat_fuentes_confiables_whitelist_sellado.md`
90. `docs/90_playbook_curacion_fuentes_clinicas.md`
91. `docs/91_frontend_chat_clinico_mvp.md`
92. `docs/92_frontend_chat_herramientas_modo_hibrido.md`
93. `docs/93_motor_conversacional_neuronal_open_source.md`
94. `docs/94_chat_clinico_operativo_ollama_local_runbook.md`
95. `docs/95_chat_open_source_hardening_prompt_injection_quality_metrics.md`
96. `docs/96_adaptacion_blueprint_agentes_oss_interno.md`

## Objetivo

- Entender el estado real del repo sin suposiciones.
- Poder reproducir el setup MCP en Codex CLI paso a paso.
- Definir una forma profesional de trabajo con agentes y handoffs.
- Tener un roadmap incremental con entregas pequenas y verificables.

## Convenciones de documentacion

- Cada cambio relevante debe incluir:
  - Que problema resuelve.
  - Que archivos toca.
  - Como se valida.
  - Riesgos pendientes.
- Las decisiones tecnicas se registran en `docs/decisions/`.

