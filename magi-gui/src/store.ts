import { create } from 'zustand';

export interface AgentMessage {
  id: string;
  agent: string;
  role: string;
  provider: string;
  content: string;
  changes: number;
  stats: string;
}

export interface Project {
  name: string;
  desc: string;
}

export interface Metrics {
  prov_a: string;
  prov_b: string;
  prov_c: string;
  status: string;
}

interface MagiState {
  connected: boolean;
  setConnected: (status: boolean) => void;
  
  activeConversationId: string;
  setActiveConversationId: (id: string) => void;
  conversations: Record<string, AgentMessage[]>;
  
  // Getter derivado para compatibilidad
  messages: AgentMessage[]; 
  
  addMessage: (msg: AgentMessage & { task_id?: string }) => void;
  // MAGI 9.0 §1.2 — streaming token a token
  streaming: Record<string, { agent: string; text: string; provider: string; family: string }>;
  appendDelta: (d: { task_id: string; agent: string; text: string; provider?: string; family?: string }) => void;
  endDelta: (d: { task_id: string; agent: string }) => void;
  // §2.2 — traza de herramientas: convierte una caja negra en un colaborador
  toolTrace: Array<{ id: string; task_id: string; agent: string; tool: string; ok?: boolean; error?: string | null }>;
  addToolUse: (d: { task_id: string; agent: string; calls: any[] }) => void;
  addToolResult: (d: { task_id: string; agent: string; results: any[] }) => void;
  // §2.3 — por qué ruta fue la petición
  route: { route: string; reason: string; max_rounds: number } | null;
  setRoute: (r: any) => void;
  startNewConversation: (id?: string) => void;
  
  terminalOutput: string;
  appendTerminal: (text: string) => void;
  
  sysCommand: (cmd: string) => void;

  projects: Project[];
  setProjects: (projects: Project[]) => void;

  metrics: Metrics;
  setMetrics: (metrics: Metrics) => void;

  telemetry: any[];
  setTelemetry: (data: any[]) => void;

  fileTree: any[];
  setFileTree: (tree: any[]) => void;

  activeFilePath: string | null;
  activeFileContent: string;
  setActiveFile: (path: string, content: string) => void;

  naokoMessages: AgentMessage[];
  addNaokoMessage: (msg: AgentMessage) => void;
  naokoStatus: string;
  setNaokoStatus: (status: string) => void;
}

export const useMagiStore = create<MagiState>((set) => ({
  connected: false,
  setConnected: (status) => set({ connected: status }),
  
  activeConversationId: "default",
  conversations: { "default": [] },
  messages: [],
  
  setActiveConversationId: (id) => set((state) => ({ 
    activeConversationId: id,
    messages: state.conversations[id] || []
  })),
  
  startNewConversation: (id) => set((state) => {
    const newId = id || `task_${Math.random().toString(36).substring(2, 10)}`;
    return {
      activeConversationId: newId,
      conversations: { ...state.conversations, [newId]: [] },
      messages: []
    };
  }),

  addMessage: (msg) => set((state) => {
    const targetId = msg.task_id || state.activeConversationId;
    const currentList = state.conversations[targetId] || [];
    const newConversations = { ...state.conversations, [targetId]: [...currentList, msg] };

    // El AGENT_POST definitivo reemplaza al buffer de streaming del mismo agente.
    const streaming = { ...state.streaming };
    delete streaming[`${targetId}:${msg.agent}`];

    return {
      conversations: newConversations,
      messages: newConversations[state.activeConversationId] || [],
      streaming,
    };
  }),
  
  // Buffers de streaming, indexados por task_id+agente. Se vacían cuando
  // llega el AGENT_POST definitivo con el texto completo.
  streaming: {},
  appendDelta: (d) => set((state) => {
    const key = `${d.task_id}:${d.agent}`;
    const prev = state.streaming[key];
    return {
      streaming: {
        ...state.streaming,
        [key]: {
          agent: d.agent,
          text: (prev?.text || "") + d.text,
          provider: d.provider || prev?.provider || "",
          family: d.family || prev?.family || "",
        },
      },
    };
  }),
  endDelta: (d) => set((state) => {
    const next = { ...state.streaming };
    delete next[`${d.task_id}:${d.agent}`];
    return { streaming: next };
  }),

  toolTrace: [],
  addToolUse: (d) => set((state) => ({
    toolTrace: [
      ...state.toolTrace.slice(-80),
      ...d.calls.map((c: any) => ({
        id: Math.random().toString(36),
        task_id: d.task_id, agent: d.agent, tool: c.tool,
      })),
    ],
  })),
  addToolResult: (d) => set((state) => {
    // Marca los últimos usos pendientes de este agente con su resultado.
    const trace = [...state.toolTrace];
    for (const r of d.results) {
      for (let i = trace.length - 1; i >= 0; i--) {
        if (trace[i].agent === d.agent && trace[i].tool === r.tool
            && trace[i].ok === undefined) {
          trace[i] = { ...trace[i], ok: r.ok, error: r.error };
          break;
        }
      }
    }
    return { toolTrace: trace };
  }),

  route: null,
  setRoute: (r) => set({ route: r }),

  terminalOutput: "",
  appendTerminal: (text) => set((state) => ({ terminalOutput: state.terminalOutput + text + "\n" })),
  
  sysCommand: (cmd) => {
    set((state) => ({ terminalOutput: state.terminalOutput + `\nroot@system:~# ${cmd}` }));
  },

  projects: [],
  setProjects: (projects) => set({ projects }),

  metrics: { prov_a: "0/0", prov_b: "0/0", prov_c: "0/0", status: "offline" },
  setMetrics: (metrics) => set({ metrics }),

  telemetry: [],
  setTelemetry: (telemetry) => set({ telemetry }),

  fileTree: [],
  setFileTree: (fileTree) => set({ fileTree }),

  activeFilePath: null,
  activeFileContent: "",
  setActiveFile: (path, content) => set({ activeFilePath: path, activeFileContent: content }),

  naokoMessages: [],
  naokoStatus: "Inactiva",
  addNaokoMessage: (msg) => set((state) => ({ naokoMessages: [...state.naokoMessages, msg] })),
  setNaokoStatus: (status) => set({ naokoStatus: status })
}));
