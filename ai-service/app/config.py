"""
Configuration management for MedAssist AI Service
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    app_name: str = "MedAssist AI Service"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # AI Model
    model_name: str = "llama-3.3-70b-versatile"  # Groq model name
    model_cache_dir: str = "./models_cache"
    use_gpu: bool = True
    max_tokens: int = 512
    temperature: float = 0.7
    huggingface_token: Optional[str] = None
    groq_api_key: Optional[str] = None  # Groq API key for Llama inference
    use_llm: bool = True  # Set to True to enable LLM via Groq, False for rule-based fallback
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    conversation_expiry_seconds: int = 3600
    
    # MongoDB
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "medassist"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/ai-service.log"
    
    # Safety
    enable_safety_checks: bool = True
    require_human_review_threshold: int = 7
    log_audit_trail: bool = True
    
    # Azure Document Intelligence
    azure_document_intelligence_endpoint: Optional[str] = None
    azure_document_intelligence_key: Optional[str] = None
    
    # Azure AI Translator
    azure_translator_endpoint: Optional[str] = None
    azure_translator_key: Optional[str] = None
    azure_translator_region: str = "southafricanorth"
    
    # Backend Integration
    backend_api_url: str = "http://localhost:8080"
    backend_api_key: Optional[str] = None
    
    # Azure AI Services
    azure_document_intelligence_endpoint: Optional[str] = None
    azure_document_intelligence_key: Optional[str] = None
    azure_translator_endpoint: Optional[str] = None
    azure_translator_key: Optional[str] = None
    azure_translator_region: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        protected_namespaces=()
    )


# Global settings instance
settings = Settings()
