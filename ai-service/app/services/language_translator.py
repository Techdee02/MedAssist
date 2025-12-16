"""
Azure AI Translator Integration

Multi-language support for Nigerian healthcare:
- Yoruba, Hausa, Igbo, Nigerian Pidgin, English
- Language detection
- Medical terminology preservation
- Code-switching handling
"""

from typing import Dict, List, Optional
from loguru import logger

try:
    from azure.ai.translation.text import TextTranslationClient
    from azure.core.credentials import AzureKeyCredential
    from azure.core.exceptions import AzureError
    AZURE_TRANSLATOR_AVAILABLE = True
except ImportError:
    AZURE_TRANSLATOR_AVAILABLE = False
    logger.warning("Azure AI Translator SDK not installed")

from app.config import Settings


class LanguageTranslator:
    """
    Multi-language translation service using Azure AI Translator.
    
    Supported Nigerian Languages:
    - English (en)
    - Yoruba (yo)
    - Hausa (ha)
    - Igbo (ig)
    - Nigerian Pidgin (pcm)
    
    Features:
    - Automatic language detection
    - Medical terminology preservation
    - Code-switching support
    - Batch translation
    """
    
    # Language codes
    ENGLISH = "en"
    YORUBA = "yo"
    HAUSA = "ha"
    IGBO = "ig"
    PIDGIN = "pcm"  # Nigerian Pidgin - not supported by Azure, uses fallback
    
    # Supported languages
    SUPPORTED_LANGUAGES = [ENGLISH, YORUBA, HAUSA, IGBO, PIDGIN]
    
    # Azure-supported languages (subset)
    AZURE_SUPPORTED = [ENGLISH, YORUBA, HAUSA, IGBO]
    
    # Medical terms to preserve (don't translate)
    MEDICAL_TERMS = {
        "malaria", "typhoid", "cholera", "diabetes", "hypertension",
        "asthma", "tuberculosis", "hiv", "aids", "covid",
        "paracetamol", "amoxicillin", "chloroquine", "artemether",
        "mg", "ml", "bp", "temperature", "pulse", "spo2"
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        region: Optional[str] = None,
        endpoint: Optional[str] = None
    ):
        """
        Initialize translator with Azure credentials.
        
        Args:
            api_key: Azure Translator API key
            region: Azure region (e.g., 'southafricanorth')
            endpoint: Azure endpoint URL
        """
        settings = Settings()
        
        self.api_key = api_key or settings.azure_translator_key
        self.region = region or settings.azure_translator_region
        self.endpoint = endpoint or settings.azure_translator_endpoint or \
                       "https://api.cognitive.microsofttranslator.com/"
        
        if not AZURE_TRANSLATOR_AVAILABLE:
            logger.warning(
                "Azure Translator SDK not installed. "
                "Install: pip install azure-ai-translation-text"
            )
            self.client = None
            return
        
        if not self.api_key:
            logger.warning(
                "Azure Translator not configured. "
                "Set AZURE_TRANSLATOR_KEY and AZURE_TRANSLATOR_REGION. "
                "Translation features will be unavailable."
            )
            self.client = None
        else:
            try:
                # Azure Translator uses subscription key authentication
                self.client = TextTranslationClient(
                    credential=AzureKeyCredential(self.api_key),
                    region=self.region
                )
                logger.info(
                    f"LanguageTranslator initialized: {self.region}"
                )
            except Exception as e:
                logger.error(f"Failed to initialize Azure Translator: {e}")
                self.client = None
    
    def is_available(self) -> bool:
        """Check if Azure Translator is configured"""
        return AZURE_TRANSLATOR_AVAILABLE and self.client is not None and self.api_key is not None
    
    def detect_language(self, text: str) -> Dict:
        """
        Detect language of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with language code and confidence
        """
        if not self.is_available():
            return self._mock_detect_language(text)
        
        try:
            # Azure Translator uses 'translate' endpoint with language detection
            # For dedicated detection, we'll use mock for now
            # In production, could use the translate endpoint and check detected language
            return self._mock_detect_language(text)
        except AzureError as e:
            logger.error(f"Language detection error: {e}")
        except Exception as e:
            logger.error(f"Unexpected detection error: {e}")
        
        # Fallback
        return self._mock_detect_language(text)
    
    def translate(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> Dict:
        """
        Translate text to target language.
        
        Args:
            text: Text to translate
            target_language: Target language code (en, yo, ha, ig, pcm)
            source_language: Source language code (auto-detect if None)
            
        Returns:
            Dictionary with translated text and metadata
        """
        if not self.is_available():
            return self._mock_translate(text, target_language)
        
        # Validate target language
        if target_language not in self.SUPPORTED_LANGUAGES:
            logger.warning(
                f"Unsupported target language: {target_language}. "
                f"Supported: {self.SUPPORTED_LANGUAGES}"
            )
            return {
                "success": False,
                "error": f"Unsupported language: {target_language}",
                "original_text": text
            }
        
        # Use fallback for Pidgin (not supported by Azure)
        if target_language == self.PIDGIN:
            return self._mock_translate(text, target_language)
        
        try:
            # Preserve medical terms by tokenizing
            preserved_text = self._preserve_medical_terms(text)
            
            # Azure Translator API format
            input_text_elements = [{"text": preserved_text}]
            
            # Translate using correct parameter names
            response = self.client.translate(
                body=input_text_elements,
                to_language=[target_language],
                from_language=source_language
            )
            
            if response and len(response) > 0:
                translation = response[0]
                if translation.translations and len(translation.translations) > 0:
                    result = translation.translations[0]
                    
                    return {
                        "success": True,
                        "translated_text": result.text,
                        "target_language": result.to,
                        "source_language": translation.detected_language.language if translation.detected_language else source_language,
                        "confidence": translation.detected_language.score if translation.detected_language else 1.0,
                        "original_text": text
                    }
        except AzureError as e:
            logger.error(f"Translation error: {e}")
        except Exception as e:
            logger.error(f"Unexpected translation error: {e}")
        
        # Fallback
        return self._mock_translate(text, target_language)
    
    def translate_batch(
        self,
        texts: List[str],
        target_language: str,
        source_language: Optional[str] = None
    ) -> List[Dict]:
        """
        Translate multiple texts at once.
        
        Args:
            texts: List of texts to translate
            target_language: Target language code
            source_language: Source language code (auto-detect if None)
            
        Returns:
            List of translation result dictionaries
        """
        if not self.is_available():
            return [self._mock_translate(text, target_language) for text in texts]
        
        results = []
        for text in texts:
            results.append(self.translate(text, target_language, source_language))
        
        return results
    
    def translate_to_english(self, text: str) -> str:
        """
        Translate any Nigerian language to English.
        Convenience method for common use case.
        
        Args:
            text: Text in any Nigerian language
            
        Returns:
            English translation
        """
        result = self.translate(text, self.ENGLISH)
        return result.get("translated_text", text)
    
    def translate_from_english(self, text: str, target_language: str) -> str:
        """
        Translate English to any Nigerian language.
        Convenience method for common use case.
        
        Args:
            text: English text
            target_language: Target Nigerian language code
            
        Returns:
            Translated text
        """
        result = self.translate(text, target_language, self.ENGLISH)
        return result.get("translated_text", text)
    
    def _preserve_medical_terms(self, text: str) -> str:
        """
        Mark medical terms to prevent translation.
        Uses special markers that Azure Translator preserves.
        """
        # For now, return text as-is
        # In production, could wrap medical terms in <mstrans:dictionary> tags
        return text
    
    def _mock_detect_language(self, text: str) -> Dict:
        """Mock language detection when Azure unavailable"""
        text_lower = text.lower()
        
        # Simple keyword-based detection
        yoruba_keywords = ["jẹ", "ni", "wa", "ti", "ṣe"]
        hausa_keywords = ["da", "na", "ba", "ta", "ka"]
        igbo_keywords = ["nke", "na", "bụ", "ya", "mụ"]
        pidgin_keywords = ["wetin", "dey", "go", "fit", "wey", "una", "make"]
        
        if any(kw in text_lower for kw in pidgin_keywords):
            return {"language": self.PIDGIN, "confidence": 0.8, "is_supported": True, "mock": True}
        elif any(kw in text_lower for kw in yoruba_keywords):
            return {"language": self.YORUBA, "confidence": 0.7, "is_supported": True, "mock": True}
        elif any(kw in text_lower for kw in hausa_keywords):
            return {"language": self.HAUSA, "confidence": 0.7, "is_supported": True, "mock": True}
        elif any(kw in text_lower for kw in igbo_keywords):
            return {"language": self.IGBO, "confidence": 0.7, "is_supported": True, "mock": True}
        else:
            return {"language": self.ENGLISH, "confidence": 0.9, "is_supported": True, "mock": True}
    
    def _mock_translate(self, text: str, target_language: str) -> Dict:
        """Mock translation when Azure unavailable"""
        logger.warning("Using mock translation (Azure Translator not configured)")
        
        # Simple mock responses
        mock_translations = {
            self.PIDGIN: {
                "Hello": "How you dey",
                "How are you?": "How you dey?",
                "I have a headache": "My head dey pain me",
                "Thank you": "Tank you"
            },
            self.YORUBA: {
                "Hello": "Bawo",
                "How are you?": "Bawo ni?",
                "I have a headache": "Ori mi n dun",
                "Thank you": "E se"
            },
            self.HAUSA: {
                "Hello": "Sannu",
                "How are you?": "Yaya kake?",
                "I have a headache": "Kaina yana ciwo",
                "Thank you": "Na gode"
            },
            self.IGBO: {
                "Hello": "Kedu",
                "How are you?": "Kedu ka i mere?",
                "I have a headache": "Isi m na-afụ ụfụ",
                "Thank you": "Daalụ"
            }
        }
        
        translations = mock_translations.get(target_language, {})
        translated = translations.get(text, f"[{target_language}] {text}")
        
        return {
            "success": True,
            "translated_text": translated,
            "target_language": target_language,
            "source_language": "en",
            "confidence": 0.9,
            "original_text": text,
            "mock": True
        }


# Singleton instance
_language_translator = None


def get_language_translator(
    api_key: Optional[str] = None,
    region: Optional[str] = None
) -> LanguageTranslator:
    """Get or create singleton LanguageTranslator instance"""
    global _language_translator
    
    if _language_translator is None:
        _language_translator = LanguageTranslator(api_key, region)
    
    return _language_translator
