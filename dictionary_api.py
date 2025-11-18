"""
Dictionary API - Lấy thông tin từ điển cho flashcard
Sử dụng Free Dictionary API: https://dictionaryapi.dev/
"""

import requests
import json
from typing import Dict, Optional, List

def get_word_info(word: str) -> Dict:
    """
    Lấy thông tin từ điển cho một từ tiếng Anh
    
    Returns:
        {
            'pronunciation': '/wɔːrd/',
            'part_of_speech': 'noun',
            'definitions': [...],
            'examples': [...],
            'synonyms': [...],
            'antonyms': [...],
            'audio': 'https://...'
        }
    """
    word = word.strip().lower()
    if not word:
        return {}
    
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                entry = data[0]  # Lấy entry đầu tiên
                
                # Lấy pronunciation
                pronunciation = ''
                if 'phonetics' in entry and len(entry['phonetics']) > 0:
                    for ph in entry['phonetics']:
                        if 'text' in ph:
                            pronunciation = ph['text']
                            break
                
                # Lấy audio
                audio_url = ''
                if 'phonetics' in entry:
                    for ph in entry['phonetics']:
                        if 'audio' in ph and ph['audio']:
                            audio_url = ph['audio']
                            break
                
                # Lấy meanings (definitions, examples, synonyms, antonyms)
                meanings = entry.get('meanings', [])
                definitions = []
                examples = []
                synonyms = []
                antonyms = []
                part_of_speech = ''
                
                for meaning in meanings:
                    # Lấy part of speech từ meaning đầu tiên
                    if not part_of_speech and 'partOfSpeech' in meaning:
                        part_of_speech = meaning['partOfSpeech']
                    
                    # Lấy definitions
                    if 'definitions' in meaning:
                        for def_item in meaning['definitions']:
                            if 'definition' in def_item:
                                definitions.append(def_item['definition'])
                            if 'example' in def_item:
                                examples.append(def_item['example'])
                    
                    # Lấy synonyms và antonyms
                    if 'synonyms' in meaning:
                        synonyms.extend(meaning['synonyms'])
                    if 'antonyms' in meaning:
                        antonyms.extend(meaning['antonyms'])
                
                # Lấy collocations (từ phrases)
                collocations = []
                for meaning in meanings:
                    if 'definitions' in meaning:
                        for def_item in meaning['definitions']:
                            if 'definition' in def_item:
                                # Tìm các cụm từ phổ biến trong definition
                                text = def_item['definition'].lower()
                                if word in text:
                                    # Tìm các cụm từ như "run out", "run into"
                                    words_around = text.split()
                                    if word in words_around:
                                        idx = words_around.index(word)
                                        if idx > 0:
                                            colloc = f"{words_around[idx-1]} {word}"
                                            if colloc not in collocations:
                                                collocations.append(colloc)
                                        if idx < len(words_around) - 1:
                                            colloc = f"{word} {words_around[idx+1]}"
                                            if colloc not in collocations:
                                                collocations.append(colloc)
                
                return {
                    'pronunciation': pronunciation,
                    'part_of_speech': part_of_speech,
                    'definitions': definitions[:3],  # Lấy 3 định nghĩa đầu
                    'examples': examples[:2],  # Lấy 2 ví dụ đầu
                    'synonyms': list(set(synonyms))[:5],  # Lấy 5 từ đồng nghĩa
                    'antonyms': list(set(antonyms))[:5],  # Lấy 5 từ trái nghĩa
                    'collocations': collocations[:5],  # Lấy 5 collocations
                    'audio': audio_url
                }
        
        return {}
    except Exception as e:
        print(f"⚠️  Error fetching dictionary info for '{word}': {e}")
        return {}

def get_collocations(word: str) -> List[str]:
    """Lấy collocations cho một từ"""
    info = get_word_info(word)
    return info.get('collocations', [])

