import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

type AuthTokens = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

type CurrentUser = {
  username: string;
  specialty: string;
  is_superuser: boolean;
};

type CareTask = {
  id: number;
  title: string;
  clinical_priority: string;
  specialty: string;
  patient_reference: string | null;
  completed: boolean;
};

type ToolMode = "chat" | "medication" | "cases" | "treatment" | "deep_search" | "images";
type ConversationMode = "auto" | "general" | "clinical";
type ResponseMode = "general" | "clinical";

type ChatHistoryItem = {
  id: number;
  session_id: string;
  clinician_id: string | null;
  effective_specialty: string;
  user_query: string;
  assistant_answer: string;
  matched_domains: string[];
  matched_endpoints: string[];
  knowledge_sources: Array<Record<string, string>>;
  web_sources: Array<Record<string, string>>;
  memory_facts_used: string[];
  patient_history_facts_used: string[];
  extracted_facts: string[];
  created_at: string;
};

type ChatResponse = {
  care_task_id: number;
  message_id: number;
  session_id: string;
  agent_run_id: number;
  workflow_name: string;
  response_mode: ResponseMode;
  tool_mode: ToolMode;
  answer: string;
  matched_domains: string[];
  matched_endpoints: string[];
  effective_specialty: string;
  knowledge_sources: Array<Record<string, string>>;
  web_sources: Array<Record<string, string>>;
  memory_facts_used: string[];
  patient_history_facts_used: string[];
  extracted_facts: string[];
  interpretability_trace: string[];
  non_diagnostic_warning: string;
};

type ChatMemory = {
  care_task_id: number;
  session_id: string | null;
  interactions_count: number;
  top_domains: string[];
  top_extracted_facts: string[];
  patient_reference: string | null;
  patient_interactions_count: number;
  patient_top_domains: string[];
  patient_top_extracted_facts: string[];
};

type ToolItem = {
  key: ToolMode;
  icon: string;
  label: string;
  hint: string;
};

const STORAGE_TOKEN_KEY = "clinical_ops_chat_token";
const STORAGE_API_KEY = "clinical_ops_api_base";
const DEFAULT_API_BASE = "http://127.0.0.1:8000/api/v1";

const TOOL_ITEMS: ToolItem[] = [
  { key: "chat", icon: "💬", label: "Chat", hint: "Conversacion general o clinica" },
  { key: "medication", icon: "💊", label: "Medicacion", hint: "Esquemas y seguridad farmacologica" },
  { key: "cases", icon: "🧾", label: "Casos", hint: "Rutas por cuadro clinico" },
  { key: "treatment", icon: "🩺", label: "Tratamiento", hint: "Plan operativo escalonado" },
  { key: "deep_search", icon: "🔎", label: "Busqueda profunda", hint: "Amplia consulta a fuentes web permitidas" },
  { key: "images", icon: "🖼️", label: "Imagenes", hint: "Soporte de imagen y correlacion clinica" },
];

function formatError(detail: unknown, fallback: string): string {
  if (!detail) {
    return fallback;
  }
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }
        if (typeof item === "object" && item !== null && "msg" in item) {
          return String(item.msg);
        }
        return JSON.stringify(item);
      })
      .join(" | ");
  }
  return fallback;
}

function inferHistoryResponseMode(item: ChatHistoryItem): ResponseMode {
  if (item.extracted_facts.some((fact) => fact.includes("modo_respuesta:general"))) {
    return "general";
  }
  return "clinical";
}

function inferHistoryTool(item: ChatHistoryItem): ToolMode {
  const toolFact = item.extracted_facts.find((fact) => fact.startsWith("herramienta:"));
  if (!toolFact) {
    return "chat";
  }
  const raw = toolFact.replace("herramienta:", "");
  if (TOOL_ITEMS.some((tool) => tool.key === raw)) {
    return raw as ToolMode;
  }
  return "chat";
}


function getTraceValue(trace: string[], key: string): string {
  const prefix = `${key}=`;
  const entry = trace.find((item) => item.startsWith(prefix));
  return entry ? entry.slice(prefix.length) : "n/a";
}

