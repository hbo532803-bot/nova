from backend.memory.goal_memory import primary_goal
from backend.memory.reflection_memory import ReflectionMemory


class MemoryBridge:

    def __init__(self):

        self.reflections = ReflectionMemory()

    def current_goal(self):

        g = primary_goal()

        if not g:
            return None

        return g["goal"]

    def record_result(self, data):

        self.reflections.record_reflection(data)