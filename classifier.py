"""
classifier.py
민원 텍스트 분류 모델 추론 모듈

Colab(train_kobert_colab.ipynb)에서 학습한 모델을 불러와서
민원 텍스트를 6개 카테고리 중 하나로 분류합니다.

사용 예:

    from classifier import get_classifier
    clf = get_classifier()
    result = clf.classify("급식에 머리카락이 나왔어요")
    # {'category': '급식', 'confidence': 96.8, 'scores': {...}}
"""

import os
import json
from typing import List, Optional

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

try:
    import streamlit as st
    _HAS_STREAMLIT = True
except ImportError:
    _HAS_STREAMLIT = False

# 팀 레포 구조 기준 모델 저장 경로 (model/train.py의 OUTPUT_DIR과 동일하게 맞춤)
# 다른 경로/HF Hub repo id를 쓰고 싶으면 환경변수로 덮어쓰면 됨
MODEL_PATH = os.environ.get("COMPLAINT_MODEL_PATH", "./model/saved_model")

# 팀 공식 라벨 체계 (model/train.py의 LABEL_TO_ID와 동일해야 함)
LABEL_TO_ID = {
    "수업/학습 문제": 0,
    "교사 태도/행동": 1,
    "시설/환경": 2,
    "급식": 3,
    "생활지도/안전": 4,
    "기타": 5,
}


class ComplaintClassifier:
    def __init__(self, model_path: str = MODEL_PATH):
        self.model_path = model_path
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.eval()  # 추론 모드 (드롭아웃 비활성화, 약간의 메모리/속도 이점)

        # 학습 스크립트가 저장하는 label_map.json을 최우선으로 사용 (팀 공식 포맷)
        # 과거 버전과의 호환을 위해 label2id.json도 보조로 확인
        id2label = None
        for filename in ("label_map.json", "label2id.json"):
            candidate = os.path.join(model_path, filename)
            if os.path.exists(candidate):
                with open(candidate, "r", encoding="utf-8") as f:
                    label2id = json.load(f)
                id2label = {v: k for k, v in label2id.items()}
                break

        if id2label is not None:
            self.id2label = id2label
        elif getattr(self.model.config, "id2label", None):
            # 그것도 없으면 모델 config에 저장된 id2label 사용
            raw = self.model.config.id2label
            self.id2label = {int(k): v for k, v in raw.items()}
        else:
            # 최후 수단: 코드에 박아둔 팀 공식 라벨 체계 사용
            self.id2label = {v: k for k, v in LABEL_TO_ID.items()}

    @torch.no_grad()
    def classify(self, text: str) -> dict:
        """단일 민원 텍스트를 분류합니다.

        Returns:
            {
                "category": "급식",
                "confidence": 96.8,                 # 0~100 (%)
                "scores": {"급식": 96.8, "기타": 1.2, ...}  # 전체 카테고리별 확률
            }
        """
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=256)
        logits = self.model(**inputs).logits
        probs = torch.softmax(logits, dim=-1)[0]

        pred_id = int(torch.argmax(probs).item())
        category = self.id2label[pred_id]
        confidence = float(probs[pred_id].item())

        scores = {self.id2label[i]: round(float(probs[i].item()) * 100, 1) for i in range(len(probs))}

        return {
            "category": category,
            "confidence": round(confidence * 100, 1),
            "scores": scores,
        }

    @torch.no_grad()
    def classify_batch(self, texts: List[str]) -> List[dict]:
        return [self.classify(t) for t in texts]


# Streamlit 앱에서는 매 요청마다 모델을 다시 로드하면 느리고 메모리도 낭비되므로 캐싱합니다.
if _HAS_STREAMLIT:
    @st.cache_resource(show_spinner="민원 분류 모델을 불러오는 중입니다...")
    def get_classifier(model_path: str = MODEL_PATH) -> ComplaintClassifier:
        return ComplaintClassifier(model_path)
else:
    _cached: Optional[ComplaintClassifier] = None

    def get_classifier(model_path: str = MODEL_PATH) -> ComplaintClassifier:
        global _cached
        if _cached is None:
            _cached = ComplaintClassifier(model_path)
        return _cached


if __name__ == "__main__":
    clf = ComplaintClassifier()
    sample = "오늘 급식에 머리카락이 나왔어요. 위생 관리가 걱정됩니다."
    print(clf.classify(sample))
