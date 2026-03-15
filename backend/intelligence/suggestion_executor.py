from backend.intelligence.system_settings import set_setting


class SuggestionExecutor:

    def apply(self, suggestions: list):

        applied = []

        for s in suggestions:

            action = s.get("action")

            if action == "Increase semantic similarity threshold":

                set_setting("semantic_threshold", "0.85")
                applied.append(action)

            elif action == "Enable recursive sub-planning":

                set_setting("recursive_planning", "enabled")
                applied.append(action)

            elif action == "Increase reasoning depth":

                set_setting("reasoning_depth", "3")
                applied.append(action)

        return applied