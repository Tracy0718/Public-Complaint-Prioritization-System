import re
from pathlib import Path
from typing import Optional
import joblib

_model = None
_vectorizer = None

MODEL_FILE = Path(__file__).parent / 'model.joblib'
VECT_FILE = Path(__file__).parent / 'vectorizer.joblib'

# Ordered keyword-category mapping (more specific / severe first)
KEYWORD_CATEGORY_MAP = [
    # Life / safety critical first
    (['building collapse', 'wall collapse', 'structure collapse', 'collapsed building', 'cracks in building'], 'Construction / Structural'),
    (['flood', 'flooding', 'waterlogging', 'water logging', 'street flooded', 'area flooded'], 'Flooding'),
    # Sewage / drainage
    (['sewer', 'sewage', 'drain', 'drainage', 'blocked drain', 'clogged drain', 'sewerage',
      'manhole', 'manhole overflow', 'sewage overflow', 'overflowing drain'], 'Sewage / Drainage'),
    # Water supply
    (['water supply', 'no water', 'tap dry', 'no drinking water', 'water cut',
      'pipeline burst', 'water pipe burst', 'water pipeline', 'water leak', 'pipe leak'], 'Water Supply'),
    # Road / transport infrastructure
    (['road', 'pothole', 'potholes', 'road damage', 'crater', 'sinkhole', 'broken road',
      'damaged road', 'uneven road'], 'Road Damage'),
    # Garbage / sanitation
    (['garbage', 'trash', 'waste', 'dumping', 'rubbish', 'litter',
      'dustbin', 'bin overflowing', 'waste heap'], 'Garbage / Sanitation'),
    # Street lighting / power
    (['street light', 'streetlight', 'lamp post', 'light not working', 'no street light',
      'dark street', 'electricity outage', 'power cut', 'power outage'], 'Street Light'),
    # Noise / public nuisance
    (['noise', 'loud', 'music at night', 'nuisance', 'loudspeaker', 'loud speaker',
      'honking', 'horn'], 'Noise'),
    # Traffic / signals
    (['traffic', 'signals', 'signal', 'signal not working', 'congestion', 'jam',
      'traffic jam'], 'Traffic'),
    # Trees / vegetation
    (['tree', 'fallen tree', 'branches', 'tree fall', 'tree blocking', 'tree leaning'], 'Tree / Vegetation'),
]


# Keyword groups with weights for priority detection
_PRIORITY_KEYWORDS = {
    100: [  # CRITICAL
        "fire",
        "explosion",
        "electrocution",
        "building collapse",
        "bridge crack",
        "gas leak",
        "short circuit",
        "chemical leak",
        "major accident",
        "road accident",
        "accident",
        "live electric wire",
    ],
    75: [   # HIGH
        "open manhole",
        "broken electric pole",
        "flooding",
        "danger",
        "hazard",
        "water logging",
        "traffic signal not working",
    ],
    50: [   # MEDIUM
        "water leakage",
        "sewage blockage",
        "large pothole",
        "garbage pile",
        "street light not working",
        "drainage issue",
    ],
    25: [   # LOW
        "cleaning issue",
        "maintenance",
        "painting",
        "slow service",
        "minor repair",
    ],
}


def _load_model_and_vectorizer():
    global _model, _vectorizer
    if _model is None and MODEL_FILE.exists():
        try:
            _model = joblib.load(MODEL_FILE)
        except Exception:
            _model = None
    if _vectorizer is None and VECT_FILE.exists():
        try:
            _vectorizer = joblib.load(VECT_FILE)
        except Exception:
            _vectorizer = None


def _keyword_category(text):
    t = text.lower()
    for keywords, cat in KEYWORD_CATEGORY_MAP:
        for kw in keywords:
            if kw in t:
                return cat
    return None


def _model_predict(text):
    _load_model_and_vectorizer()
    if _model is None or _vectorizer is None:
        return None
    X = _vectorizer.transform([text])
    try:
        pred = _model.predict(X)
        return pred[0]
    except Exception:
        return None


def _normalise_text(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _contains_keyword(text: str, keyword: str) -> bool:
    """
    Safe partial matching:
    - Multi-word phrases: simple substring.
    - Single words: word-boundary regex to avoid 'fire' in 'fireworks'.
    """
    kw = keyword.lower()
    if " " in kw:
        return kw in text
    pattern = r"\b" + re.escape(kw) + r"\b"
    return re.search(pattern, text) is not None


def _score_text(text: str) -> Optional[int]:
    """
    Return the highest matching keyword score for the text.
    We do not sum scores; we care only about maximum severity present.
    """
    best: Optional[int] = None
    for score, keywords in _PRIORITY_KEYWORDS.items():
        for kw in keywords:
            if _contains_keyword(text, kw):
                if best is None or score > best:
                    best = score
    return best


def detect_priority(description: str) -> str:
    """
    Determine priority for a complaint description using weighted keyword scoring.

    Rules:
    - Normalise text and remove punctuation before matching.
    - Use the highest matching keyword score (no summation).
    - Mapping:
        score >= 90  -> Critical
        score >= 70  -> High
        score >= 40  -> Medium
        else         -> Low
    - If no keyword matches -> Medium (balanced default, never High).
    - If description has < 5 words -> Low.
    - If both critical and low words appear, Critical wins via max-score logic.
    """
    if not description:
        return "Low"

    text = _normalise_text(description)
    if not text:
        return "Low"

    # Edge case: very short descriptions are treated as low-severity noise.
    if len(text.split()) < 5:
        return "Low"

    best_score = _score_text(text)

    # No keyword matched -> default to Medium (not High)
    if best_score is None:
        return "Medium"

    if best_score >= 90:
        return "Critical"
    if best_score >= 70:
        return "High"
    if best_score >= 40:
        return "Medium"
    return "Low"


def predict_category_priority(text):
    """
    Predict (category, priority) for a complaint.
    Category uses rules + optional ML model.
    Priority uses weighted keyword scoring, independent of category.
    """
    if not text:
        return "Other", "Low"

    # Normalise whitespace for category / ML handling
    cleaned = re.sub(r"\s+", " ", text.strip())

    # Category: keywords first, ML fallback
    cat = _keyword_category(cleaned)
    if not cat:
        mcat = _model_predict(cleaned)
        if mcat:
            cat = mcat
    if not cat:
        cat = "Other"

    # Priority: use new scoring-based detector
    priority = detect_priority(cleaned)

    return cat, priority
