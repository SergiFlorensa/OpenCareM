import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Bot,
  Brain,
  ChevronRight,
  ClipboardList,
  FileText,
  HeartPulse,
  History,
  Menu,
  Pill,
  Plus,
  RefreshCw,
  Search,
  SendHorizonal,
  Shield,
  Sparkles,
  Stethoscope,
  User,
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
  "Sepsis con lactato elevado: prioridades 0-10 minutos",
  "Dolor toracico agudo: descarte inicial y escalado",
  "Hiperkalemia con QRS ancho: pasos inmediatos",
  "Neutropenia febril: ruta operativa en urgencias",
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

export default function App() {
  const [apiBaseUrl, setApiBaseUrl] = useState(() =>
    normalizeApiBase(localStorage.getItem(STORAGE_API_KEY)),
  );
  const [tasks, setTasks] = useState<CareTask[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(null);
  const [isCasePickerOpen, setIsCasePickerOpen] = useState(false);
  const [caseSearch, setCaseSearch] = useState("");
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

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
        setError(exc instanceof Error ? exc.message : "No se pudo cargar la aplicación");
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
          pipeline_relaxed_mode: true,
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
    <main
      data-theme="clinical"
      className="relative min-h-full overflow-hidden bg-[#f8f9fb] text-slate-900 selection:bg-teal-100"
    >
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -right-32 -top-32 h-96 w-96 rounded-full bg-cyan-200/30 blur-3xl" />
        <div className="absolute -left-24 bottom-0 h-80 w-80 rounded-full bg-violet-200/25 blur-3xl" />
      </div>

      <div className="relative flex h-full min-h-screen">
        {isSidebarOpen && (
          <button
            className="fixed inset-0 z-30 bg-slate-900/40 backdrop-blur-sm md:hidden"
            onClick={() => setIsSidebarOpen(false)}
            aria-label="Cerrar menú"
          />
        )}

        <aside
          className={`fixed z-40 h-full w-[300px] flex-col border-r border-slate-800/70 bg-gradient-to-b from-[#0f172a] via-[#111d35] to-[#0c1425] text-white transition-transform duration-300 md:relative md:translate-x-0 ${
            isSidebarOpen ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          <div className="flex h-full flex-col">
            <div className="flex items-center justify-between p-5">
              <div className="flex items-center gap-3">
                <div className="relative rounded-2xl bg-gradient-to-br from-teal-400 to-blue-500 p-2.5 shadow-lg shadow-teal-700/30">
                  <Brain className="h-5 w-5 text-white" />
                  <span className="absolute -right-1 -top-1 h-3 w-3 rounded-full bg-emerald-400 ring-2 ring-[#0f172a]" />
                </div>
                <div>
                  <p className="text-sm font-semibold">ClinicalOps AI</p>
                  <p className="text-[11px] text-teal-300/80">Chat clínico operativo</p>
                </div>
              </div>
              <button
                onClick={() => setIsSidebarOpen(false)}
                className="rounded-xl p-2 text-white/60 hover:bg-white/10 md:hidden"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="px-4 pb-2">
              <button
                className="btn btn-sm w-full justify-start border-teal-300/20 bg-teal-500/20 text-teal-100 hover:bg-teal-500/30"
                onClick={() => setSessionId(buildSessionId())}
              >
                <Plus className="h-4 w-4" /> Nueva conversación
              </button>
            </div>

            <div className="flex-1 space-y-6 overflow-y-auto px-4 py-3">
              <section>
                <p className="mb-2 px-2 text-[11px] font-semibold uppercase tracking-wider text-white/40">
                  Modos IA
                </p>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { icon: Stethoscope, label: "Dx" },
                    { icon: Pill, label: "Farma" },
                    { icon: HeartPulse, label: "Urgencias" },
                  ].map((mode) => (
                    <div
                      key={mode.label}
                      className="rounded-2xl border border-white/10 bg-white/5 p-3 text-center"
                    >
                      <mode.icon className="mx-auto mb-1 h-4 w-4 text-cyan-200" />
                      <p className="text-[10px] text-white/70">{mode.label}</p>
                    </div>
                  ))}
                </div>
              </section>

              <section>
                <p className="mb-2 px-2 text-[11px] font-semibold uppercase tracking-wider text-white/40">
                  Navegación
                </p>
                <div className="space-y-1">
                  {[
                    { icon: History, label: "Historial clínico" },
                    { icon: FileText, label: "Registros" },
                    { icon: Activity, label: "Signos vitales" },
                  ].map((item) => (
                    <button
                      key={item.label}
                      className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm text-white/70 transition hover:bg-white/10 hover:text-white"
                      type="button"
                    >
                      <item.icon className="h-4 w-4 text-white/50" />
                      {item.label}
                      <ChevronRight className="ml-auto h-3.5 w-3.5 opacity-50" />
                    </button>
                  ))}
                </div>
              </section>

              <section className="rounded-2xl border border-emerald-300/20 bg-emerald-500/10 p-3">
                <div className="flex items-center gap-2 text-emerald-200">
                  <Shield className="h-4 w-4" />
                  <p className="text-xs font-medium">TLS + trazabilidad activa</p>
                </div>
              </section>
            </div>

            <div className="border-t border-white/10 p-4">
              <p className="text-xs text-white/60">API base</p>
              <label className="mt-2 flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2">
                <Activity className="h-4 w-4 text-white/50" />
                <input
                  value={apiBaseUrl}
                  onChange={(e) => setApiBaseUrl(e.target.value)}
                  className="w-full bg-transparent text-xs text-white placeholder:text-white/40 focus:outline-none"
                  aria-label="API base"
                />
              </label>
            </div>
          </div>
        </aside>

        <section className="flex min-w-0 flex-1 flex-col">
          <header className="flex items-center justify-between border-b border-slate-200 bg-white/70 px-4 py-3 backdrop-blur-xl md:px-6">
            <div className="flex items-center gap-3">
              <button
                className="rounded-xl border border-slate-200 p-2 text-slate-600 md:hidden"
                onClick={() => setIsSidebarOpen(true)}
                aria-label="Abrir menú"
              >
                <Menu className="h-4 w-4" />
              </button>
              <div>
                <p className="text-sm font-semibold text-slate-800">
                  {selectedTask ? selectedTask.title : "Selecciona un caso"}
                </p>
                <p className="text-xs text-slate-500">
                  Paciente: {selectedTask?.patient_reference || "N/A"} · Especialidad: {selectedTask?.specialty || "general"}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="badge badge-info badge-outline gap-1">
                <Sparkles className="h-3.5 w-3.5" /> Auto-routing
              </span>
              <button className="btn btn-sm btn-primary" onClick={refreshTasks}>
                <RefreshCw className="h-4 w-4" />
              </button>
            </div>
          </header>

          <div className="grid min-h-0 flex-1 gap-4 p-4 md:grid-cols-[320px_1fr] md:p-6">
            <aside className="order-2 rounded-2xl border border-slate-200 bg-white/80 p-4 shadow-soft md:order-1">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-slate-800">Casos y sesión</h2>
                <button
                  type="button"
                  className="btn btn-ghost btn-xs"
                  onClick={() => setSessionId(buildSessionId())}
                >
                  <ClipboardList className="h-3.5 w-3.5" /> Nueva
                </button>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="rounded-xl bg-slate-100 p-3">
                  <p className="text-slate-500">Casos</p>
                  <p className="text-xl font-semibold text-slate-800">{tasks.length}</p>
                </div>
                <div className="rounded-xl bg-slate-100 p-3">
                  <p className="text-slate-500">Sesión</p>
                  <p className="truncate text-xs font-medium text-slate-800">{sessionId}</p>
                </div>
              </div>

              <div className="mt-3 flex gap-2">
                <button
                  type="button"
                  className="btn btn-outline btn-sm flex-1"
                  onClick={() => setIsCasePickerOpen((prev) => !prev)}
                >
                  <Search className="h-4 w-4" /> Buscar caso
                </button>
                <button type="button" className="btn btn-primary btn-sm" onClick={refreshTasks}>
                  <RefreshCw className="h-4 w-4" />
                </button>
              </div>

              {isCasePickerOpen && (
                <div className="mt-3 space-y-2 rounded-xl border border-slate-200 bg-slate-50 p-3">
                  <label className="input input-bordered input-sm flex items-center gap-2 bg-white">
                    <Search className="h-4 w-4 text-slate-400" />
                    <input
                      value={caseSearch}
                      onChange={(e) => setCaseSearch(e.target.value)}
                      placeholder="Filtra por título o paciente"
                      className="grow"
                    />
                  </label>
                  <div className="max-h-56 space-y-2 overflow-y-auto pr-1">
                    {filteredTasks.map((task) => (
                      <button
                        type="button"
                        key={task.id}
                        className={`w-full rounded-xl border p-2 text-left transition ${
                          selectedTaskId === task.id
                            ? "border-primary bg-primary/10"
                            : "border-slate-200 bg-white hover:bg-slate-100"
                        }`}
                        onClick={() => {
                          setSelectedTaskId(task.id);
                          setIsCasePickerOpen(false);
                          setCaseSearch("");
                        }}
                      >
                        <p className="text-sm font-semibold text-slate-800">#{task.id} {task.title}</p>
                        <p className="text-xs text-slate-500">{task.patient_reference || "sin referencia"}</p>
                      </button>
                    ))}
                    {filteredTasks.length === 0 && (
                      <p className="rounded-lg bg-white p-2 text-xs text-slate-500">Sin resultados.</p>
                    )}
                  </div>
                </div>
              )}

              <div className="mt-4">
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Prompts rápidos</p>
                <div className="space-y-2">
                  {quickPrompts.map((item) => (
                    <button
                      key={item}
                      type="button"
                      className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-left text-xs text-slate-700 hover:bg-slate-50"
                      onClick={() => useQuickPrompt(item)}
                    >
                      {item}
                    </button>
                  ))}
                </div>
              </div>
            </aside>

            <section className="order-1 flex min-h-[70vh] min-w-0 flex-col rounded-2xl border border-slate-200 bg-white/85 shadow-soft md:order-2">
              <div className="border-b border-slate-200 px-4 py-3">
                <div className="flex items-center gap-2">
                  <Brain className="h-4 w-4 text-cyan-600" />
                  <p className="text-sm font-semibold text-slate-800">Workspace clínico</p>
                </div>
                <p className="mt-1 text-xs text-slate-500">
                  Resumen operativo, prioridades y fuentes trazables en cada respuesta.
                </p>
              </div>

              <div className="chat-scroll flex-1 space-y-4 overflow-y-auto p-4">
                {history.length === 0 && (
                  <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-5 text-sm text-slate-500">
                    Sin mensajes todavía. Haz una consulta clínica y te respondo con trazabilidad.
                  </div>
                )}

                {history.map((item) => (
                  <article key={item.id} className="space-y-2 animate-fadeInUp">
                    <div className="chat chat-end">
                      <div className="chat-image avatar placeholder">
                        <div className="w-8 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 text-white">
                          <User className="h-4 w-4" />
                        </div>
                      </div>
                      <div className="chat-bubble chat-bubble-primary whitespace-pre-wrap text-primary-content">
                        {item.user_query}
                      </div>
                    </div>
                    <div className="chat chat-start">
                      <div className="chat-image avatar placeholder">
                        <div className="w-8 rounded-full bg-gradient-to-br from-teal-500 to-cyan-600 text-white">
                          <Bot className="h-4 w-4" />
                        </div>
                      </div>
                      <div className="chat-bubble max-w-[90%] whitespace-pre-wrap border border-slate-200 bg-white text-slate-700">
                        {item.assistant_answer}
                      </div>
                    </div>
                  </article>
                ))}

                {isBusy && (
                  <div className="chat chat-start animate-pulse">
                    <div className="chat-image avatar placeholder">
                      <div className="w-8 rounded-full bg-gradient-to-br from-teal-500 to-cyan-600 text-white">
                        <Bot className="h-4 w-4" />
                      </div>
                    </div>
                    <div className="chat-bubble border border-slate-200 bg-white text-slate-500">
                      Procesando respuesta clínica...
                    </div>
                  </div>
                )}
              </div>

              <form onSubmit={handleSend} className="border-t border-slate-200 bg-slate-50/70 p-3">
                <div className="flex items-center gap-2">
                  <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Escribe tu consulta clínica..."
                    disabled={isBusy || !selectedTaskId}
                    className="input input-bordered w-full bg-white"
                  />
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={isBusy || !query.trim() || !selectedTaskId}
                  >
                    <SendHorizonal className="h-4 w-4" />
                  </button>
                </div>

                <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
                  {lastResponse && (
                    <>
                      <span className="badge badge-outline">#{lastResponse.message_id}</span>
                    </>
                  )}
                  <span className="ml-auto flex items-center gap-1 text-amber-700/80">
                    <AlertTriangle className="h-3.5 w-3.5" /> Validar con protocolo local
                  </span>
                </div>
              </form>
            </section>
          </div>
        </section>
      </div>

      {error && (
        <div className="toast toast-bottom toast-end z-[90]">
          <div className="alert alert-error text-error-content">
            <span>{error}</span>
          </div>
        </div>
      )}
    </main>
  );
}
