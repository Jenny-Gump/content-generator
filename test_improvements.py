#!/usr/bin/env python3
"""
Тестирование улучшений системы очистки данных на существующем dataset.
"""

import json
import sys
import os
from pathlib import Path

# Добавляем путь к src для импорта модулей
sys.path.append(str(Path(__file__).parent / "src"))

from processing import clean_content

def test_cleaning_improvements():
    """
    Тестирует улучшения очистки на данных из существующего запуска.
    """
    test_data_path = "output/Best_prompts_for_create_ideas_for_video/02_parsing/03_valid_sources.json"
    
    if not os.path.exists(test_data_path):
        print(f"❌ Test data not found: {test_data_path}")
        return
    
    print("🧪 Testing content cleaning improvements...")
    print("="*60)
    
    # Загружаем тестовые данные
    with open(test_data_path, 'r', encoding='utf-8') as f:
        test_sources = json.load(f)
    
    # Берем первые 3 источника для теста
    test_sources = test_sources[:3]
    
    print(f"📊 Testing on {len(test_sources)} sources:\n")
    
    # Применяем улучшенную очистку
    cleaned_sources = clean_content(test_sources)
    
    # Анализируем результаты
    total_original = 0
    total_cleaned = 0
    
    print("\n📈 Results Summary:")
    print("-" * 40)
    
    for i, source in enumerate(cleaned_sources, 1):
        url = source['url']
        original_len = source['original_length']
        cleaned_len = source['cleaned_length'] 
        reduction = source['reduction_percent']
        
        total_original += original_len
        total_cleaned += cleaned_len
        
        print(f"{i}. {url[:60]}...")
        print(f"   📏 Original: {original_len:,} chars")
        print(f"   ✂️  Cleaned:  {cleaned_len:,} chars")
        print(f"   📉 Reduction: {reduction:.1f}%\n")
    
    overall_reduction = ((total_original - total_cleaned) / total_original * 100) if total_original > 0 else 0
    
    print("🎯 Overall Results:")
    print(f"   Total original: {total_original:,} chars")
    print(f"   Total cleaned:  {total_cleaned:,} chars")
    print(f"   Overall reduction: {overall_reduction:.1f}%")
    
    # Сравнение с предыдущими результатами
    old_results_path = "output/Best_prompts_for_create_ideas_for_video/05_cleaning/final_cleaned_sources.json"
    if os.path.exists(old_results_path):
        with open(old_results_path, 'r', encoding='utf-8') as f:
            old_sources = json.load(f)
        
        # Найдем соответствующие источники по URL
        old_total_cleaned = 0
        matches = 0
        
        for new_source in cleaned_sources:
            for old_source in old_sources:
                if new_source['url'] == old_source['url']:
                    old_total_cleaned += len(old_source['cleaned_content'])
                    matches += 1
                    break
        
        if matches > 0:
            old_reduction = ((total_original - old_total_cleaned) / total_original * 100) if total_original > 0 else 0
            improvement = overall_reduction - old_reduction
            
            print(f"\n🔄 Comparison with previous cleaning:")
            print(f"   Previous reduction: {old_reduction:.1f}%")
            print(f"   New reduction:      {overall_reduction:.1f}%")
            print(f"   Improvement:        {improvement:+.1f} percentage points")

if __name__ == "__main__":
    test_cleaning_improvements()