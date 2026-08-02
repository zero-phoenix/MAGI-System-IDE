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

interface MagiState {
  connected: boolean;
  setConnected: (status: boolean) => void;
  
  messages: AgentMessage[];
  addMessage: (msg: AgentMessage) => void;
  
  terminalOutput: string;
  appendTerminal: (text: string) => void;
  
  sysCommand: (cmd: string) => void;
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
  }
}));
