# 🎨 AI Image Colorization Web App

A deep learning–based system to colorize black-and-white images using computer vision and neural networks.
The project focuses on **faithful color restoration**, preserving image structure while intelligently predicting plausible colors.

---

## 🚀 Features

- 🧠 **Deep Learning Colorization**
  - Trained a neural network to map grayscale images to color (LAB color space).
  - Uses transfer learning with a pretrained encoder.

- 🖼️ **High-Resolution Inference**
  - Preserves original image details while applying AI-predicted colors.

- 🖌️ **Interactive Refinement (Smart Brush)**
  - Users can refine specific regions (e.g., faces, flowers) for better colorization.
  - Human-in-the-loop design improves results where visual cues exist.

- 🌐 **Web-Based Application**
  - Backend API built with FastAPI.
  - Frontend built with React for image upload and visualization.

- ⚡ **GPU Acceleration**
  - Supports CUDA-enabled GPUs for faster inference and training.

---

## 🧰 Tech Stack

### Backend
- Python
- PyTorch
- OpenCV
- FastAPI
- Uvicorn

### Frontend
- React
- Vite
- Tailwind CSS
- Framer Motion

### ML Concepts Used
- LAB color space
- Monotonic stacks (for preprocessing logic)
- Transfer learning
- CNN-based regression

---

## 📁 Project Structure

```bash
BW-colorization/
├── training/    # Model, dataset loader, training scripts
├── inference/   # Inference pipeline
├── webapp/
│   ├── backend/ # FastAPI backend
│   └── frontend/ # React frontend
├── model/       # Model directory (weights ignored)
├── data/        # Datasets (ignored)
├── output/      # Generated images (ignored)
├── results/     # Results (ignored)
├── requirements.txt
├── README.md
└── .gitignore
```

---

## ⚙️ Setup Instructions

### Backend Setup

```bash
python -m venv ai-env
# Windows
.\ai-env\Scripts\activate
# Linux/Mac
source ai-env/bin/activate

pip install -r requirements.txt
```

Run backend:

```bash
uvicorn webapp.backend.main:app --reload
```

### Frontend Setup

```bash
cd webapp/frontend
npm install
npm run dev
```

---

## 🧪 Notes on Colorization

The model performs best on:
- Human portraits
- Old photographs
- Nature scenes (trees, flowers, sky)

Some objects (e.g., apples, animals) are color-ambiguous in grayscale.
The system avoids hallucinating colors when visual cues are insufficient.
This is an intentional design choice for faithful restoration.

## 📌 Future Work

- Add a Creative (Generative) Mode for imaginative colorization.
- Improve semantic awareness using segmentation models.
- Deploy the app using Docker / cloud services.
