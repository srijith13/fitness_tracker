import matplotlib.pyplot as plt
from pathlib import Path
from models import list_weights, list_exercises
import flet as ft
from datetime import datetime
import base64
from PIL import Image
import io

CHART_PATH = Path(__file__).parent / "data" / "chart.png"

# def generate_weight_chart():
#     data = list_weights()
#     if not data:
#         plt.figure()
#         plt.text(0.5, 0.5, 'No weight data', ha='center')
#         plt.savefig(CHART_PATH)
#         return str(CHART_PATH)

#     dates = [w['date'] for w in data]
#     vals = [w['weight_kg'] for w in data]

#     plt.figure(figsize=(6,3))
#     plt.plot(dates, vals)
#     plt.xticks(rotation=45)
#     plt.tight_layout()
#     plt.savefig(CHART_PATH)
#     return str(CHART_PATH)

def generate_weight_chart():

    data = list_weights()

    if not data:
        return [], []   # no points, no labels

     # Convert date strings → datetime
    for w in data:
        if isinstance(w["date"], str):
            w["date"] = datetime.fromisoformat(w["date"]).date()


    # Sort data by date
    data = sorted(data, key=lambda w: w["date"])

    xs = list(range(len(data)))                # X numeric values: 0,1,2,3...
    ys = [w["weight_kg"] for w in data]        # Y values
    labels = [w["date"].strftime("%m-%d")  for w in data ]     # labels for ticks

    return list(zip(xs, ys)), labels

def png_converter(ico_bytes):
    # 2. Convert ICO → PNG in memory
    ico_image = Image.open(io.BytesIO(ico_bytes))
    png_buffer = io.BytesIO()
    ico_image.save(png_buffer, format="PNG")
    png_base64 = base64.b64encode(png_buffer.getvalue()).decode()
    return png_base64




