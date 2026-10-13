"""This module stores all pretrained ai models used so they can be re-used on other modules"""

import torch
from transformers import pipeline
from sentence_transformers import SentenceTransformer

device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")

# used to find intents
ner_pipeline = pipeline(
    "token-classification",
    model="niruthiha/restaurant-ner",
    aggregation_strategy="simple",
    device=device,
)

# used to embedd english language for checking cosine similarity
embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
embedding_model.to(device)
