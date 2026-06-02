from pydantic import BaseModel
from typing import List, Optional

class TextRequest(BaseModel):
    text: str
    use_fuzzy: Optional[bool] = False  # Dinonaktifkan secara default untuk performa maksimal

class LexiconMatch(BaseModel):
    matched_phrase: str
    category: str
    severity: str
    method: str

class LexiconResponse(BaseModel):
    text: str
    normalized_spaced: str
    normalized_compact: str
    is_cyberbullying: bool
    risk_label: str
    score: int
    matches: List[LexiconMatch]

class MLResponse(BaseModel):
    text: str
    is_toxic: bool
    is_bully: bool
    probability_toxic: float
    probability_bully: float
    category: str

class TransformerResponse(BaseModel):
    text: str
    is_toxic: bool
    is_bully: bool
    probability_toxic: float
    probability_bully: float
    category: str

class EnsembleResponse(BaseModel):
    text: str
    is_toxic: bool
    is_bully: bool
    probability_toxic: float
    probability_bully: float
    category: str

class HybridResponse(BaseModel):
    text: str
    is_toxic: bool
    is_bully: bool
    probability_toxic: float
    probability_bully: float
    category: str
    decision_source: str
    reason: str

class BatchTextRequest(BaseModel):
    texts: List[str]
    model_name: Optional[str] = "qwen2.5:3b"

class BatchItemResponse(BaseModel):
    text: str
    is_toxic: bool
    is_bully: bool
    probability_toxic: float
    probability_bully: float
    category: str
    decision_source: str
    reason: str

class BatchResponse(BaseModel):
    results: List[BatchItemResponse]

def determine_category(is_toxic: bool, is_bully: bool) -> str:
    if is_toxic and is_bully:
        return "Toxic & Bully (Serangan Langsung)"
    elif is_toxic and not is_bully:
        return "Toxic but Non-Bully (Casual Slang / Swearing)"
    elif not is_toxic and is_bully:
        return "Non-Toxic but Bully (Sarcasm / Insult)"
    else:
        return "Non-Toxic & Non-Bully (Aman)"

