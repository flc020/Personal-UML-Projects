from functools import lru_cache
from io import BytesIO
import base64

import matplotlib.pyplot as plt
import seaborn as sns
import torch
import torchvision.transforms as transforms
from PIL import Image
import requests
from shiny.express import input, output, render, ui
from torchvision.models import (
    resnet18, ResNet18_Weights,
    resnet50, ResNet50_Weights,
    mobilenet_v2, MobileNet_V2_Weights,
    efficientnet_b0, EfficientNet_B0_Weights,
    efficientnet_b4, EfficientNet_B4_Weights,
    densenet121, DenseNet121_Weights,
)

sns.set_theme(style="whitegrid")

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

MODEL_LOOKUP = {
    "Resnet18": (resnet18, ResNet18_Weights.DEFAULT),
    "Resnet50": (resnet50, ResNet50_Weights.DEFAULT),
    "Mobilenet_V2": (mobilenet_v2, MobileNet_V2_Weights.DEFAULT),
    "EfficientNet_B0": (efficientnet_b0, EfficientNet_B0_Weights.DEFAULT),
    "EfficientNet_B4": (efficientnet_b4, EfficientNet_B4_Weights.DEFAULT),
    "DenseNet121": (densenet121, DenseNet121_Weights.DEFAULT),
}


@lru_cache(maxsize=None)
def get_model(name: str):
    model_fn, weights = MODEL_LOOKUP[name]
    model = model_fn(weights=weights)
    model.eval()
    model.to(DEVICE)
    return model


# Image Transformations
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])

# Load imagenet class names
LABELS_URL = "https://raw.githubusercontent.com/pytorch/hub/master/imagenet_classes.txt"

try:
    labels = requests.get(LABELS_URL, timeout=10).text.strip().split("\n")
except Exception:
    labels = [f"class_{i}" for i in range(1000)]


def render_bar_chart(pred_labels, pred_scores):
    fig, ax = plt.subplots(figsize=(4.4, 3.0))
    ax.barh(pred_labels, pred_scores, color="#3b82f6")
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Probability (%)")
    ax.set_ylabel("")
    for i, score in enumerate(pred_scores):
        ax.text(score + 0.5, i, f"{score:.1f}%", va="center", fontsize=8, color="#333333")
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


ui.page_opts(title="TorchSight: Let's classify!", window_title="TorchSight")


# Udemy provided
ui.tags.style("""
@import url("https://fonts.googleapis.com/css2?family=Fraunces:wght@600&family=Space+Grotesk:wght@400;500;600&display=swap");

:root {
    --bg: #eef4ff;
    --card: #ffffff;
    --ink: #0f172a;
    --muted: #5b6b84;
    --accent: #3b82f6;
    --accent-2: #38bdf8;
    --border: #dbe6ff;
    --shadow: 0 14px 28px rgba(0, 0, 0, 0.08);
}

body {
    background:
        radial-gradient(circle at 12% 12%, rgba(59, 130, 246, 0.14), transparent 45%),
        radial-gradient(circle at 88% 18%, rgba(56, 189, 248, 0.12), transparent 40%),
        var(--bg);
    color: var(--ink);
    font-family: "Space Grotesk", "Segoe UI", sans-serif;
}

h1, h2, h3 {
    font-family: "Fraunces", serif;
}

.result-grid {
    display: grid;
    gap: 18px;
    margin-top: 8px;
}

.result-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 16px 18px 18px;
    box-shadow: var(--shadow);
}

.result-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-size: 1.05rem;
    margin-bottom: 10px;
}

.result-body {
    display: grid;
    grid-template-columns: 220px 1fr;
    gap: 16px;
    align-items: center;
}

.result-img {
    width: 220px;
    border-radius: 14px;
    border: 1px solid var(--border);
    object-fit: cover;
}

.result-chart {
    width: 100%;
    height: auto;
}

.pred-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 8px;
    font-size: 0.9rem;
}

.pred-table td {
    padding: 4px 0;
    border-bottom: 1px dashed var(--border);
}

.pred-table td:last-child {
    text-align: right;
    color: var(--muted);
}

.empty-state {
    margin-top: 24px;
    color: var(--muted);
    font-size: 1rem;
}

.error {
    color: #b00020;
}

@media (max-width: 900px) {
    .result-body {
        grid-template-columns: 1fr;
    }

    .result-img {
        width: 100%;
    }
}
""")

with ui.sidebar():
    choices = list(MODEL_LOOKUP.keys())

    ui.input_select("model_choice", "Model", choices=choices, selected="Resnet18")
    ui.input_slider("topn", "Top N predictions", min=3, max=10, value=3)
    ui.input_file("images", "Upload images", accept=["image/png", "image/jpeg"], multiple=True)
    ui.hr()
    ui.markdown("**TorchSight** | Built using PyTorch and Shiny")

ui.h1("TorchSight")
ui.p("Upload one or more images and compare model predictions side-by-side.")


@output
@render.ui
def results():
    files = input.images()
    model_name = input.model_choice()
    topn = input.topn()

    if not files:
        return ui.div({"class": "empty-state"}, "Upload some images to be classified.")

    model = get_model(model_name)
    blocks = []

    for idx, f in enumerate(files, start=1):
        path = f.get("datapath", f.get("data"))
        mime = f.get("type") or "image/jpeg"

        try:
            img = Image.open(path).convert("RGB")
        except Exception as exc:
            blocks.append(
                ui.tags.div({"class": "result-card"},
                    ui.tags.div({"class": "result-header"}, f"Image {idx}"),
                    ui.tags.div({"class": "error"}, f"Could not open image: {exc}"),
                )
            )
            continue

        img_tensor = transform(img).unsqueeze(0).to(DEVICE)

        with torch.no_grad():
            out = model(img_tensor)
            probs = torch.nn.functional.softmax(out[0], dim=0).cpu()
            top = torch.topk(probs, topn)

        top_indices = top.indices.tolist()
        top_scores = top.values.tolist()
        pred_labels = [labels[i] if i < len(labels) else f"class_{i}" for i in top_indices]
        pred_scores = [score * 100 for score in top_scores]

        with open(path, "rb") as r:
            encoded = base64.b64encode(r.read()).decode("utf-8")

        chart_b64 = render_bar_chart(pred_labels, pred_scores)

        rows = [
            ui.tags.tr(
                ui.tags.td(label),
                ui.tags.td(f"{score:.2f}%"),
            )
            for label, score in zip(pred_labels, pred_scores)
        ]

        blocks.append(
            ui.tags.div({"class": "result-card"},
                ui.tags.div({"class": "result-header"},
                    ui.tags.span(f"Image {idx}"),
                    ui.tags.span(model_name),
                ),
                ui.tags.div({"class": "result-body"},
                    ui.tags.img(
                        src=f"data:{mime};base64,{encoded}",
                        class_="result-img",
                        alt=f"uploaded image {idx}",
                    ),
                    ui.tags.img(
                        src=f"data:image/png;base64,{chart_b64}",
                        class_="result-chart",
                        alt=f"top {topn} predictions",
                    ),
                ),
                ui.tags.table({"class": "pred-table"}, ui.tags.tbody(*rows)),
            )
        )

    return ui.tags.div({"class": "result-grid"}, *blocks)