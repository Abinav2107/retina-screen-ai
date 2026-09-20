"""inspect_model.py — Print layer names to identify the Grad-CAM target layer."""
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import keras
from huggingface_hub import hf_hub_download

path = hf_hub_download(
    repo_id="manudaza/retinal-triage-efficientnetb0",
    filename="efficientnetb0_finetuned_patched.keras",
)
model = keras.saving.load_model(path)

print("=== TOP-LEVEL LAYERS ===")
for i, layer in enumerate(model.layers):
    print(f"  [{i:02d}] {layer.name:<45} {type(layer).__name__}")

print()
# Check for sub-models (nested model layers)
for layer in model.layers:
    if hasattr(layer, "layers"):
        print(f"=== SUB-MODEL: {layer.name} ===")
        conv_layers = [l for l in layer.layers if "conv" in l.name.lower()]
        print(f"  Total conv layers inside: {len(conv_layers)}")
        print("  Last 6 conv layers:")
        for l in conv_layers[-6:]:
            try:
                shape = str(l.output_shape)
            except Exception:
                shape = "unknown"
            print(f"    {l.name:<50} {shape}")
        break

print()
print("=== MODEL INPUT/OUTPUT ===")
print(f"  Input:  {model.input_shape}")
print(f"  Output: {model.output_shape}")
