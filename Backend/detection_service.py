"""
Deterministic crop image analysis service.

This is a real image-processing pipeline based on simple visual heuristics,
not a trained ML model. It provides a non-random diagnosis path now and keeps
the backend structured so a true model can be plugged in later.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True


@dataclass(frozen=True)
class DiseaseProfile:
    disease: str
    description: str
    treatment: List[str]
    severity: str


DISEASE_PROFILES: Dict[str, DiseaseProfile] = {
    "Healthy Crop": DiseaseProfile(
        disease="Healthy Crop",
        description="Leaf coloration appears balanced with limited visible stress markers.",
        treatment=[
            "Continue routine field scouting",
            "Maintain balanced irrigation and nutrition",
            "Monitor for any new spotting or discoloration",
        ],
        severity="Low",
    ),
    "Potato Early Blight": DiseaseProfile(
        disease="Potato Early Blight",
        description="Detected dark and brown spotting patterns consistent with early blight stress.",
        treatment=[
            "Remove heavily affected leaves",
            "Apply a suitable fungicide if symptoms spread",
            "Avoid overhead irrigation late in the day",
        ],
        severity="High",
    ),
    "Tomato Mosaic Virus": DiseaseProfile(
        disease="Tomato Mosaic Virus",
        description="Detected uneven green-yellow mottling and color variance suggestive of mosaic-type stress.",
        treatment=[
            "Isolate and remove infected plants if spread continues",
            "Disinfect tools and handling surfaces",
            "Control possible pest vectors and avoid plant-to-plant contact",
        ],
        severity="High",
    ),
    "Rice Blast": DiseaseProfile(
        disease="Rice Blast",
        description="Detected pale lesion-like contrast with darker regions that resemble blast damage.",
        treatment=[
            "Inspect nearby plants for lesion spread",
            "Use resistant varieties where possible",
            "Apply an appropriate fungicide strategy if field symptoms confirm blast",
        ],
        severity="High",
    ),
    "Corn Common Rust": DiseaseProfile(
        disease="Corn Common Rust",
        description="Detected warmer rust-toned spot distribution consistent with common rust-like symptoms.",
        treatment=[
            "Monitor upper leaves for expanding pustules",
            "Use resistant hybrids in future planting cycles",
            "Apply fungicide when disease pressure is significant",
        ],
        severity="Medium",
    ),
}


def _safe_ratio(mask: np.ndarray) -> float:
    return float(mask.mean()) if mask.size else 0.0


def _softmax(values: Dict[str, float]) -> Dict[str, float]:
    keys = list(values.keys())
    arr = np.array([values[key] for key in keys], dtype=np.float32)
    arr = arr - arr.max()
    exp = np.exp(arr)
    probs = exp / exp.sum()
    return {key: float(probs[idx]) for idx, key in enumerate(keys)}


def _extract_metrics(filepath: str) -> Dict[str, float]:
    with Image.open(filepath) as image:
        rgb_image = image.convert("RGB").resize((256, 256))

    arr = np.asarray(rgb_image, dtype=np.float32) / 255.0
    r = arr[:, :, 0]
    g = arr[:, :, 1]
    b = arr[:, :, 2]

    maxc = np.max(arr, axis=2)
    minc = np.min(arr, axis=2)
    delta = maxc - minc + 1e-6

    saturation = np.where(maxc == 0, 0, delta / (maxc + 1e-6))

    hue = np.zeros_like(maxc)
    r_mask = maxc == r
    g_mask = maxc == g
    b_mask = maxc == b

    hue[r_mask] = ((g - b) / delta)[r_mask] % 6
    hue[g_mask] = ((b - r) / delta)[g_mask] + 2
    hue[b_mask] = ((r - g) / delta)[b_mask] + 4
    hue = hue / 6.0

    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    gx = np.abs(np.diff(luminance, axis=1))
    gy = np.abs(np.diff(luminance, axis=0))
    edge_density = float(((gx.mean() + gy.mean()) / 2.0))

    green_mask = (g > r * 1.05) & (g > b * 1.05) & (g > 0.22)
    yellow_mask = (r > 0.35) & (g > 0.35) & (b < 0.28)
    brown_mask = (r > 0.28) & (g > 0.18) & (g < r * 0.92) & (b < g * 0.9)
    rust_mask = (r > 0.42) & (g > 0.18) & (g < 0.48) & (b < 0.22)
    pale_lesion_mask = (luminance > 0.58) & (saturation < 0.4)
    dark_spot_mask = (luminance < 0.22) & (saturation > 0.18)
    mottled_mask = (saturation > 0.22) & (np.abs(g - r) > 0.08)

    return {
        "green_ratio": _safe_ratio(green_mask),
        "yellow_ratio": _safe_ratio(yellow_mask),
        "brown_ratio": _safe_ratio(brown_mask),
        "rust_ratio": _safe_ratio(rust_mask),
        "pale_lesion_ratio": _safe_ratio(pale_lesion_mask),
        "dark_spot_ratio": _safe_ratio(dark_spot_mask),
        "mottled_ratio": _safe_ratio(mottled_mask),
        "saturation_mean": float(saturation.mean()),
        "hue_std": float(hue.std()),
        "edge_density": edge_density,
        "brightness_mean": float(luminance.mean()),
    }


def _score_profiles(metrics: Dict[str, float]) -> Dict[str, float]:
    green_ratio = metrics["green_ratio"]
    yellow_ratio = metrics["yellow_ratio"]
    brown_ratio = metrics["brown_ratio"]
    rust_ratio = metrics["rust_ratio"]
    pale_lesion_ratio = metrics["pale_lesion_ratio"]
    dark_spot_ratio = metrics["dark_spot_ratio"]
    mottled_ratio = metrics["mottled_ratio"]
    hue_std = metrics["hue_std"]
    edge_density = metrics["edge_density"]
    brightness_mean = metrics["brightness_mean"]

    scores = {
        "Healthy Crop": (
            2.4
            + green_ratio * 7.5
            - yellow_ratio * 5.0
            - brown_ratio * 6.0
            - dark_spot_ratio * 4.0
            - rust_ratio * 4.5
            - pale_lesion_ratio * 2.0
            - max(hue_std - 0.15, 0.0) * 5.0
        ),
        "Potato Early Blight": (
            1.6
            + brown_ratio * 9.0
            + dark_spot_ratio * 8.5
            + edge_density * 12.0
            + yellow_ratio * 2.0
            - green_ratio * 2.5
        ),
        "Tomato Mosaic Virus": (
            1.4
            + mottled_ratio * 8.5
            + hue_std * 7.0
            + yellow_ratio * 3.2
            - brown_ratio * 1.8
            - rust_ratio * 1.2
        ),
        "Rice Blast": (
            1.2
            + pale_lesion_ratio * 8.0
            + dark_spot_ratio * 4.0
            + edge_density * 10.0
            + max(0.5 - brightness_mean, 0.0) * 3.5
            - green_ratio * 1.5
        ),
        "Corn Common Rust": (
            1.0
            + rust_ratio * 10.0
            + brown_ratio * 3.5
            + yellow_ratio * 1.4
            + edge_density * 6.5
            - green_ratio * 1.5
        ),
    }
    return scores


def analyze_crop_image(filepath: str) -> Dict[str, object]:
    metrics = _extract_metrics(filepath)
    score_map = _score_profiles(metrics)
    probabilities = _softmax(score_map)

    disease_name = max(probabilities, key=probabilities.get)
    confidence = probabilities[disease_name]
    profile = DISEASE_PROFILES[disease_name]

    return {
        "disease": profile.disease,
        "confidence": round(confidence, 4),
        "description": profile.description,
        "treatment": profile.treatment,
        "severity": profile.severity,
        "analysis_type": "heuristic-image-analysis",
        "metrics": {
            key: round(value, 4)
            for key, value in metrics.items()
        },
    }
