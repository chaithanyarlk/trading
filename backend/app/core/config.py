import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings"""
    
    # Server
    APP_NAME = "AI Trading Assistant"
    APP_VERSION = "2.0.0"
    DEBUG = os.getenv("DEBUG", "False") == "True"
    
    # AI Configuration - Choose between "anthropic" or "ollama"
    AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama")  # or "anthropic"
    
    # Claude AI Configuration (for Anthropic)
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
    CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
    
    # Ollama Configuration (for local LLM)
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:latest")  # Default to Qwen
    
    # Groww API Configuration
    GROWW_API_KEY = os.getenv("GROWW_API_KEY", "")
    GROWW_API_SECRET = os.getenv("GROWW_API_SECRET", "")
    GROWW_API_BASE_URL = os.getenv("GROWW_API_BASE_URL", "https://api.groww.in")
    GROWW_AUTH_TOKEN = os.getenv("GROWW_AUTH_TOKEN", "")
    
    # Trading Configuration
    LIVE_TRADING_ENABLED = os.getenv("LIVE_TRADING_ENABLED", "False") == "True"
    PAPER_TRADING_INITIAL_CAPITAL = float(os.getenv("PAPER_TRADING_INITIAL_CAPITAL", "1000000"))
    MAX_POSITION_SIZE_PERCENT = float(os.getenv("MAX_POSITION_SIZE_PERCENT", "10"))
    STOP_LOSS_PERCENT = float(os.getenv("STOP_LOSS_PERCENT", "2"))
    
    # Analysis Configuration
    RSI_PERIOD = int(os.getenv("RSI_PERIOD", "14"))
    MACD_FAST = int(os.getenv("MACD_FAST", "12"))
    MACD_SLOW = int(os.getenv("MACD_SLOW", "26"))
    MACD_SIGNAL = int(os.getenv("MACD_SIGNAL", "9"))
    
    # Database (SQLite for now)
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./trading_system.db")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
settings = Settings()
