import { useEffect } from "react";
import { useNovaStore } from "../state/novaStore";
import {
  getSystemState,
  getConfidence,
  listAgents,
  listOpportunities,
  listExperiments,
  listPlaybooks,
  listCommands,
  listReflections,
  getExperimentAnalytics,
  getAgentActivity,
  getConfidenceTrend,
  getStabilityHealth
  ,getAgentProductivity
  ,getKnowledgeGraphSummary
  ,getPortfolioHealth
  ,getCurrentStrategy
  ,getKnowledgeInsights
  ,getCognitiveLast
  ,getResearchLast
} from "../services/consoleApi";

export default function useNovaSystem(){

  const setSystemState = useNovaStore(s=>s.setSystemState);
  const setConfidence = useNovaStore(s=>s.setConfidence);
  const setAgents = useNovaStore(s=>s.setAgents);
  const setOpportunities = useNovaStore(s=>s.setOpportunities);
  const setExperiments = useNovaStore(s=>s.setExperiments);
  const setCommands = useNovaStore(s=>s.setCommands);
  const setReflections = useNovaStore(s=>s.setReflections);
  const setPlaybooks = useNovaStore(s=>s.setPlaybooks);
  const setExperimentAnalytics = useNovaStore(s=>s.setExperimentAnalytics);
  const setAgentActivity = useNovaStore(s=>s.setAgentActivity);
  const setConfidenceTrend = useNovaStore(s=>s.setConfidenceTrend);
  const setStabilityHealth = useNovaStore(s=>s.setStabilityHealth);
  const setAgentProductivity = useNovaStore(s=>s.setAgentProductivity);
  const setKnowledgeGraph = useNovaStore(s=>s.setKnowledgeGraph);
  const setPortfolioHealth = useNovaStore(s=>s.setPortfolioHealth);
  const setCurrentStrategy = useNovaStore(s=>s.setCurrentStrategy);
  const setKnowledgeInsights = useNovaStore(s=>s.setKnowledgeInsights);
  const setCognitiveLast = useNovaStore(s=>s.setCognitiveLast);
  const setResearchLast = useNovaStore(s=>s.setResearchLast);
  const setApiError = useNovaStore(s=>s.setApiError);
  const setLoading = useNovaStore(s=>s.setLoading);
  const setInitialized = useNovaStore(s=>s.setInitialized);

  useEffect(()=>{

    let inFlight = false;
    let tick = 0;
    let abort = null;

    async function load(){

      try{
        setLoading(true);
        setApiError("");
        if (inFlight) return;
        inFlight = true;
        tick += 1;
        abort?.abort?.();
        abort = new AbortController();

        // Fast path (every 5s): minimal operational state to keep UI alive.
        const [state, confidence, cmdRes, stabilityRes] = await Promise.all([
          getSystemState({ signal: abort.signal }),
          getConfidence({ signal: abort.signal }),
          listCommands(50, { signal: abort.signal }),
          getStabilityHealth({ signal: abort.signal })
        ]);

        setSystemState(state || {});
        setConfidence(confidence || {});
        setCommands(cmdRes?.commands || []);
        setStabilityHealth(stabilityRes || {});

        // Slow path (every ~30s): heavy endpoints.
        if (tick % 6 === 0) {
          const [
            agentsRes, oppRes, expRes, reflRes, playbooksRes, analyticsRes,
            activityRes, trendRes, prodRes, kgRes, portRes, stratRes,
            kgInsightsRes, cogRes, researchRes
          ] = await Promise.all([
            listAgents(undefined, { signal: abort.signal }),
            listOpportunities({ signal: abort.signal }),
            listExperiments({ signal: abort.signal }),
            listReflections(50, { signal: abort.signal }),
            listPlaybooks({ signal: abort.signal }),
            getExperimentAnalytics(50, { signal: abort.signal }),
            getAgentActivity(200, { signal: abort.signal }),
            getConfidenceTrend(50, { signal: abort.signal }),
            getAgentProductivity(7, { signal: abort.signal }),
            getKnowledgeGraphSummary({ signal: abort.signal }),
            getPortfolioHealth({ signal: abort.signal }),
            getCurrentStrategy({ signal: abort.signal }),
            getKnowledgeInsights({ signal: abort.signal }),
            getCognitiveLast({ signal: abort.signal }),
            getResearchLast({ signal: abort.signal })
          ]);

          setAgents(agentsRes?.agents || []);
          setOpportunities(oppRes?.proposals || []);
          setExperiments(expRes?.experiments || []);
          setReflections(reflRes?.reflections || []);
          setPlaybooks(playbooksRes?.playbooks || {});
          setExperimentAnalytics(analyticsRes || {});
          setAgentActivity(activityRes?.events || []);
          setConfidenceTrend(trendRes?.points || []);
          setAgentProductivity(prodRes?.agents || []);
          setKnowledgeGraph(kgRes || {});
          setPortfolioHealth(portRes || {});
          setCurrentStrategy(stratRes || {});
          setKnowledgeInsights(kgInsightsRes || {});
          setCognitiveLast(cogRes || {});
          setResearchLast(researchRes || {});
        }

      }
      catch(e){

        console.error("Nova load failed",e);
        setApiError("Unable to load admin data. Check backend connectivity and token.");

      }
      finally{
        inFlight = false;
        setLoading(false);
        setInitialized(true);
      }

    }

    load();

    const timer = setInterval(load,5000);

    return ()=>{
      abort?.abort?.();
      clearInterval(timer);
    };

  },[]);
}
