import re
from fastapi import HTTPException

# Blacklist of vulgar, offensive, and prohibited base terms (Uzbek, Russian, English)
PROFANITY_WORDS = {
    # Uzbek
    "ahmoq", "tentak", "harom", "jalab", "jalap", "itvachcha", "qoxtaq", "qotoq", "kot",
    "am", "amchiq", "sik", "siktir", "sikiw", "sikish", "hezala", "shilta", "fohisha",
    "qanjiq", "padar", "iflos", "dalbayob", "dalbaeb", "gandon",
    
    # Russian
    "blya", "blyad", "suka", "nahui", "nahuy", "pidor", "pidoras", "pizda", "ebat",
    "ebaniy", "gandon", "zaebal", "mudak", "dermo", "khuy", "hui", "chmo", "shlyuha",
    "blat", "yebat", "sukin", "dolboyob", "huesos", "zalupa", "ebalo", "huylo",
    
    # English
    "fuck", "fucker", "fucking", "shit", "bitch", "asshole", "dick", "pussy",
    "bastard", "cunt", "whore", "slut", "motherfucker", "cock", "nigger", "nigga",
    "fag", "faggot", "retard", "dumbass", "bullshit", "prick", "twat"
}

# Common leet / obfuscation substitutions
LEET_TRANS = str.maketrans({
    "@": "a", "4": "a",
    "8": "b",
    "3": "e",
    "1": "i", "!": "i", "|": "i",
    "0": "o",
    "$": "s", "5": "s",
    "7": "t", "+": "t",
    "v": "u", "u": "u"
})

def contains_profanity(text: str) -> bool:
    if not text:
        return False
    
    lower_text = text.lower()
    
    # 1. Direct check on raw tokens and full phrase
    raw_clean = re.sub(r'[^a-z0-9а-яёўқғҳ]', '', lower_text)
    
    # 2. Leet translated clean
    leet_clean = lower_text.translate(LEET_TRANS)
    leet_clean = re.sub(r'[^a-z0-9а-яёўқғҳ]', '', leet_clean)
    
    # Also handle wildcard characters like f*ck, f!ck
    wildcard_clean = re.sub(r'[!*_\-.]', 'u', lower_text)
    wildcard_clean = re.sub(r'[^a-z0-9а-яёўқғҳ]', '', wildcard_clean)
    
    variants = [lower_text, raw_clean, leet_clean, wildcard_clean]
    
    # Check words separated by spaces or punctuation
    tokens = re.split(r'[^a-z0-9а-яёўқғҳ]+', lower_text)
    
    for bad in PROFANITY_WORDS:
        # Check tokens directly
        if bad in tokens:
            return True
        # Check substring in variants (only if length >= 3 to avoid false positives)
        if len(bad) >= 3:
            for variant in variants:
                if bad in variant:
                    return True
                    
    return False

def validate_name(name: str):
    if not name or len(name.strip()) < 2:
        raise HTTPException(
            status_code=400,
            detail="Ism kamida 2 ta belgidan iborat bo'lishi kerak / Name must be at least 2 characters."
        )
    if len(name.strip()) > 50:
        raise HTTPException(
            status_code=400,
            detail="Ism 50 ta belgidan oshmasligi kerak / Name must not exceed 50 characters."
        )
    if contains_profanity(name):
        raise HTTPException(
            status_code=400,
            detail="Kiritilgan ismda taqiqlangan yoki nomaqbul so'zlar aniqlandi! Iltimos, odobli ism kiriting. / Name contains inappropriate or offensive words!"
        )
