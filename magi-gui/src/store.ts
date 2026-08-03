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
    
    return { 
      conversations: newConversations,
      messages: newConversations[state.activeConversationId] || []
    };
  }),
  
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
  setFileTree: (fileTree) => set({ fileTree })
}));
