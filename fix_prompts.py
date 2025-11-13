#!/usr/bin/env python3
"""
Script per correggere i caratteri corrotti nei prompts.
Esegui: python fix_prompts_encoding.py
"""

import re

def fix_prompts_encoding():
    # Leggi file
    with open('prompts.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Mappatura caratteri corrotti → corretti
    replacements = {
        'Ã¢Å"â€¦': '✅',
        'Ã¢â€ â€™': '→',
        'ÃƒÂ¢Ã…â€œÃ¢â‚¬Â¦': '✅',
        'ÃƒÂ¢Ã¢â‚¬Å"Ã…Â¡': '🚀',
        'ÃƒÂ¢Ã‚Â¢Ã¢â€šÂ¬Ã…â„¢': '✓',
        "Ã¢ÂÅ'": '❌',
        'Ã¢Å¡': '⚠️',
        'ÃƒÂ¢Ã…Â¡ ÃƒÂ¯Ã‚Â¸': '⚠️',
        'Ã¢Å"': '✓',
        'â³': '⏳',
        'ðŸ"„': '🔄',
        'âœ…': '✅',
        'â"': '❓',
        'ðŸ"§': '🔧',
        'ðŸš€': '🚀',
        'Ã¢â€Å"Ã¢â€â‚¬': '→',
        'Ã¢ÂÂÃ¢â€â‚¬': '→',
        'Ã¢Ââ€Ã¢â€â‚¬': '→',
    }
    
    # Applica sostituzioni
    for corrupted, correct in replacements.items():
        content = content.replace(corrupted, correct)
    
    # Salva file corretto
    with open('prompts.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ File prompts.py corretto!")
    print("   - Caratteri corrotti sostituiti con emoji corretti")
    print("   - File salvato con encoding UTF-8")

if __name__ == "__main__":
    fix_prompts_encoding()