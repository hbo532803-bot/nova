import { useEffect, useRef } from "react";
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
  const inFlightRef = useRef(false);
  const tickRef = useRef(0);
  const abortRef = useRef(null);
  const mountedRef = useRef(false);

  useEffect(()=>{
    mountedRef.current = true;

    async function load(){
      if (!mountedRef.current || inFlightRef.current) return;
      inFlightRef.current = true;
      tickRef.current += 1;

      try{
        if (!useNovaStore.getState().initialized) setLoading(true);
        setApiError("");
        abortRef.current?.abort?.();
        const controller = new AbortController();
        abortRef.current = controller;

        // Fast path (every 5s): minimal operational state to keep UI alive.
        const [state, confidence, cmdRes, stabilityRes] = await Promise.all([
          getSystemState({ signal: controller.signal }),
          getConfidence({ signal: controller.signal }),
          listCommands(50, { signal: controller.signal }),
          getStabilityHealth({ signal: controller.signal })
        ]);
        if (!mountedRef.current || controller.signal.aborted) return;

        setSystemState(state || {});
        setConfidence(confidence || {});
        setCommands(cmdRes?.commands || []);
        setStabilityHealth(stabilityRes || {});

        // Slow path (every ~30s): heavy endpoints.
        if (tickRef.current % 6 === 0) {
          const [
            agentsRes, oppRes, expRes, reflRes, playbooksRes, analyticsRes,
            activityRes, trendRes, prodRes, kgRes, portRes, stratRes,
            kgInsightsRes, cogRes, researchRes
          ] = await Promise.all([
            listAgents(undefined, { signal: controller.signal }),
            listOpportunities({ signal: controller.signal }),
            listExperiments({ signal: controller.signal }),
            listReflections(50, { signal: controller.signal }),
            listPlaybooks({ signal: controller.signal }),
            getExperimentAnalytics(50, { signal: controller.signal }),
            getAgentActivity(200, { signal: controller.signal }),
            getConfidenceTrend(50, { signal: controller.signal }),
            getAgentProductivity(7, { signal: controller.signal }),
            getKnowledgeGraphSummary({ signal: controller.signal }),
            getPortfolioHealth({ signal: controller.signal }),
            getCurrentStrategy({ signal: controller.signal }),
            getKnowledgeInsights({ signal: controller.signal }),
            getCognitiveLast({ signal: controller.signal }),
            getResearchLast({ signal: controller.signal })
          ]);
          if (!mountedRef.current || controller.signal.aborted) return;

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
        if (e?.name === "AbortError") return;
        console.error("Nova load failed",e);
        if (mountedRef.current) {
          setApiError("Unable to load admin data. Check backend connectivity and token.");
        }

      }
      finally{
        inFlightRef.current = false;
        if (mountedRef.current) {
          setLoading(false);
          setInitialized(true);
        }
      }

    }

    load();

    const timer = setInterval(load,5000);

    return ()=>{
      mountedRef.current = false;
      abortRef.current?.abort?.();
      clearInterval(timer);
    };

  },[setAgentActivity, setAgentProductivity, setAgents, setApiError, setCognitiveLast, setCommands, setConfidence, setConfidenceTrend, setCurrentStrategy, setExperimentAnalytics, setExperiments, setInitialized, setKnowledgeGraph, setKnowledgeInsights, setLoading, setOpportunities, setPlaybooks, setPortfolioHealth, setReflections, setResearchLast, setStabilityHealth, setSystemState]);
}
