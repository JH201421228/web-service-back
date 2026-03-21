import os
import json
import numpy as np
import pandas as pd
import onnxruntime as ort
from .config import config, DATA_DIR

class ModelManager:
    def __init__(self):
        self._load_vocab()
        self._load_onnx()
        self._load_data()

    def _load_vocab(self):
        vocab_path = DATA_DIR / "ko_vocab.json"
        with open(vocab_path, "r", encoding="utf-8") as f:
            self.vocab = json.load(f)
        # Create char to id mapping
        self.char2id = {char: idx for idx, char in enumerate(self.vocab)}
        self.pad_id = self.char2id.get("<pad>", 0)
        self.unk_id = self.char2id.get("<unk>", 1)

    def _load_onnx(self):
        onnx_path = DATA_DIR / "ko_encoder.onnx"
        self.ort_session = ort.InferenceSession(str(onnx_path))

    def _load_data(self):
        self.candidate_vectors = {}
        self.candidate_meta = {}
        for lang in config.languages:
            vec_path = DATA_DIR / config.vector_pattern.format(lang=lang)
            meta_path = DATA_DIR / config.meta_pattern.format(lang=lang)
            if vec_path.exists() and meta_path.exists():
                self.candidate_vectors[lang] = np.load(str(vec_path))
                self.candidate_meta[lang] = pd.read_parquet(str(meta_path))

    def _decompose_hangul(self, text):
        CHO = ["ㄱ", "ㄲ", "ㄴ", "ㄷ", "ㄸ", "ㄹ", "ㅁ", "ㅂ", "ㅃ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅉ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]
        JUNG = ["ㅏ", "ㅐ", "ㅑ", "ㅒ", "ㅓ", "ㅔ", "ㅕ", "ㅖ", "ㅗ", "ㅘ", "ㅙ", "ㅚ", "ㅛ", "ㅜ", "ㅝ", "ㅞ", "ㅟ", "ㅠ", "ㅡ", "ㅢ", "ㅣ"]
        JONG = ["", "ㄱ", "ㄲ", "ㄳ", "ㄴ", "ㄵ", "ㄶ", "ㄷ", "ㄹ", "ㄺ", "ㄻ", "ㄼ", "ㄽ", "ㄾ", "ㄿ", "ㅀ", "ㅁ", "ㅂ", "ㅄ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]
        
        result = []
        for char in text:
            if 0xAC00 <= ord(char) <= 0xD7A3:
                code = ord(char) - 0xAC00
                cho = code // 588
                jung = (code % 588) // 28
                jong = code % 28
                
                result.append(CHO[cho])
                result.append(JUNG[jung])
                if jong > 0:
                    result.append(JONG[jong])
            else:
                result.append(char)
        return result

    def get_embedding(self, name: str, gender: str):
        jamos = self._decompose_hangul(name)
        input_ids = [self.char2id.get(char, self.unk_id) for char in jamos]
        
        # padding/truncating
        max_len = config.ko_max_len
        if len(input_ids) > max_len:
            input_ids = input_ids[:max_len]
        else:
            input_ids = input_ids + [self.pad_id] * (max_len - len(input_ids))
            
        gender_id = config.gender2id.get(gender, config.gender2id.get("UNK", 3))
        
        # create numpy arrays (typically batch size 1)
        # Check expected shape from config/onnx inputs. Often it's [batch, sequence] and [batch]
        input_ids_arr = np.array([input_ids], dtype=np.int64)
        gender_ids_arr = np.array([gender_id], dtype=np.int64)
        
        inputs = {
            config.onnx_inputs[0]: input_ids_arr,
            config.onnx_inputs[1]: gender_ids_arr
        }
        
        # run inference
        outputs = self.ort_session.run([config.onnx_output], inputs)
        embedding = outputs[0][0] # remove batch dimension
        
        # Normalize if necessary based on score_type
        if "normalized" in config.score_type:
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm

        return embedding

    def get_top_k(self, embedding, lang: str, k: int = 5):
        if lang not in self.candidate_vectors:
            raise ValueError(f"Language {lang} is not supported or data is missing.")
            
        vectors = self.candidate_vectors[lang]
        meta = self.candidate_meta[lang]
        
        # compute similarity
        if "inner_product" in config.score_type:
            # check if vectors need normalization? usually they are pre-normalized
            scores = np.dot(vectors, embedding)
        else:
            # fallback to cosine similarity
            scores = np.dot(vectors, embedding) / (np.linalg.norm(vectors, axis=1) * np.linalg.norm(embedding) + 1e-9)
            
        # Get top k indices
        top_indices = np.argsort(scores)[::-1][:k]
        
        results = []
        for idx in top_indices:
            row = meta.iloc[idx]
            # assume name and gender are present in the parquet columns
            name_val = row.get('candidate_romanized', 'Unknown')
            gender_val = row.get('candidate_gender', 'Unknown')
            results.append({
                "name": name_val,
                "gender": gender_val,
                "score": float(scores[idx])
            })
            
        return results

model_manager = ModelManager()