def generate_ai_example(word: str, meaning: str = '', part_of_speech: str = '') -> str:
    """
    AI tự sinh ví dụ cho từ dựa trên từ, nghĩa và từ loại
    
    Args:
        word: Từ tiếng Anh
        meaning: Nghĩa tiếng Việt (optional)
        part_of_speech: Từ loại (noun, verb, adjective, etc.)
    
    Returns:
        Câu ví dụ tiếng Anh
    """
    word = word.strip()
    if not word:
        return ""
    
    word_lower = word.lower()
    part_of_speech = part_of_speech.lower() if part_of_speech else ''
    
    # Template ví dụ theo từ loại
    templates = {
        'verb': [
            f"I {word_lower} every day.",
            f"She {word_lower}s regularly.",
            f"They {word_lower} together.",
            f"We should {word_lower} more often.",
            f"He {word_lower}ed yesterday.",
            f"Please {word_lower} carefully.",
            f"I will {word_lower} tomorrow.",
            f"She can {word_lower} well."
        ],
        'noun': [
            f"The {word_lower} is important.",
            f"This {word_lower} helps me.",
            f"I need a {word_lower}.",
            f"The {word_lower} was useful.",
            f"Every {word_lower} matters.",
            f"Find the {word_lower}.",
            f"This {word_lower} is good.",
            f"The {word_lower} works well."
        ],
        'adjective': [
            f"This is very {word_lower}.",
            f"It's a {word_lower} solution.",
            f"She looks {word_lower}.",
            f"The {word_lower} approach works.",
            f"I feel {word_lower} today.",
            f"That's quite {word_lower}.",
            f"More {word_lower} than expected.",
            f"Really {word_lower} and helpful."
        ],
        'adverb': [
            f"She works {word_lower}.",
            f"Do it {word_lower}.",
            f"He speaks {word_lower}.",
            f"Move {word_lower} please.",
            f"Think {word_lower} about it.",
            f"Act {word_lower}.",
            f"React {word_lower}.",
            f"Respond {word_lower}."
        ]
    }
    
    # Xác định từ loại nếu chưa có
    if not part_of_speech:
        if word_lower.endswith(('ed', 'ing', 'ize', 'ise')):
            part_of_speech = 'verb'
        elif word_lower.endswith(('ly',)):
            part_of_speech = 'adverb'
        elif word_lower.endswith(('tion', 'sion', 'ness', 'ment', 'ity', 'er', 'or')):
            part_of_speech = 'noun'
        elif word_lower.endswith(('ful', 'less', 'ous', 'ive', 'al', 'ic')):
            part_of_speech = 'adjective'
        else:
            part_of_speech = 'noun'  # Default
    
    # Lấy template phù hợp
    if part_of_speech in templates:
        import random
        template = random.choice(templates[part_of_speech])
        
        # Xử lý số ít/số nhiều cho noun
        if part_of_speech == 'noun':
            # Nếu từ kết thúc bằng s, x, ch, sh, z -> thêm es
            if word_lower.endswith(('s', 'x', 'ch', 'sh', 'z')):
                plural = word_lower + 'es'
            # Nếu từ kết thúc bằng y và trước đó là phụ âm -> ies
            elif word_lower.endswith('y') and len(word_lower) > 1 and word_lower[-2] not in 'aeiou':
                plural = word_lower[:-1] + 'ies'
            else:
                plural = word_lower + 's'
            
            # Thay thế trong template
            template = template.replace(f'the {word_lower}', f'the {word}')
            template = template.replace(f'a {word_lower}', f'a {word}')
            template = template.replace(f'this {word_lower}', f'this {word}')
            template = template.replace(f'every {word_lower}', f'every {word}')
        else:
            # Giữ nguyên từ gốc cho verb, adjective, adverb
            template = template.replace(word_lower, word)
        
        return template.capitalize()
    
    # Fallback: tạo ví dụ đơn giản
    return f"I use {word} in my daily life.".capitalize()

if __name__ == '__main__':
    # Test
    word = "run"
    info = get_word_info(word)
    print(json.dumps(info, indent=2, ensure_ascii=False))

