from data_collector import MarketDataCollector

collector = MarketDataCollector()

test_niches = [
    "AI Sales Automation",
    "YouTube Shorts Editing",
    "Healthcare AI Admin",
    "Real Estate Lead Bots",
    "Ecommerce AI Chatbots"
]

collector.run_collection(test_niches)