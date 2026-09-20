"""
predict.py — Model loading and inference for diabetic retinopathy screening.

Model: EfficientNetB0 fine-tuned for 5-class DR severity grading
Source: manudaza/retinal-triage-efficientnetb0 on Hugging Face
Input:  224x224x3 RGB, preprocessed with efficientnet.preprocess_input
Output: 5-class softmax (No DR → Proliferative DR)
"""

import os
import numpy as np
from PIL import Image
import tensorflow as tf
import keras
from huggingface_hub import hf_hub_download

# Suppress verbose TF / oneDNN logs
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

# ------------------------------------------------------------------
# Class labels (index order matches model output)
# ------------------------------------------------------------------
CLASS_LABELS = [
    "No DR",
    "Mild NPDR",
    "Moderate NPDR",
    "Severe NPDR",
    "Proliferative DR",
]

# Expose referral logic & multi-language messages
from referral import get_patient_message, PATIENT_GUIDANCE, MESSAGES  # noqa: E402

# ------------------------------------------------------------------
# Load model once at import time
# The HF repo contains a single .keras file; download it explicitly
# then load from the local path (avoids the hf:// dir-layout issue).
# ------------------------------------------------------------------
print("[predict.py] Downloading model from Hugging Face …")
_model_path = hf_hub_download(
    repo_id="manudaza/retinal-triage-efficientnetb0",
    filename="efficientnetb0_finetuned_patched.keras",
)
print(f"[predict.py] Model cached at: {_model_path}")
print("[predict.py] Loading model …")
model = keras.saving.load_model(_model_path)
print("[predict.py] Model loaded successfully.")


# ------------------------------------------------------------------
# Preprocessing helper
# ------------------------------------------------------------------
def _preprocess(pil_image: Image.Image) -> np.ndarray:
    """
    Resize a PIL image to 224x224, convert to float32, apply
    EfficientNet-specific preprocessing (scales to ~[-1, 1]).
    Returns a batch tensor of shape (1, 224, 224, 3).
    """
    img = pil_image.convert("RGB").resize((224, 224), Image.LANCZOS)
    arr = np.array(img, dtype=np.float32)          # (224, 224, 3)
    arr = np.expand_dims(arr, axis=0)              # (1, 224, 224, 3)
    arr = tf.keras.applications.efficientnet.preprocess_input(arr)
    return arr


# ------------------------------------------------------------------
# Public inference function
# ------------------------------------------------------------------
def predict(pil_image: Image.Image):
    """
    Run inference on a PIL image.

    Parameters
    ----------
    pil_image : PIL.Image.Image
        A fundus photograph.

    Returns
    -------
    predicted_index : int
        Index of the predicted class (0–4).
    predicted_label : str
        Human-readable severity label.
    scores : dict[str, float]
        Mapping from each class label to its confidence (0–1).
    """
    x = _preprocess(pil_image)
    raw = model.predict(x, verbose=0)         # shape: (1, 5)
    probs = raw[0].tolist()                   # list of 5 floats

    predicted_index = int(np.argmax(probs))
    predicted_label = CLASS_LABELS[predicted_index]
    scores = {label: float(prob) for label, prob in zip(CLASS_LABELS, probs)}

    return predicted_index, predicted_label, scores
