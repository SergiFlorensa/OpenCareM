import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Bot,
  Brain,
  ChevronRight,
  ClipboardList,
  FileText,
  HeartPulse,
  History,
  Menu,
  Plus,
  RefreshCw,
  Search,
  SendHorizonal,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  User,
  Waves,
  X,
} from "lucide-react";

type CareTask = {
  id: number;
  title: string;
  specialty: string;
  patient_reference: string | null;
};

type ChatHistoryItem = {
  id: number;
  session_id: string;
  user_query: string;
  assistant_answer: string;
  created_at: string;
};

type ChatResponse = {
  message_id: number;
  response_mode: string;
  tool_mode: string;
  answer: string;
};

const STORAGE_API_KEY = "clinical_ops_api_base";
const LEGACY_API_BASE = "http://127.0.0.1:8010/api/v1";
const DEFAULT_API_BASE = "http://127.0.0.1:8000/api/v1";

const quickPrompts = [
  "Pasos iniciales ante dolor toracico en urgencias",
  "Molestias oculares agudas: que valorar primero",
  "Paciente con dolor abdominal: datos clave y escalado",
  "Neutropenia febril: ruta operativa priorizada",
];

const commandShortcuts = [
  { label: "Protocolos", icon: FileText },
  { label: "Monitorizacion", icon: Activity },
  { label: "Historial", icon: History },
];

const guidanceCards = [
  {
    icon: Stethoscope,
    title: "Consulta operativa",
    text: "Interroga, resume y orienta la decision con contexto del caso y fuentes internas.",
  },
  {
    icon: HeartPulse,
    title: "Escalado clinico",
    text: "Prioriza signos de alarma, derivacion y ventanas temporales para actuar en urgencias.",
  },
  {
    icon: ShieldCheck,
    title: "Trazabilidad",
    text: "Mantiene referencia de sesion, origen del caso y consistencia visual en toda la conversacion.",
  },
];

function normalizeApiBase(raw: string | null): string {
  const value = (raw || "").trim();
  if (!value || value === LEGACY_API_BASE) return DEFAULT_API_BASE;
  return value;
}

function formatError(detail: unknown, fallback: string): string {
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (typeof item === "object" && item !== null && "msg" in item) return String(item.msg);
        return JSON.stringify(item);
      })
      .join(" | ");
  }
  return fallback;
}

function buildSessionId(): string {
  const stamp = new Date().toISOString().replace(/[^0-9]/g, "").slice(0, 12);
  return `session-${stamp}`;
}

function formatTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("es-ES", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export default function App() {
  const [apiBaseUrl, setApiBaseUrl] = useState(() =>
    normalizeApiBase(localStorage.getItem(STORAGE_API_KEY)),
  );
  const [tasks, setTasks] = useState<CareTask[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(null);
  const [isCasePickerOpen, setIsCasePickerOpen] = useState(false);
  const [caseSearch, setCaseSearch] = useState("");
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const [sessionId, setSessionId] = useState(buildSessionId());
  const [query, setQuery] = useState("");
  const [history, setHistory] = useState<ChatHistoryItem[]>([]);
  const [lastResponse, setLastResponse] = useState<ChatResponse | null>(null);

  const [isBusy, setIsBusy] = useState(false);
  const [error, setError] = useState("");

  const selectedTask = useMemo(
    () => tasks.find((task) => task.id === selectedTaskId) ?? null,
    [tasks, selectedTaskId],
  );

  const filteredTasks = useMemo(() => {
    const term = caseSearch.trim().toLowerCase();
    if (!term) return tasks;
    return tasks.filter((task) => {
      const label = `#${task.id} ${task.title} ${task.patient_reference ?? ""}`.toLowerCase();
      return label.includes(term);
    });
  }, [tasks, caseSearch]);

  const apiRequest = useCallback(
    async <T,>(path: string, init: RequestInit = {}): Promise<T> => {
      const headers = new Headers(init.headers || {});
      if (!headers.has("Content-Type") && init.body && !(init.body instanceof FormData)) {
        headers.set("Content-Type", "application/json");
      }

      const response = await fetch(`${apiBaseUrl}${path}`, { ...init, headers });
      if (!response.ok) {
        let message = `Error ${response.status}`;
        try {
          const payload = await response.json();
          message = formatError(payload?.detail, message);
        } catch {
          message = response.statusText || message;
        }
        throw new Error(message);
      }

      if (response.status === 204) {
        return undefined as T;
      }

      return (await response.json()) as T;
    },
    [apiBaseUrl],
  );

  const refreshTasks = useCallback(async () => {
    const result = await apiRequest<CareTask[]>("/care-tasks/?limit=100");
    setTasks(result);
    if (!selectedTaskId && result.length > 0) {
      setSelectedTaskId(result[0].id);
    }
  }, [apiRequest, selectedTaskId]);

  const loadConversation = useCallback(
    async (taskId: number, activeSessionId: string) => {
      const result = await apiRequest<ChatHistoryItem[]>(
        `/care-tasks/${taskId}/chat/messages?session_id=${encodeURIComponent(activeSessionId)}&limit=100`,
      );
      const ordered = [...result].sort((a, b) => a.created_at.localeCompare(b.created_at));
      setHistory(ordered);
    },
    [apiRequest],
  );

  useEffect(() => {
    localStorage.setItem(STORAGE_API_KEY, apiBaseUrl);
  }, [apiBaseUrl]);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        if (!active) return;
        await refreshTasks();
      } catch (exc) {
        if (!active) return;
        setError(exc instanceof Error ? exc.message : "No se pudo cargar la aplicacion");
      }
    })();

    return () => {
      active = false;
    };
  }, [refreshTasks]);

  useEffect(() => {
    if (!selectedTaskId) return;
    loadConversation(selectedTaskId, sessionId).catch(() => undefined);
  }, [selectedTaskId, loadConversation, sessionId]);

  const handleSend = async (event: FormEvent) => {
    event.preventDefault();
    if (!query.trim() || !selectedTaskId) return;

    setError("");
    setIsBusy(true);
    try {
      const response = await apiRequest<ChatResponse>(`/care-tasks/${selectedTaskId}/chat/messages`, {
        method: "POST",
        body: JSON.stringify({
          query: query.trim(),
          session_id: sessionId,
          use_web_sources: false,
          use_patient_history: true,
          use_authenticated_specialty_mode: false,
          include_protocol_catalog: false,
          pipeline_relaxed_mode: false,
        }),
      });
      setLastResponse(response);
      setQuery("");
      await loadConversation(selectedTaskId, sessionId);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "No se pudo enviar el mensaje");
    } finally {
      setIsBusy(false);
    }
  };

  const useQuickPrompt = (value: string) => {
    setQuery(value);
  };

  return (
    <main data-theme="clinical" className="clinical-shell">
      <div className="clinical-backdrop" />
      <div className="clinical-noise" />

      {isSidebarOpen && (
        <button
          type="button"
          className="fixed inset-0 z-30 bg-slate-950/55 backdrop-blur-sm lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
          aria-label="Cerrar panel lateral"
        />
      )}

      <div className="relative z-10 flex min-h-screen">
        <aside
          className={`clinical-sidebar ${
            isSidebarOpen ? "translate-x-0" : "-translate-x-full"
          } lg:translate-x-0`}
        >
          <div className="clinical-sidebar__inner">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="clinical-mark">
                  <Brain className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-white">Clinical Chat</p>
                  <p className="text-xs text-cyan-100/70">Urgencias, seguimiento y contexto medico</p>
                </div>
              </div>
              <button
                type="button"
                className="rounded-2xl border border-white/10 p-2 text-white/60 lg:hidden"
                onClick={() => setIsSidebarOpen(false)}
                aria-label="Ocultar panel lateral"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <button
              type="button"
              className="clinical-sidebar__cta"
              onClick={() => {
                setSessionId(buildSessionId());
                setLastResponse(null);
              }}
            >
              <Plus className="h-4 w-4" />
              Nueva conversacion
            </button>

            <section className="clinical-sidebar__section">
              <p className="clinical-sidebar__kicker">Atajos</p>
              <div className="grid gap-2">
                {commandShortcuts.map((item) => (
                  <button key={item.label} type="button" className="clinical-sideitem">
                    <item.icon className="h-4 w-4 text-cyan-200" />
                    <span>{item.label}</span>
                    <ChevronRight className="ml-auto h-3.5 w-3.5 text-white/35" />
                  </button>
                ))}
              </div>
            </section>

            <section className="clinical-sidebar__section">
              <p className="clinical-sidebar__kicker">Estado de la sesion</p>
              <div className="clinical-statusgrid">
                <div className="clinical-statuscard">
                  <span>Casos</span>
                  <strong>{tasks.length}</strong>
                </div>
                <div className="clinical-statuscard">
                  <span>Sesion</span>
                  <strong>{sessionId.slice(-6)}</strong>
                </div>
              </div>
            </section>

            <section className="clinical-sidebar__section">
              <div className="flex items-center gap-2 text-xs uppercase tracking-[0.22em] text-cyan-100/55">
                <ShieldCheck className="h-4 w-4" />
                Trazabilidad activa
              </div>
              <p className="mt-2 text-sm leading-6 text-white/72">
                Interfaz unificada para consultar el caso, mantener contexto y lanzar preguntas
                clinicas sin partir la experiencia visual entre paneles inconexos.
              </p>
            </section>

            <section className="clinical-sidebar__section mt-auto">
              <p className="clinical-sidebar__kicker">API</p>
              <label className="clinical-apiinput">
                <Waves className="h-4 w-4 text-cyan-200/70" />
                <input
                  value={apiBaseUrl}
                  onChange={(event) => setApiBaseUrl(event.target.value)}
                  aria-label="API base"
                />
              </label>
            </section>
          </div>
        </aside>

        <section className="flex min-w-0 flex-1 flex-col">
          <header className="clinical-topbar">
            <div className="flex items-center gap-3">
              <button
                type="button"
                className="clinical-iconbutton lg:hidden"
                onClick={() => setIsSidebarOpen(true)}
                aria-label="Abrir panel lateral"
              >
                <Menu className="h-4 w-4" />
              </button>
              <div>
                <p className="text-[11px] uppercase tracking-[0.24em] text-slate-500">
                  Workspace conversacional
                </p>
                <h1 className="text-lg font-semibold text-slate-900">
                  {selectedTask ? selectedTask.title : "Selecciona un caso para empezar"}
                </h1>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="clinical-pill">
                <Sparkles className="h-3.5 w-3.5" />
                Chat unificado
              </span>
              <button type="button" className="clinical-iconbutton" onClick={refreshTasks}>
                <RefreshCw className="h-4 w-4" />
              </button>
            </div>
          </header>

          <div className="clinical-main">
            <section className="clinical-panel clinical-hero">
              <div className="clinical-hero__copy">
                <p className="clinical-kicker">Caso activo</p>
                <h2>
                  {selectedTask ? selectedTask.title : "Sin caso cargado"}
                </h2>
                <p>
                  Una sola interfaz para conversar con el modelo, revisar el episodio y tener accesos
                  utiles sin que la identidad visual se rompa entre lateral, cabecera y chat.
                </p>
              </div>

              <div className="clinical-hero__stats">
                <div className="clinical-chipcard">
                  <span>Especialidad</span>
                  <strong>{selectedTask?.specialty || "general"}</strong>
                </div>
                <div className="clinical-chipcard">
                  <span>Paciente</span>
                  <strong>{selectedTask?.patient_reference || "sin referencia"}</strong>
                </div>
                <div className="clinical-chipcard">
                  <span>Mensaje</span>
                  <strong>{lastResponse ? `#${lastResponse.message_id}` : "sin envio"}</strong>
                </div>
              </div>
            </section>

            <div className="clinical-grid">
              <aside className="clinical-panel clinical-context">
                <div className="clinical-panel__header">
                  <div>
                    <p className="clinical-kicker">Control del caso</p>
                    <h3>Sesion y acceso rapido</h3>
                  </div>
                  <button
                    type="button"
                    className="clinical-ghostbutton"
                    onClick={() => {
                      setSessionId(buildSessionId());
                      setLastResponse(null);
                    }}
                  >
                    <ClipboardList className="h-4 w-4" />
                    Reiniciar
                  </button>
                </div>

                <div className="clinical-fieldgrid">
                  <div className="clinical-metric">
                    <span>Sesion actual</span>
                    <strong>{sessionId}</strong>
                  </div>
                  <div className="clinical-metric">
                    <span>Casos visibles</span>
                    <strong>{filteredTasks.length}</strong>
                  </div>
                </div>

                <div className="mt-5 flex flex-wrap gap-2">
                  <button
                    type="button"
                    className="clinical-actionbutton"
                    onClick={() => setIsCasePickerOpen((prev) => !prev)}
                  >
                    <Search className="h-4 w-4" />
                    Buscar caso
                  </button>
                  <button type="button" className="clinical-actionbutton" onClick={refreshTasks}>
                    <RefreshCw className="h-4 w-4" />
                    Recargar
                  </button>
                </div>

                {isCasePickerOpen && (
                  <div className="clinical-casepicker">
                    <label className="clinical-searchbox">
                      <Search className="h-4 w-4 text-slate-400" />
                      <input
                        value={caseSearch}
                        onChange={(event) => setCaseSearch(event.target.value)}
                        placeholder="Titulo o referencia de paciente"
                      />
                    </label>

                    <div className="chat-scroll max-h-72 space-y-2 overflow-y-auto pr-1">
                      {filteredTasks.map((task) => (
                        <button
                          type="button"
                          key={task.id}
                          className={`clinical-caseitem ${
                            selectedTaskId === task.id ? "clinical-caseitem--active" : ""
                          }`}
                          onClick={() => {
                            setSelectedTaskId(task.id);
                            setIsCasePickerOpen(false);
                            setCaseSearch("");
                          }}
                        >
                          <div>
                            <p className="font-semibold text-slate-900">#{task.id} {task.title}</p>
                            <p className="text-xs text-slate-500">
                              {task.patient_reference || "sin referencia"} · {task.specialty}
                            </p>
                          </div>
                          <ArrowUpRight className="h-4 w-4 text-slate-400" />
                        </button>
                      ))}
                      {filteredTasks.length === 0 && (
                        <div className="rounded-2xl border border-dashed border-slate-300 px-4 py-3 text-sm text-slate-500">
                          No hay casos que coincidan con el filtro.
                        </div>
                      )}
                    </div>
                  </div>
                )}

                <div className="mt-6 space-y-3">
                  {guidanceCards.map((item) => (
                    <article key={item.title} className="clinical-infoitem">
                      <item.icon className="h-4 w-4 text-cyan-700" />
                      <div>
                        <h4>{item.title}</h4>
                        <p>{item.text}</p>
                      </div>
                    </article>
                  ))}
                </div>
              </aside>

              <section className="clinical-panel clinical-chatpanel">
                <div className="clinical-panel__header">
                  <div>
                    <p className="clinical-kicker">Conversacion</p>
                    <h3>Chat clinico operativo</h3>
                  </div>
                  <div className="flex items-center gap-2">
                    {lastResponse && (
                      <span className="clinical-pill clinical-pill--soft">
                        msg #{lastResponse.message_id}
                      </span>
                    )}
                    <span className="clinical-pill clinical-pill--soft">
                      {selectedTask?.specialty || "general"}
                    </span>
                  </div>
                </div>

                <div className="chat-scroll clinical-transcript">
                  {history.length === 0 && !isBusy && (
                    <div className="clinical-empty">
                      <Bot className="h-6 w-6 text-cyan-700" />
                      <div>
                        <h4>Conversacion vacia</h4>
                        <p>
                          Haz una consulta libre y el chat respondera dentro de la misma experiencia
                          visual, sin bloques incoherentes ni zonas sin estilo.
                        </p>
                      </div>
                    </div>
                  )}

                  {history.map((item) => (
                    <article key={item.id} className="clinical-messagegroup">
                      <div className="clinical-message clinical-message--user">
                        <div className="clinical-avatar clinical-avatar--user">
                          <User className="h-4 w-4" />
                        </div>
                        <div className="clinical-bubble clinical-bubble--user">
                          <p>{item.user_query}</p>
                          <span>{formatTimestamp(item.created_at)}</span>
                        </div>
                      </div>

                      <div className="clinical-message clinical-message--assistant">
                        <div className="clinical-avatar clinical-avatar--assistant">
                          <Bot className="h-4 w-4" />
                        </div>
                        <div className="clinical-bubble clinical-bubble--assistant">
                          <p>{item.assistant_answer}</p>
                          <span>{formatTimestamp(item.created_at)}</span>
                        </div>
                      </div>
                    </article>
                  ))}

                  {isBusy && (
                    <div className="clinical-message clinical-message--assistant">
                      <div className="clinical-avatar clinical-avatar--assistant">
                        <Bot className="h-4 w-4" />
                      </div>
                      <div className="clinical-bubble clinical-bubble--assistant clinical-bubble--loading">
                        Procesando la consulta y actualizando la conversacion...
                      </div>
                    </div>
                  )}
                </div>

                <div className="clinical-quickbar">
                  {quickPrompts.map((item) => (
                    <button
                      key={item}
                      type="button"
                      className="clinical-quickprompt"
                      onClick={() => useQuickPrompt(item)}
                    >
                      {item}
                    </button>
                  ))}
                </div>

                <form onSubmit={handleSend} className="clinical-composer">
                  <div className="clinical-composer__box">
                    <textarea
                      value={query}
                      onChange={(event) => setQuery(event.target.value)}
                      placeholder="Escribe una consulta clinica o conversacional..."
                      disabled={isBusy || !selectedTaskId}
                      rows={3}
                    />
                    <button
                      type="submit"
                      className="clinical-sendbutton"
                      disabled={isBusy || !query.trim() || !selectedTaskId}
                    >
                      <SendHorizonal className="h-4 w-4" />
                    </button>
                  </div>

                  <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                    <span className="clinical-pill clinical-pill--soft">
                      {selectedTaskId ? `Caso #${selectedTaskId}` : "Sin caso"}
                    </span>
                    <span className="clinical-pill clinical-pill--soft">
                      Sesion {sessionId.slice(-8)}
                    </span>
                    <span className="ml-auto flex items-center gap-1 text-amber-700">
                      <AlertTriangle className="h-3.5 w-3.5" />
                      Validar con protocolo local y juicio clinico
                    </span>
                  </div>
                </form>
              </section>
            </div>
          </div>
        </section>
      </div>

      {error && (
        <div className="toast toast-bottom toast-end z-[90]">
          <div className="alert border border-red-300/40 bg-red-950/90 text-red-50 shadow-2xl">
            <span>{error}</span>
          </div>
        </div>
      )}
    </main>
  );
}
