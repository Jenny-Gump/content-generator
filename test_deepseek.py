#!/usr/bin/env python3
"""
Простой тест DeepSeek API для проверки работоспособности
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()  # Загружаем переменные из .env файла

from deepseek import DeepSeekAPI

def test_deepseek_api():
    print("🔍 Testing DeepSeek API...")
    
    client = DeepSeekAPI()
    
    # Простое тестовое сообщение
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say 'Hello, DeepSeek API is working!' and return it as JSON with key 'message'."}
    ]
    
    try:
        print("📤 Sending test request...")
        
        # Тест с deepseek-reasoner
        print("Testing deepseek-reasoner model...")
        response = client.chat_completion(
            model="deepseek-reasoner",
            messages=messages,
            max_tokens=100
        )
        
        print("✅ deepseek-reasoner response:")
        print(f"Response type: {type(response)}")
        print(f"Response length: {len(response) if response else 0}")
        print(f"Response: {response[:500]}...")
        print()
        
        # Тест с deepseek-chat для сравнения
        print("Testing deepseek-chat model...")
        response2 = client.chat_completion(
            model="deepseek-chat",
            messages=messages,
            max_tokens=100
        )
        
        print("✅ deepseek-chat response:")
        print(f"Response type: {type(response2)}")
        print(f"Response length: {len(response2) if response2 else 0}")
        print(f"Response: {response2[:500]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_deepseek_api()