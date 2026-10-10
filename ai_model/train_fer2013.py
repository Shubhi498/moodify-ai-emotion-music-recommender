"""Train the Moodify CNN from the FER-2013 CSV using TensorFlow/Keras."""
import argparse
import csv
from pathlib import Path

import numpy as np
from tensorflow import keras
from tensorflow.keras import layers

LABEL_NAMES = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]


def read_dataset(csv_path):
    images, labels, usages = [], [], []
    with Path(csv_path).open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        required = {"emotion", "pixels", "Usage"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Expected FER-2013 CSV columns: emotion, pixels, Usage")
        for row in reader:
            pixels = np.fromstring(row["pixels"], sep=" ", dtype=np.uint8)
            if pixels.size != 48 * 48:
                continue
            label = int(row["emotion"])
            if label < 0 or label >= len(LABEL_NAMES):
                continue
            images.append(pixels.reshape(48, 48, 1))
            labels.append(label)
            usages.append(row["Usage"].strip())
    if not images:
        raise ValueError("No valid 48x48 images were found in the FER-2013 CSV.")
    x = np.asarray(images, dtype="float32") / 255.0
    y = np.asarray(labels, dtype="int64")
    usages = np.asarray(usages)
    return x, y, usages


def build_model():
    model = keras.Sequential([
        layers.Input(shape=(48, 48, 1)),
        layers.RandomFlip("horizontal"), layers.RandomRotation(0.06), layers.RandomContrast(0.12),
        layers.Conv2D(32, 3, padding="same", activation="relu"), layers.BatchNormalization(), layers.MaxPooling2D(), layers.Dropout(0.20),
        layers.Conv2D(64, 3, padding="same", activation="relu"), layers.BatchNormalization(), layers.MaxPooling2D(), layers.Dropout(0.25),
        layers.Conv2D(128, 3, padding="same", activation="relu"), layers.BatchNormalization(), layers.MaxPooling2D(), layers.Dropout(0.30),
        layers.Flatten(), layers.Dense(128, activation="relu"), layers.Dropout(0.40), layers.Dense(7, activation="softmax"),
    ])
    model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.001), loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    return model


def evaluate(model, x, y):
    probabilities = model.predict(x, verbose=0)
    predicted = probabilities.argmax(axis=1)
    matrix = np.zeros((7, 7), dtype="int64")
    for actual, guess in zip(y, predicted):
        matrix[actual, guess] += 1
    precision, recall = [], []
    for label in range(7):
        true_positive = matrix[label, label]
        precision.append(true_positive / max(int(matrix[:, label].sum()), 1))
        recall.append(true_positive / max(int(matrix[label, :].sum()), 1))
    return float(np.mean(predicted == y)), precision, recall, matrix


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", help="Path to the FER-2013 fer2013.csv file")
    parser.add_argument("--epochs", type=int, default=35)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "models/emotion_cnn.keras")
    args = parser.parse_args()
    if args.epochs < 1 or args.batch_size < 1:
        parser.error("epochs and batch-size must be positive")
    x, y, usages = read_dataset(args.csv)
    training = usages == "Training"
    validation = usages == "PublicTest"
    testing = usages == "PrivateTest"
    if not training.any() or not validation.any() or not testing.any():
        raise ValueError("FER-2013 must include Training, PublicTest, and PrivateTest rows.")
    model = build_model()
    model.fit(x[training], y[training], validation_data=(x[validation], y[validation]), epochs=args.epochs, batch_size=args.batch_size, callbacks=[keras.callbacks.EarlyStopping(patience=6, restore_best_weights=True), keras.callbacks.ReduceLROnPlateau(patience=3, factor=0.5)], class_weight={i: len(y[training]) / max(7 * int((y[training] == i).sum()), 1) for i in range(7)})
    accuracy, precision, recall, matrix = evaluate(model, x[testing], y[testing])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    model.save(args.output)
    print(f"Test accuracy: {accuracy:.4f}")
    print("Per-class precision:", dict(zip(LABEL_NAMES, [round(float(v), 4) for v in precision])))
    print("Per-class recall:", dict(zip(LABEL_NAMES, [round(float(v), 4) for v in recall])))
    print("Confusion matrix (actual rows, predicted columns):")
    print(matrix)
    print(f"Saved model: {args.output}")


if __name__ == "__main__":
    main()
