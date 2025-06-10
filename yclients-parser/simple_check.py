#!/usr/bin/env python3
import os

def check_files():
    print("🔍 Проверка готовности YCLIENTS Parser...")
    
    files = [
        "src/parser/improved_data_extractor.py",
        "src/parser/improved_selectors.py", 
        "docker-compose-timeweb.yml",
        "Dockerfile-timeweb",
        ".env.timeweb.example",
        "TIMEWEB_DEPLOYMENT_GUIDE.md"
    ]
    
    passed = 0
    for f in files:
        if os.path.exists(f):
            print(f"✅ {f}")
            passed += 1
        else:
            print(f"❌ {f}")
    
    # Проверка главного исправления
    try:
        with open("src/parser/yclients_parser.py", 'r') as file:
            if "ImprovedDataExtractor" in file.read():
                print("✅ ImprovedDataExtractor используется")
                passed += 1
            else:
                print("❌ ImprovedDataExtractor НЕ используется")
    except:
        print("❌ Ошибка чтения yclients_parser.py")
    
    print(f"\n📊 Результат: {passed}/{len(files)+1} ✅")
    
    if passed == len(files)+1:
        print("🎉 ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ!")
        return True
    else:
        print("⚠️ Некоторые исправления отсутствуют")
        return False

if __name__ == "__main__":
    success = check_files()
    exit(0 if success else 1)
