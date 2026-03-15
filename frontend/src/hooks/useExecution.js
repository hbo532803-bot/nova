import { useEffect } from "react";
import { getExecutionPlan } from "../services/executionApi";
import { useExecutionStore } from "../state/executionStore";

export default function useExecution(id) {
  const setPlan = useExecutionStore((s) => s.setPlan);

  useEffect(() => {
    async function load() {
      const data = await getExecutionPlan(id);
      setPlan(data);
    }

    if (id) load();
  }, [id]);
}