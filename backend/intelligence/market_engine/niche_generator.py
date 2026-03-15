import random


class DynamicNicheGenerator:

    def __init__(self):

        self.seed_keywords = [
            "AI",
            "Automation",
            "Sales",
            "Healthcare",
            "Real Estate",
            "Ecommerce",
            "Lead Generation",
            "Chatbot",
            "Content",
            "Marketing"
        ]

    def generate_niches(self, top_k=8):

        keywords = list(set(self.seed_keywords))

        random.shuffle(keywords)

        niches = []

        for i in range(len(keywords)):

            for j in range(i + 1, len(keywords)):

                niche = f"{keywords[i]} {keywords[j]}"

                niches.append(niche)

        random.shuffle(niches)

        return niches[:top_k]