import { useEffect } from "react";
import { fetchAgents } from "../services/novaApi";
import { useNovaStore } from "../state/novaStore";

export default function useAgents() {
  const setAgents = useNovaStore((s) => s.setAgents);

  useEffect(() => {
    async function load() {
      const data = await fetchAgents();
      setAgents(data);
    }

    load();
  }, []);
}