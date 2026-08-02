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
  
  messages: AgentMessage[];
  addMessage: (msg: AgentMessage) => void;
  
  terminalOutput: string;
  appendTerminal: (text: string) => void;
  
  sysCommand: (cmd: string) => void;

  projects: Project[];
  setProjects: (projects: Project[]) => void;

  metrics: Metrics;
  setMetrics: (metrics: Metrics) => void;

  telemetry: any[];
  setTelemetry: (data: any[]) => void;
}

export const useMagiStore = create<MagiState>((set) => ({
  connected: false,
  setConnected: (status) => set({ connected: status }),
  
  messages: [],
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  
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
  setTelemetry: (telemetry) => set({ telemetry })
}));
