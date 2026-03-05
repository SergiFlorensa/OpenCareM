import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  Bot,
  ClipboardList,
  RefreshCw,
  Search,
  SendHorizonal,
  Sparkles,
  User,
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
          tool_mode: "chat",
          use_web_sources: false,
          use_patient_history: true,
          use_authenticated_specialty_mode: false,
          include_protocol_catalog: true,
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

  return (
    <main data-theme="clinical" className="min-h-full bg-[radial-gradient(circle_at_top_left,#0f172a_20%,#111827_60%,#0b1220_100%)] p-4 md:p-8">
      <section className="mx-auto grid w-full max-w-6xl gap-4 rounded-3xl border border-base-300/50 bg-base-100/95 p-4 shadow-soft backdrop-blur md:grid-cols-[320px_1fr] md:p-6">
        <aside className="rounded-2xl border border-base-300 bg-base-200/80 p-4">
          <div className="mb-4 flex items-center gap-3">
            <div className="rounded-xl bg-primary/15 p-2 text-primary">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-neutral">Clinical Chat</h1>
              <p className="text-xs text-slate-500">Interfaz moderna sin login</p>
            </div>
          </div>

          <div className="grid gap-3">
            <label className="input input-bordered input-sm flex items-center gap-2 bg-base-100">
              <Activity className="h-4 w-4 text-slate-500" />
              <input
                value={apiBaseUrl}
                onChange={(e) => setApiBaseUrl(e.target.value)}
                aria-label="API base"
                className="grow"
              />
            </label>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="rounded-xl bg-base-100 p-3">
                <p className="text-slate-500">Casos</p>
                <p className="text-xl font-semibold text-neutral">{tasks.length}</p>
              </div>
              <div className="rounded-xl bg-base-100 p-3">
                <p className="text-slate-500">Sesión</p>
                <p className="truncate text-xs font-medium text-neutral">{sessionId}</p>
              </div>
            </div>

            <div className="flex gap-2">
              <button type="button" className="btn btn-primary btn-sm flex-1" onClick={refreshTasks}>
                <RefreshCw className="h-4 w-4" /> Actualizar
              </button>
              <button
                type="button"
                className="btn btn-outline btn-sm flex-1"
                onClick={() => setSessionId(buildSessionId())}
              >
                <ClipboardList className="h-4 w-4" /> Nueva
              </button>
            </div>

            <button
              type="button"
              className="btn btn-ghost btn-sm justify-start"
              onClick={() => setIsCasePickerOpen((prev) => !prev)}
            >
              <Search className="h-4 w-4" />
              {isCasePickerOpen ? "Ocultar casos" : "Buscar caso"}
            </button>

            {isCasePickerOpen && (
              <div className="animate-fadeInUp space-y-2 rounded-xl border border-base-300 bg-base-100 p-3">
                <label className="input input-bordered input-sm flex items-center gap-2">
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
                          : "border-base-300 bg-base-100 hover:bg-base-200"
                      }`}
                      onClick={() => {
                        setSelectedTaskId(task.id);
                        setIsCasePickerOpen(false);
                        setCaseSearch("");
                      }}
                    >
                      <p className="text-sm font-semibold text-neutral">#{task.id} {task.title}</p>
                      <p className="text-xs text-slate-500">{task.patient_reference || "sin referencia"}</p>
                    </button>
                  ))}
                  {filteredTasks.length === 0 && (
                    <p className="rounded-lg bg-base-200 p-2 text-xs text-slate-500">Sin resultados.</p>
                  )}
                </div>
              </div>
            )}
          </div>
        </aside>

        <section className="flex min-h-[72vh] flex-col rounded-2xl border border-base-300 bg-base-200/60">
          <header className="flex items-center justify-between border-b border-base-300 px-4 py-3">
            <div>
              <p className="text-sm font-semibold text-neutral">{selectedTask ? selectedTask.title : "Selecciona un caso"}</p>
              <p className="text-xs text-slate-500">Paciente: {selectedTask?.patient_reference || "N/A"}</p>
            </div>
            <div className="badge badge-outline badge-info gap-1">
              <Sparkles className="h-3.5 w-3.5" /> Auto-routing
            </div>
          </header>

          <div className="chat-scroll flex-1 space-y-4 overflow-y-auto p-4">
            {history.length === 0 && (
              <div className="rounded-xl border border-dashed border-base-300 bg-base-100 p-5 text-sm text-slate-500">
                Sin mensajes todavía. Haz una consulta clínica y te respondo con trazabilidad.
              </div>
            )}

            {history.map((item) => (
              <article key={item.id} className="space-y-2 animate-fadeInUp">
                <div className="chat chat-end">
                  <div className="chat-image avatar placeholder">
                    <div className="w-8 rounded-full bg-primary text-primary-content">
                      <User className="h-4 w-4" />
                    </div>
                  </div>
                  <div className="chat-bubble chat-bubble-primary text-primary-content whitespace-pre-wrap">{item.user_query}</div>
                </div>
                <div className="chat chat-start">
                  <div className="chat-image avatar placeholder">
                    <div className="w-8 rounded-full bg-neutral text-neutral-content">
                      <Bot className="h-4 w-4" />
                    </div>
                  </div>
                  <div className="chat-bubble whitespace-pre-wrap bg-base-100 text-neutral border border-base-300">{item.assistant_answer}</div>
                </div>
              </article>
            ))}

            {isBusy && (
              <div className="chat chat-start animate-pulse">
                <div className="chat-image avatar placeholder">
                  <div className="w-8 rounded-full bg-neutral text-neutral-content">
                    <Bot className="h-4 w-4" />
                  </div>
                </div>
                <div className="chat-bubble border border-base-300 bg-base-100 text-slate-500">Procesando respuesta...</div>
              </div>
            )}
          </div>

          <form onSubmit={handleSend} className="border-t border-base-300 bg-base-100 p-3">
            <div className="flex items-center gap-2">
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Escribe tu consulta clínica..."
                disabled={isBusy || !selectedTaskId}
                className="input input-bordered w-full"
              />
              <button type="submit" className="btn btn-primary" disabled={isBusy || !query.trim() || !selectedTaskId}>
                <SendHorizonal className="h-4 w-4" />
              </button>
            </div>

            <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
              {lastResponse && (
                <>
                  <span className="badge badge-outline">#{lastResponse.message_id}</span>
                  <span className="badge badge-outline badge-info">{lastResponse.response_mode}</span>
                </>
              )}
              <span className="ml-auto text-slate-500">Enter para enviar</span>
            </div>
          </form>
        </section>
      </section>

      {error && (
        <div className="toast toast-bottom toast-end">
          <div className="alert alert-error text-error-content">
            <span>{error}</span>
          </div>
        </div>
      )}
    </main>
  );
}

