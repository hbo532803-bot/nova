import { useEffect } from "react";
import { fetchOpportunities } from "../services/novaApi";
import { useNovaStore } from "../state/novaStore";

export default function useOpportunities() {
  const setOpportunities = useNovaStore((s) => s.setOpportunities);

  useEffect(() => {
    async function load() {
      const data = await fetchOpportunities();
      setOpportunities(data);
    }

    load();
  }, []);
}