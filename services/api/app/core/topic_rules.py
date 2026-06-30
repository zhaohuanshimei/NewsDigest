"""Keyword rules for topic classification.

Each topic is associated with a list of keywords.  Keywords are matched
against lowercased article titles and summaries using word boundaries.

The topic with the most keyword matches wins.  If the winner has fewer
than MIN_MATCHES hits the article is classified as ``general``.
"""

from __future__ import annotations

# Minimum number of keyword matches required for a non-general classification.
# Topics have very different keyword-list sizes, so absolute count is more
# intuitive than a hit rate.
MIN_MATCHES = 2

TOPIC_RULES: dict[str, list[str]] = {
    "politics": [
        "congress", "senate", "parliament", "election", "bill", "lawmaker",
        "legislation", "governor", "mayor", "campaign", "vote", "voter",
        "ballot", "democrat", "republican", "gop", "senator", "representative",
        "president", "prime minister", "cabinet", "minister", "mp",
        "senate", "house of representatives", "assembly",
        "constitutional", "impeachment", "lobby", "lobbyist",
        "diplomatic", "embassy", "ambassador", "sanction",
        "government", "governing", "administration",
    ],
    "business": [
        "stock", "market", "nasdaq", "dow jones", "s&p 500", "bond",
        "merger", "acquisition", "ipo", "startup", "funding", "venture",
        "revenue", "profit", "earnings", "quarterly", "fiscal",
        "ceo", "cfo", "executive", "corporate", "board",
        "trade", "tariff", "import", "export", "supply chain",
        "inflation", "interest rate", "central bank", "fed", "federal reserve",
        "bankruptcy", "layoff", "unemployment", "economy", "economic",
        "investor", "shareholder", "dividend", "buyback",
        "real estate", "housing market", "mortgage",
    ],
    "tech": [
        "ai", "artificial intelligence", "machine learning", "llm", "gpt",
        "chatgpt", "openai", "google", "apple", "microsoft", "meta",
        "amazon", "tesla", "nvidia", "intel", "qualcomm", "amd",
        "software", "hardware", "chip", "semiconductor", "processor",
        "smartphone", "iphone", "android", "app", "application",
        "cloud", "aws", "azure", "database", "api",
        "cybersecurity", "hack", "breach", "ransomware", "malware",
        "algorithm", "robot", "automation", "autonomous",
        "electric vehicle", "ev", "battery", "renewable",
        "social media", "twitter", "facebook", "instagram", "tiktok",
        "cryptocurrency", "bitcoin", "ethereum", "blockchain", "nft",
        "startup", "venture capital", "silicon valley",
        "data", "privacy", "encryption", "surveillance",
        "5g", "network", "internet", "web", "browser",
        "gaming", "console", "playstation", "xbox", "nintendo",
    ],
    "science": [
        "research", "study", "scientist", "researcher", "laboratory",
        "discovery", "breakthrough", "space", "nasa", "esa",
        "mars", "moon", "planet", "telescope", "astronomy", "astronaut",
        "physics", "quantum", "particle", "cern", "nuclear",
        "biology", "genetics", "gene", "dna", "protein", "cell",
        "climate", "climate change", "global warming", "carbon",
        "emission", "fossil fuel", "renewable", "solar", "wind",
        "environment", "pollution", "conservation", "biodiversity",
        "species", "extinction", "ecosystem", "ocean", "arctic",
        "archaeology", "fossil", "dinosaur", "evolution",
        "neuroscience", "brain", "psychology", "cognitive",
    ],
    "world": [
        "war", "military", "army", "navy", "air force", "troop",
        "conflict", "invasion", "attack", "strike", "missile", "drone",
        "ceasefire", "truce", "peace", "treaty", "alliance", "allies",
        "nato", "defense", "defence",
        "united nations", "un", "refugee", "asylum", "migrant",
        "protest", "demonstration", "riot", "rebellion", "coup",
        "terror", "terrorism", "extremist", "insurgent",
        "border", "territory", "sovereignty", "occupation",
        "foreign", "international", "global", "diplomacy",
        "humanitarian", "aid", "relief", "crisis",
        "european union", "eu", "brexit", "china", "russia",
        "ukraine", "iran", "israel", "palestine", "africa",
        "asia", "latin america", "middle east",
    ],
    "health": [
        "covid", "coronavirus", "pandemic", "epidemic", "outbreak",
        "hospital", "doctor", "nurse", "patient", "medical",
        "disease", "cancer", "diabetes", "heart", "stroke",
        "symptom", "diagnosis", "therapy", "surgery",
        "mental health", "depression", "anxiety", "wellness",
        "nutrition", "diet", "exercise", "fitness",
        "drug", "fda", "approval", "prescription", "pharmaceutical",
        "vaccine", "vaccination", "immunization", "immunity",
        "healthcare", "health care", "clinical trial", "insurance", "medicare", "medicaid",
        "sleep", "aging", "senior", "elderly", "pandemic",
        "smoking", "alcohol", "substance", "opioid", "addiction",
        "pregnancy", "birth", "infant", "child health",
    ],
}
