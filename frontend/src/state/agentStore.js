import { create } from "zustand";

export const useAgentStore = create((set) => ({
  agents: [],
  activeAgent: null,

  setAgents: (agents) => set({ agents }),

  setActiveAgent: (agent) => set({
    activeAgent: agent
  })
}));