import { create } from "zustand";

export const useOpportunityStore = create((set) => ({
  opportunities: [],
  selectedOpportunity: null,

  setOpportunities: (data) =>
    set({ opportunities: data }),

  setSelectedOpportunity: (data) =>
    set({ selectedOpportunity: data })
}));