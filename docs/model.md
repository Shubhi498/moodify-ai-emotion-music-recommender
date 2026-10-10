# Emotion model and reproducibility

## Dataset and labels

The CNN is trained from the FER-2013 CSV. The expected columns are `emotion`, `pixels`, and `Usage`; each image must be 48 by 48 grayscale pixels. The seven labels follow the dataset's index order: angry, disgust, fear, happy, sad, surprise, neutral.

The training script uses rows marked `Training` for fitting, `PublicTest` for validation, and `PrivateTest` for final evaluation. It reports test accuracy, per-class precision and recall, and a confusion matrix for the actual run. No metric is promised in advance.

## Train

Install dependencies in an environment that supports the pinned TensorFlow/Keras and OpenCV packages, obtain FER-2013 through its dataset source, then run:

```text
python ai_model/train_fer2013.py C:\path\to\fer2013.csv --epochs 35
```

The resulting `ai_model/models/emotion_cnn.keras` file is ignored by Git because trained weights are data artifacts and can be large. Put the trained file at that path on each deployed environment, or set `EMOTION_MODEL_PATH`. The application does not claim recognition is available until that real file can be loaded. No model weights are included or inferred to have been trained in this repository.

## Inference preprocessing

The webcam image is decoded in memory by OpenCV. The largest Haar Cascade face is converted to grayscale, cropped, resized to 48 by 48, cast to float32, divided by 255, and reshaped to `(1, 48, 48, 1)`. The CNN returns seven class probabilities. Predictions below `EMOTION_CONFIDENCE_THRESHOLD` are marked low-confidence. No image file is written.

Facial expression classification is an estimate of visible expression, can be inaccurate, and is not a medical or psychological assessment.
