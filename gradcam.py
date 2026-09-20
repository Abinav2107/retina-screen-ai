"""
gradcam.py -- Manual Grad-CAM explainability for the DR screening model
with dynamic opacity adjustment and component caching.
"""

import os
from typing import Tuple
import numpy as np
import cv2
import keras
import tensorflow as tf
from PIL import Image

os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

# ------------------------------------------------------------------
# Plain-language captions per severity class
# ------------------------------------------------------------------
CAPTIONS = {
    0: (
        "No significant abnormalities detected in the retina. "
        "The highlighted region shows areas the model focused on to confirm "
        "the absence of retinopathy."
    ),
    1: (
        "Highlighted regions show possible microaneurysms or small haemorrhages "
        "-- early signs of diabetic retinopathy. "
        "Regular monitoring is recommended."
    ),
    2: (
        "Highlighted regions show possible microaneurysms or small haemorrhages "
        "-- early signs of diabetic retinopathy. "
        "Regular monitoring is recommended."
    ),
    3: (
        "Highlighted regions show extensive retinal damage including possible "
        "abnormal blood vessel growth or haemorrhages -- urgent referral recommended."
    ),
    4: (
        "Highlighted regions show extensive retinal damage including possible "
        "abnormal blood vessel growth -- urgent referral recommended."
    ),
}


def get_caption(predicted_class_index: int) -> str:
    """Return a plain-language explanation for the predicted severity class."""
    return CAPTIONS.get(predicted_class_index, "")


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------
def _get_post_conv_layers(effnet_submodel):
    """
    Return the layers inside efficientnetb0 that come AFTER top_conv, in order.
    Standard EfficientNetB0 sequence: top_conv -> top_bn -> top_activation -> avg_pool
    """
    preferred = ["top_bn", "top_activation", "avg_pool"]
    found = []
    for name in preferred:
        try:
            found.append(effnet_submodel.get_layer(name))
        except ValueError:
            matched = [l for l in effnet_submodel.layers if name in l.name.lower()]
            if matched:
                found.append(matched[-1])
    return found


def _build_conv_extractor(effnet_submodel):
    """
    Build a sub-model that maps efficientnetb0 input -> top_conv output.
    Output shape is typically (batch, 7, 7, 1280) for a 224x224 input.
    """
    top_conv = effnet_submodel.get_layer("top_conv")
    return keras.Model(
        inputs=effnet_submodel.inputs,
        outputs=top_conv.output,
        name="conv_extractor",
    )


# In-memory cache for the most recently computed components
# Enables instantaneous 60fps sliding of opacity without re-running backpropagation
_LAST_GRADCAM_CACHE = {
    "img_224": None,
    "heatmap_rgb": None,
    "predicted_class_index": None,
}


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------
def compute_gradcam_components(
    pil_image: Image.Image,
    model,
    predicted_class_index: int,
) -> Tuple[Image.Image, np.ndarray]:
    """
    Compute raw Grad-CAM components (original 224x224 and colored heatmap).
    Caches results in memory for real-time opacity adjustments.

    Returns
    -------
    img_224 : PIL.Image.Image
        224x224 RGB image.
    heatmap_rgb : np.ndarray
        224x224x3 uint8 RGB array of the jet colormap heatmap.
    """
    global _LAST_GRADCAM_CACHE

    img_224 = pil_image.convert("RGB").resize((224, 224), Image.LANCZOS)
    arr = np.array(img_224, dtype=np.float32)
    x = tf.keras.applications.efficientnet.preprocess_input(
        np.expand_dims(arr, axis=0)
    )
    x_tensor = tf.constant(x)

    effnet = model.get_layer("efficientnetb0")
    conv_extractor = _build_conv_extractor(effnet)
    post_conv_layers = _get_post_conv_layers(effnet)
    dropout_layer = model.get_layer("dropout")
    dense_layer = model.get_layer("dense")

    with tf.GradientTape() as tape:
        conv_outputs = conv_extractor(x_tensor, training=False)
        tape.watch(conv_outputs)

        h = conv_outputs
        for layer in post_conv_layers:
            h = layer(h, training=False)
        h = dropout_layer(h, training=False)
        predictions = dense_layer(h, training=False)
        class_score = predictions[:, predicted_class_index]

    grads = tape.gradient(class_score, conv_outputs)
    if grads is None:
        heatmap_rgb = np.zeros((224, 224, 3), dtype=np.uint8)
        _LAST_GRADCAM_CACHE = {
            "img_224": img_224,
            "heatmap_rgb": heatmap_rgb,
            "predicted_class_index": predicted_class_index,
        }
        return img_224, heatmap_rgb

    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2)).numpy()
    conv_np = conv_outputs[0].numpy().copy()
    for i, w in enumerate(pooled_grads):
        conv_np[:, :, i] *= w
    heatmap = np.mean(conv_np, axis=-1)

    heatmap = np.maximum(heatmap, 0)
    max_val = heatmap.max()
    if max_val > 0:
        heatmap /= max_val

    heatmap_u8 = np.uint8(255 * heatmap)
    heatmap_resized = cv2.resize(heatmap_u8, (224, 224), interpolation=cv2.INTER_LINEAR)
    heatmap_bgr = cv2.applyColorMap(heatmap_resized, cv2.COLORMAP_JET)
    heatmap_rgb = cv2.cvtColor(heatmap_bgr, cv2.COLOR_BGR2RGB)

    _LAST_GRADCAM_CACHE = {
        "img_224": img_224,
        "heatmap_rgb": heatmap_rgb,
        "predicted_class_index": predicted_class_index,
    }

    return img_224, heatmap_rgb


def blend_gradcam_overlay(
    img_224: Image.Image,
    heatmap_rgb: np.ndarray,
    opacity_percent: int = 40,
) -> Image.Image:
    """
    Blend fundus photograph and heatmap with custom opacity (0 to 100%).
    Runs in <1ms.
    """
    alpha = max(0.0, min(1.0, float(opacity_percent) / 100.0))
    original_np = np.array(img_224)
    overlay = ((1.0 - alpha) * original_np + alpha * heatmap_rgb).astype(np.uint8)
    return Image.fromarray(overlay)


def adjust_cached_opacity(opacity_percent: int = 40) -> Image.Image:
    """
    Instantly adjust opacity of the most recently computed Grad-CAM heatmap
    without re-evaluating the neural network.
    """
    img_224 = _LAST_GRADCAM_CACHE.get("img_224")
    heatmap_rgb = _LAST_GRADCAM_CACHE.get("heatmap_rgb")
    if img_224 is None or heatmap_rgb is None:
        return None
    return blend_gradcam_overlay(img_224, heatmap_rgb, opacity_percent=opacity_percent)


def generate_gradcam(
    pil_image: Image.Image,
    model,
    predicted_class_index: int,
    opacity_percent: int = 40,
) -> Image.Image:
    """
    Compute Grad-CAM heatmap and blend with customizable opacity (default 40%).
    """
    img_224, heatmap_rgb = compute_gradcam_components(pil_image, model, predicted_class_index)
    return blend_gradcam_overlay(img_224, heatmap_rgb, opacity_percent=opacity_percent)