function buildNewSessionId(): string {
  const stamp = new Date().toISOString().replace(/[^0-9]/g, "").slice(0, 12);
  return `session-${stamp}`;
}

export default function App() {
  const [apiBaseUrl, setApiBaseUrl] = useState<string>(
    localStorage.getItem(STORAGE_API_KEY) || DEFAULT_API_BASE,
  );
  const [token, setToken] = useState<string>(localStorage.getItem(STORAGE_TOKEN_KEY) || "");
  const [username, setUsername] = useState("medico_demo");
  const [password, setPassword] = useState("StrongPass123!");
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [tasks, setTasks] = useState<CareTask[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(null);
  const [sessionId, setSessionId] = useState(buildNewSessionId());
  const [query, setQuery] = useState("");
  const [useWebSources, setUseWebSources] = useState(true);
  const [conversationMode, setConversationMode] = useState<ConversationMode>("auto");
  const [selectedTool, setSelectedTool] = useState<ToolMode>("chat");
  const [includeProtocolCatalog, setIncludeProtocolCatalog] = useState(true);
  const [taskTitle, setTaskTitle] = useState("Caso guardia");
  const [taskPatientReference, setTaskPatientReference] = useState("PAC-FE-001");
  const [history, setHistory] = useState<ChatHistoryItem[]>([]);
  const [memory, setMemory] = useState<ChatMemory | null>(null);
  const [lastResponse, setLastResponse] = useState<ChatResponse | null>(null);
  const [isBusy, setIsBusy] = useState(false);
  const [error, setError] = useState("");
  const [statusMessage, setStatusMessage] = useState("Listo.");

  const selectedToolMeta = useMemo(
    () => TOOL_ITEMS.find((tool) => tool.key === selectedTool) ?? TOOL_ITEMS[0],
    [selectedTool],
  );

  const deepSearchEnabled = selectedTool === "deep_search";

  const traceSummary = useMemo(() => {
    if (!lastResponse) {
      return null;
    }
    return {
      llmUsed: getTraceValue(lastResponse.interpretability_trace, "llm_used"),
      llmEndpoint: getTraceValue(lastResponse.interpretability_trace, "llm_endpoint"),
      queryExpanded: getTraceValue(lastResponse.interpretability_trace, "query_expanded"),
      matchedEndpoints: getTraceValue(lastResponse.interpretability_trace, "matched_endpoints"),
    };
  }, [lastResponse]);

  const apiRequest = useCallback(
    async <T,>(path: string, init: RequestInit = {}, tokenOverride?: string): Promise<T> => {
      const headers = new Headers(init.headers || {});
      if (!headers.has("Content-Type") && init.body && !(init.body instanceof FormData)) {
        headers.set("Content-Type", "application/json");
      }
      const activeToken = tokenOverride ?? token;
      if (activeToken) {
        headers.set("Authorization", `Bearer ${activeToken}`);
      }
      const response = await fetch(`${apiBaseUrl}${path}`, { ...init, headers });
      if (!response.ok) {
        let message = `Error ${response.status}`;
        try {
          const errorPayload = await response.json();
          message = formatError(errorPayload?.detail, message);
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
    [apiBaseUrl, token],
  );

  const refreshTasks = useCallback(async () => {
    const result = await apiRequest<CareTask[]>("/care-tasks/?limit=100");
    setTasks(result);
    if (!selectedTaskId && result.length > 0) {
      setSelectedTaskId(result[0].id);
    }
  }, [apiRequest, selectedTaskId]);

  const loadConversation = useCallback(
    async (taskId: number, chatSessionId: string) => {
      const [historyResponse, memoryResponse] = await Promise.all([
        apiRequest<ChatHistoryItem[]>(
          `/care-tasks/${taskId}/chat/messages?session_id=${encodeURIComponent(chatSessionId)}&limit=100`,
        ),
        apiRequest<ChatMemory>(
          `/care-tasks/${taskId}/chat/memory?session_id=${encodeURIComponent(chatSessionId)}`,
        ),
      ]);
      const orderedHistory = [...historyResponse].sort((a, b) =>
        a.created_at.localeCompare(b.created_at),
      );
      setHistory(orderedHistory);
      setMemory(memoryResponse);
    },
    [apiRequest],
  );

  const createDefaultTask = useCallback(async (): Promise<number> => {
    const newTask = await apiRequest<CareTask>("/care-tasks/", {
      method: "POST",
      body: JSON.stringify({
        title: `Conversacion ${new Date().toLocaleString()}`,
        clinical_priority: "medium",
        specialty: currentUser?.specialty || "general",
        patient_reference: null,
        sla_target_minutes: 60,
        human_review_required: true,
        completed: false,
      }),
    });
    await refreshTasks();
    setSelectedTaskId(newTask.id);
    return newTask.id;
  }, [apiRequest, currentUser?.specialty, refreshTasks]);

  useEffect(() => {
    localStorage.setItem(STORAGE_API_KEY, apiBaseUrl);
  }, [apiBaseUrl]);

  useEffect(() => {
    if (!token) {
      setCurrentUser(null);
      setTasks([]);
      setHistory([]);
      setMemory(null);
      setLastResponse(null);
      return;
    }
    let active = true;
    (async () => {
      try {
        const me = await apiRequest<CurrentUser>("/auth/me");
        if (!active) {
          return;
        }
        setCurrentUser(me);
        await refreshTasks();
        setStatusMessage(`Sesion activa como ${me.username} (${me.specialty}).`);
      } catch (exc) {
        if (!active) {
          return;
        }
        setError(`Sesion invalida: ${exc instanceof Error ? exc.message : "error desconocido"}`);
        setToken("");
        localStorage.removeItem(STORAGE_TOKEN_KEY);
      }
    })();
    return () => {
      active = false;
    };
  }, [apiRequest, refreshTasks, token]);

  useEffect(() => {
    if (!selectedTaskId || !sessionId || !token) {
      return;
    }
    loadConversation(selectedTaskId, sessionId).catch(() => undefined);
  }, [loadConversation, selectedTaskId, sessionId, token]);

  const selectedTask = useMemo(
    () => tasks.find((task) => task.id === selectedTaskId) || null,
    [tasks, selectedTaskId],
  );

  const handleLogin = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setIsBusy(true);
    try {
      const body = new URLSearchParams({ username, password });
      const tokens = await apiRequest<AuthTokens>(
        "/auth/login",
        {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: body.toString(),
        },
        "",
      );
      setToken(tokens.access_token);
      localStorage.setItem(STORAGE_TOKEN_KEY, tokens.access_token);
      setStatusMessage("Sesion iniciada.");
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Error de autenticacion.");
    } finally {
      setIsBusy(false);
    }
  };

  const handleLogout = () => {
    setToken("");
    setCurrentUser(null);
    setSelectedTaskId(null);
    setTasks([]);
    setHistory([]);
    setMemory(null);
    setLastResponse(null);
    localStorage.removeItem(STORAGE_TOKEN_KEY);
    setStatusMessage("Sesion cerrada.");
  };

  const handleCreateTask = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setIsBusy(true);
    try {
      const newTask = await apiRequest<CareTask>("/care-tasks/", {
        method: "POST",
        body: JSON.stringify({
          title: taskTitle,
          clinical_priority: "high",
          specialty: currentUser?.specialty || "general",
          patient_reference: taskPatientReference || null,
          sla_target_minutes: 30,
          human_review_required: true,
          completed: false,
        }),
      });
      await refreshTasks();
      setSelectedTaskId(newTask.id);
      setStatusMessage(`Caso ${newTask.id} creado.`);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "No se pudo crear el caso.");
    } finally {
      setIsBusy(false);
    }
  };

  const handleSendMessage = async (event: FormEvent) => {
    event.preventDefault();
    if (!query.trim()) {
      return;
    }
    setError("");
    setIsBusy(true);
    try {
      const activeTaskId = selectedTaskId ?? (await createDefaultTask());
      const response = await apiRequest<ChatResponse>(`/care-tasks/${activeTaskId}/chat/messages`, {
        method: "POST",
        body: JSON.stringify({
          query: query.trim(),
          session_id: sessionId,
          use_web_sources: deepSearchEnabled ? true : useWebSources,
          use_authenticated_specialty_mode: true,
          use_patient_history: true,
          max_history_messages: 25,
          max_patient_history_messages: 40,
          max_web_sources: deepSearchEnabled ? 6 : 3,
          include_protocol_catalog: includeProtocolCatalog,
          conversation_mode: conversationMode,
          tool_mode: selectedTool,
        }),
      });
      setLastResponse(response);
      setQuery("");
      await loadConversation(activeTaskId, sessionId);
      setStatusMessage(
        `Turno ${response.message_id} generado - modo ${response.response_mode} - herramienta ${response.tool_mode}.`,
      );
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "No se pudo enviar mensaje.");
    } finally {
      setIsBusy(false);
    }
  };

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="sidebar-title">
          <h1>Clinical Copilot</h1>
          <p>Chat operativo hospitalario</p>
        </div>

        {currentUser && (
          <div className="user-card">
            <div className="user-main">
              <strong>{currentUser.username}</strong>
              <span>{currentUser.specialty}</span>
            </div>
            <button onClick={handleLogout}>Salir</button>
          </div>
        )}

        <section className="card compact">
          <div className="card-head">
            <h2>Sesion</h2>
            <button onClick={() => setSessionId(buildNewSessionId())}>Nueva</button>
          </div>
          <input value={sessionId} onChange={(event) => setSessionId(event.target.value)} />
        </section>

        <section className="card">
          <h2>Crear caso</h2>
          <form onSubmit={handleCreateTask} className="stack">
            <input
              value={taskTitle}
              onChange={(event) => setTaskTitle(event.target.value)}
              placeholder="Titulo"
            />
            <input
              value={taskPatientReference}
              onChange={(event) => setTaskPatientReference(event.target.value)}
              placeholder="Referencia paciente"
            />
            <button type="submit" disabled={isBusy}>
              Crear
            </button>
          </form>
        </section>

        <section className="card grow">
          <div className="card-head">
            <h2>Casos</h2>
            <button onClick={() => refreshTasks()}>Actualizar</button>
          </div>
          <div className="case-list">
            {tasks.map((task) => (
              <button
                key={task.id}
                className={task.id === selectedTaskId ? "case-item active" : "case-item"}
                onClick={() => setSelectedTaskId(task.id)}
              >
                <span className="case-title">#{task.id} {task.title}</span>
                <span className="case-sub">{task.specialty} - {task.patient_reference || "sin ref"}</span>
              </button>
            ))}
            {tasks.length === 0 && <p className="muted">Sin casos.</p>}
          </div>
        </section>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="topbar-left">
            <span className="status">{statusMessage}</span>
          </div>
          <div className="topbar-right">
            <input
              value={apiBaseUrl}
              onChange={(event) => setApiBaseUrl(event.target.value)}
              className="api-input"
              disabled={isBusy}
            />
          </div>
        </header>

        {!token ? (
          <section className="login-panel">
            <h2>Acceso profesional</h2>
            <form onSubmit={handleLogin} className="stack">
              <input value={username} onChange={(event) => setUsername(event.target.value)} placeholder="Usuario" />
              <input
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Password"
                type="password"
              />
              <button type="submit" disabled={isBusy}>
                {isBusy ? "Accediendo..." : "Entrar"}
              </button>
            </form>
            {error && <p className="error">{error}</p>}
          </section>
        ) : (
          <section className="chat-shell">
            <div className="chat-head">
              <div>
                <h2>{selectedTask ? `Caso #${selectedTask.id}` : "Conversacion libre"}</h2>
                <p>
                  {selectedTask
                    ? `${selectedTask.title} - ${selectedTask.specialty}`
                    : "Si no eliges caso, se crea uno automatico al enviar."}
                </p>
              </div>
              <div className="head-controls compact-controls">
                <label>
                  Herramienta
                  <select
                    value={selectedTool}
                    onChange={(event) => setSelectedTool(event.target.value as ToolMode)}
                  >
                    {TOOL_ITEMS.map((tool) => (
                      <option key={tool.key} value={tool.key}>
                        {tool.icon} {tool.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Modo
                  <select
                    value={conversationMode}
                    onChange={(event) => setConversationMode(event.target.value as ConversationMode)}
                  >
                    <option value="auto">Auto</option>
                    <option value="general">General</option>
                    <option value="clinical">Clinico</option>
                  </select>
                </label>
                <details className="advanced-menu">
                  <summary>Opciones avanzadas</summary>
                  <label className="check">
                    <input
                      type="checkbox"
                      checked={deepSearchEnabled ? true : useWebSources}
                      onChange={(event) => setUseWebSources(event.target.checked)}
                      disabled={deepSearchEnabled}
                    />
                    fuentes web
                  </label>
                  <label className="check">
                    <input
                      type="checkbox"
                      checked={includeProtocolCatalog}
                      onChange={(event) => setIncludeProtocolCatalog(event.target.checked)}
                    />
                    catalogo protocolos
                  </label>
                </details>
              </div>
            </div>

            <div className="selected-tool-hint">
              <strong>{selectedToolMeta.label}</strong> - {selectedToolMeta.hint}
            </div>

            {traceSummary && (
              <div className="trace-pills">
                <span className="chip">llm_used: {traceSummary.llmUsed}</span>
                <span className="chip">llm_endpoint: {traceSummary.llmEndpoint}</span>
                <span className="chip">query_expanded: {traceSummary.queryExpanded}</span>
                <span className="chip">matched_endpoints: {traceSummary.matchedEndpoints}</span>
              </div>
            )}

            <div className="timeline">
              {history.map((item) => {
                const historyMode = inferHistoryResponseMode(item);
                const historyTool = inferHistoryTool(item);
                return (
                  <article key={item.id} className="turn">
                    <div className="bubble user">{item.user_query}</div>
                    <div className="bubble assistant">
                      <div className="bubble-meta">
                        <span className="chip">{historyMode}</span>
                        <span className="chip">{historyTool}</span>
                        <span className="chip">{item.effective_specialty}</span>
                      </div>
                      <pre>{item.assistant_answer}</pre>
                    </div>
                  </article>
                );
              })}
              {history.length === 0 && <p className="muted">Sin mensajes en esta sesion.</p>}
            </div>

            <form className="composer" onSubmit={handleSendMessage}>
              <textarea
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Escribe una consulta. Puedes hablar en general o en clave clinica."
                rows={4}
                disabled={isBusy}
              />
              <div className="composer-row">
                <span className="mode-tag">
                  {conversationMode} - {selectedTool}
                </span>
                <button type="submit" disabled={isBusy || query.trim().length < 2}>
                  {isBusy ? "Procesando..." : "Enviar"}
                </button>
              </div>
            </form>

            {error && <p className="error">{error}</p>}
          </section>
        )}
      </main>

      <aside className="inspector">
        <section className="card">
          <h2>Memoria</h2>
          {memory ? (
            <dl className="kv">
              <div>
                <dt>Interacciones</dt>
                <dd>{memory.interactions_count}</dd>
              </div>
              <div>
                <dt>Paciente</dt>
                <dd>{memory.patient_reference || "N/A"}</dd>
              </div>
              <div>
                <dt>Top dominios</dt>
                <dd>{memory.top_domains.join(", ") || "N/A"}</dd>
              </div>
              <div>
                <dt>Top hechos</dt>
                <dd>{memory.top_extracted_facts.join(", ") || "N/A"}</dd>
              </div>
            </dl>
          ) : (
            <p className="muted">Sin memoria cargada.</p>
          )}
        </section>

        <section className="card">
          <h2>Ultima respuesta</h2>
          {lastResponse ? (
            <>
              <p><strong>Run:</strong> {lastResponse.agent_run_id}</p>
              <p><strong>Modo:</strong> {lastResponse.response_mode}</p>
              <p><strong>Herramienta:</strong> {lastResponse.tool_mode}</p>
              <p><strong>Fuentes:</strong> {lastResponse.knowledge_sources.length} internas / {lastResponse.web_sources.length} web</p>
              <p><strong>Endpoints:</strong> {lastResponse.matched_endpoints.join(", ") || "N/A"}</p>
              <details>
                <summary>Trazabilidad</summary>
                <ul>
                  {lastResponse.interpretability_trace.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </details>
            </>
          ) : (
            <p className="muted">Sin respuesta reciente.</p>
          )}
        </section>
      </aside>
    </div>
  );
}
