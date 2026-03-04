from config.env import env
    
GEMINI_API_KEY = env.str("GEMINI_API_KEY", default="")
EMBEDDING_PROVIDER = env.str("EMBEDDING_PROVIDER", default="gemini")
PGVECTOR_ENABLED = env.bool("PGVECTOR_ENABLED", default=True)