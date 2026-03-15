import { create } from "zustand";

export const useExecutionStore = create((set) => ({
  plan: [],
  tasks: [],

  setPlan: (plan) =>
    set({ plan }),

  setTasks: (tasks) =>
    set({ tasks })
}));