import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

class ServiceConfig:
    def __init__(self):
        config_path = DATA_DIR / "service_config.json"
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        self.languages = self.config["languages"]
        self.ko_max_len = self.config["ko_max_len"]
        self.embedding_dim = self.config["embedding_dim"]
        self.gender2id = self.config["gender2id"]
        self.onnx_inputs = self.config["onnx_inputs"]
        self.onnx_output = self.config["onnx_output"]
        self.vector_pattern = self.config["vector_pattern"]
        self.meta_pattern = self.config["meta_pattern"]
        self.score_type = self.config["score_type"]

config = ServiceConfig()
