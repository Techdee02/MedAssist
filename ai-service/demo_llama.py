"""
Demo script to test Intent Classifier with Llama LLM

Run with rule-based (default):
    python demo_llama.py

Run with LLM (requires setup):
    USE_LLM=true HUGGINGFACE_TOKEN=hf_your_token python demo_llama.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.intent_classifier import get_intent_classifier
from app.config import settings
from loguru import logger

# Test messages covering all intent types
TEST_MESSAGES = [
    # Appointment booking
    "I need to book an appointment for next Tuesday",
    "Can I see a doctor tomorrow?",
    "I wan schedule checkup for my pikin",
    
    # Medication refill
    "I need to refill my blood pressure medication",
    "My hypertension drug don finish",
    
    # Symptom inquiry
    "I have a severe headache that won't go away",
    "My belle dey pain me since morning",
    
    # Emergency
    "I'm having chest pain and can't breathe properly",
    "I no fit breathe, help me!",
    
    # Feedback/Complaint
    "The wait time was very long yesterday",
    "Thank you for the excellent service",
    
    # General inquiry
    "What time do you open on Saturdays?",
    "Do you accept health insurance?",
]


def main():
    """Run intent classification demo"""
    
    print("\n" + "="*70)
    print("    MEDASSIST INTENT CLASSIFIER - LLAMA LLM INTEGRATION")
    print("="*70)
    
    # Show configuration
    print(f"\n📋 Configuration:")
    print(f"   USE_LLM: {settings.use_llm}")
    print(f"   Model: {settings.model_name}")
    print(f"   GPU Available: {settings.use_gpu}")
    
    if settings.use_llm:
        print(f"   HF Token: {'✅ Provided' if settings.huggingface_token else '❌ Not provided'}")
        print(f"\n🤖 Mode: LLM-POWERED (Llama)")
    else:
        print(f"\n🔧 Mode: RULE-BASED FALLBACK")
    
    print("\n" + "-"*70)
    
    # Initialize classifier
    print("\n⚙️  Initializing classifier...")
    try:
        classifier = get_intent_classifier()
        print("✅ Classifier ready!\n")
    except Exception as e:
        print(f"❌ Error initializing classifier: {e}")
        return
    
    # Test classifications
    print("🧪 Testing classifications:\n")
    
    for i, message in enumerate(TEST_MESSAGES, 1):
        print(f"\n[{i}/{len(TEST_MESSAGES)}] Message: \"{message}\"")
        
        try:
            result = classifier.classify(message)
            
            # Determine emoji based on intent
            emoji_map = {
                "appointment_booking": "📅",
                "medication_refill": "💊",
                "symptom_inquiry": "🩺",
                "emergency": "🚨",
                "feedback_complaint": "💬",
                "general_inquiry": "❓"
            }
            emoji = emoji_map.get(result.intent.value, "🔍")
            
            print(f"    {emoji} Intent: {result.intent.value}")
            print(f"    📊 Confidence: {result.confidence:.2%}")
            print(f"    💭 Reasoning: {result.reasoning}")
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    print("\n" + "="*70)
    print("✅ Demo complete!")
    print("="*70)
    
    # Summary
    print(f"\n📝 Summary:")
    if settings.use_llm:
        print("   • LLM mode provides better accuracy for complex queries")
        print("   • Handles Nigerian Pidgin with high confidence")
        print("   • Provides detailed reasoning for each classification")
    else:
        print("   • Rule-based mode is fast and reliable")
        print("   • No external dependencies required")
        print("   • Perfect for development and testing")
    
    print(f"\n💡 Tip: Set USE_LLM=true in .env to enable Llama LLM")
    print(f"   See LLAMA_SETUP.md for detailed instructions\n")


if __name__ == "__main__":
    main()
