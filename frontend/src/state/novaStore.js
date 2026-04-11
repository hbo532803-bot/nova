import { create } from "zustand";

export const useNovaStore = create((set)=>({

  systemState:{},
  confidence:{},
  agents:[],
  opportunities:[], // proposals
  experiments:[],
  commands:[],
  reflections:[],
  playbooks:{},
  experimentAnalytics:{},
  agentActivity:[],
  confidenceTrend:[],
  stabilityHealth:{},
  agentProductivity:[],
  knowledgeGraph:{},
  portfolioHealth:{},
  currentStrategy:{},
  knowledgeInsights:{},
  cognitiveLast:{},
  researchLast:{},
  logs:[],
  apiError:"",
  initialized:false,
  realtimeConnected:false,
  realtimeFallback:false,

  loading:true,

  setSystemState:(data)=>set({systemState:data}),
  setConfidence:(data)=>set({confidence:data}),
  setAgents:(data)=>set({agents:data}),
  setOpportunities:(data)=>set({opportunities:data}),
  setExperiments:(data)=>set({experiments:data}),
  setCommands:(data)=>set({commands:data}),
  setReflections:(data)=>set({reflections:data}),
  setPlaybooks:(data)=>set({playbooks:data}),
  setExperimentAnalytics:(data)=>set({experimentAnalytics:data}),
  setAgentActivity:(data)=>set({agentActivity:data}),
  setConfidenceTrend:(data)=>set({confidenceTrend:data}),
  setStabilityHealth:(data)=>set({stabilityHealth:data}),
  setAgentProductivity:(data)=>set({agentProductivity:data}),
  setKnowledgeGraph:(data)=>set({knowledgeGraph:data}),
  setPortfolioHealth:(data)=>set({portfolioHealth:data}),
  setCurrentStrategy:(data)=>set({currentStrategy:data}),
  setKnowledgeInsights:(data)=>set({knowledgeInsights:data}),
  setCognitiveLast:(data)=>set({cognitiveLast:data}),
  setResearchLast:(data)=>set({researchLast:data}),
  setLogs:(data)=>set({logs:data}),
  setApiError:(msg)=>set({apiError:msg}),
  setInitialized:(v)=>set({initialized:v}),
  setRealtimeConnected:(v)=>set({realtimeConnected:v}),
  setRealtimeFallback:(v)=>set({realtimeFallback:v}),

  setLoading:(v)=>set({loading:v})

}));
