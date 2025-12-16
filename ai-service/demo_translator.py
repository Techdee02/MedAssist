"""
MedAssist Multi-Language Translator Demo

Demonstrates Azure AI Translator integration for Nigerian healthcare.

Features:
- Yoruba, Hausa, Igbo (via Azure)
- Nigerian Pidgin (mock fallback)
- Medical terminology preservation
- Batch translation
"""

from app.services.language_translator import get_language_translator


def demo_basic_translation():
    """Basic translation examples"""
    print("=" * 70)
    print("🌍 BASIC TRANSLATION DEMO")
    print("=" * 70)
    
    translator = get_language_translator()
    
    # Test cases
    cases = [
        ("Hello, how are you?", "yo", "Yoruba"),
        ("I have a fever", "ha", "Hausa"),
        ("Where is the doctor?", "ig", "Igbo"),
        ("Take this medicine", "pcm", "Pidgin (mock)"),
    ]
    
    for english, target, name in cases:
        result = translator.translate(english, target, "en")
        indicator = "🔷 AZURE" if not result.get("mock") else "🔶 MOCK"
        print(f"\n{indicator} {name}:")
        print(f"  EN: {english}")
        print(f"  {target.upper()}: {result['translated_text']}")
        print(f"  Confidence: {result.get('confidence', 0):.2f}")


def demo_medical_terminology():
    """Medical term preservation"""
    print("\n" + "=" * 70)
    print("💊 MEDICAL TERMINOLOGY DEMO")
    print("=" * 70)
    
    translator = get_language_translator()
    
    medical_phrases = [
        "I have malaria and need paracetamol",
        "My blood pressure is high",
        "I tested positive for typhoid fever"
    ]
    
    for phrase in medical_phrases:
        result = translator.translate(phrase, "yo", "en")
        print(f"\n✚ Medical Case:")
        print(f"  English: {phrase}")
        print(f"  Yoruba: {result['translated_text']}")


def demo_batch_translation():
    """Batch translation for efficiency"""
    print("\n" + "=" * 70)
    print("📋 BATCH TRANSLATION DEMO")
    print("=" * 70)
    
    translator = get_language_translator()
    
    symptoms = [
        "I have a headache",
        "My stomach hurts",
        "I feel dizzy",
        "I have a cough"
    ]
    
    print("\nTranslating 4 symptoms to Hausa...")
    results = translator.translate_batch(symptoms, "ha", "en")
    
    for i, (orig, result) in enumerate(zip(symptoms, results), 1):
        print(f"\n{i}. {orig}")
        print(f"   → {result['translated_text']}")


def demo_language_detection():
    """Automatic language detection"""
    print("\n" + "=" * 70)
    print("🔍 LANGUAGE DETECTION DEMO")
    print("=" * 70)
    
    translator = get_language_translator()
    
    phrases = [
        "Báwo ni o ṣe wa?",  # Yoruba
        "Sannu, yaya lafiya?",  # Hausa
        "Kedu ka i mere?",  # Igbo
        "How you dey?",  # Pidgin
        "Hello doctor"  # English
    ]
    
    print("\nDetecting languages...")
    for phrase in phrases:
        result = translator.detect_language(phrase)
        lang_name = {
            "yo": "Yoruba",
            "ha": "Hausa",
            "ig": "Igbo",
            "pcm": "Pidgin",
            "en": "English"
        }.get(result["language"], "Unknown")
        
        print(f"\n'{phrase}'")
        print(f"  → Detected: {lang_name} ({result['language']})")
        print(f"  → Confidence: {result['confidence']:.2f}")


def demo_conversation_flow():
    """Realistic patient conversation"""
    print("\n" + "=" * 70)
    print("💬 PATIENT CONVERSATION DEMO")
    print("=" * 70)
    
    translator = get_language_translator()
    
    conversation = [
        ("Doctor: Hello, what brings you here today?", "yo"),
        ("Patient response in Yoruba", "en"),
        ("Doctor: How long have you had these symptoms?", "ha"),
        ("Doctor: I will prescribe medication for you", "ig"),
    ]
    
    print("\nMulti-language consultation:")
    for message, target in conversation:
        result = translator.translate(message, target, "en")
        lang_name = {
            "yo": "Yoruba",
            "ha": "Hausa", 
            "ig": "Igbo",
            "en": "English"
        }.get(target, target)
        
        print(f"\n🗣️  {message}")
        print(f"   [{lang_name}] → {result['translated_text']}")


def demo_convenience_methods():
    """Convenience translation helpers"""
    print("\n" + "=" * 70)
    print("⚡ CONVENIENCE METHODS DEMO")
    print("=" * 70)
    
    translator = get_language_translator()
    
    # Quick English translation
    pidgin = "I dey feel pain for body"
    english = translator.translate_to_english(pidgin)
    print(f"\n🔄 Quick to English:")
    print(f"   '{pidgin}' → '{english}'")
    
    # Quick from English
    english_phrase = "Thank you for your help"
    yoruba = translator.translate_from_english(english_phrase, "yo")
    hausa = translator.translate_from_english(english_phrase, "ha")
    igbo = translator.translate_from_english(english_phrase, "ig")
    
    print(f"\n🔄 Quick from English:")
    print(f"   EN: {english_phrase}")
    print(f"   YO: {yoruba}")
    print(f"   HA: {hausa}")
    print(f"   IG: {igbo}")


def main():
    """Run all demos"""
    print("\n" + "🏥" * 35)
    print("  MedAssist Multi-Language Translation System")
    print("  Supporting Nigerian Healthcare Communication")
    print("🏥" * 35 + "\n")
    
    try:
        demo_basic_translation()
        demo_medical_terminology()
        demo_batch_translation()
        demo_language_detection()
        demo_conversation_flow()
        demo_convenience_methods()
        
        print("\n" + "=" * 70)
        print("✅ All demos completed successfully!")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
