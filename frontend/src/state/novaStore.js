import { create } from "zustand";

export const useNovaStore = create((set)=>({

  system:{},
  agents:[],
  opportunities:[],
  execution:[],
  logs:[],

  loading:true,

  setSystem:(data)=>set({system:data}),
  setAgents:(data)=>set({agents:data}),
  setOpportunities:(data)=>set({opportunities:data}),
  setExecution:(data)=>set({execution:data}),
  setLogs:(data)=>set({logs:data}),

  setLoading:(v)=>set({loading:v})

}));