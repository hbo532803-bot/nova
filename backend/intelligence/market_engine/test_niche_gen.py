from niche_generator import DynamicNicheGenerator

gen = DynamicNicheGenerator()
niches = gen.generate_niches()

print("Generated Niches:")
for n in niches:
    print("-", n)