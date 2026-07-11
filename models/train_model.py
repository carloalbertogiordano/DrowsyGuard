"""
Trains a lightweight custom CNN (<2M parameters, no transfer learning) for
binary drowsy / not_drowsy classification, using dataset/train and
dataset/validation (see prepare_dataset.py).

Preprocessing: no crop, no filter. Just square resize + conversion to
luminance (Y channel of YCbCr, see preprocessing.py). The eye-crop-via-Haar-
cascade idea was abandoned (too many false detections/discards on the real
dataset).

The model output is a single sigmoid neuron: P(drowsy). To guarantee this
explicitly (rather than relying on automatic alphabetical order), the
classes are passed explicitly to flow_from_directory in the order
["not_drowsy", "drowsy"], so "drowsy" is always index 1 (the sigmoid's
positive class) -- consistent with the rest of the pipeline
(DrowsinessMonitor treats confidence as P(drowsy)).

After training, evaluates the model on the validation set (never seen
during training, no augmentation) and produces:
  - models/evaluation/training_curves.png   (loss/val_loss, accuracy/val_accuracy)
  - models/evaluation/confusion_matrix.png
  - models/evaluation/roc_curve.png         (with AUC)
  - models/evaluation/classification_report.txt (precision/recall/f1 per class)
"""

import os

import matplotlib

matplotlib.use("Agg")  # no display, save to file only (headless container)
import matplotlib.pyplot as plt
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    classification_report,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
)
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras import layers, models, callbacks, metrics as keras_metrics

from preprocessing import SQUARE_SIZE, to_luminance

# --- CONFIGURATION ---
# dataset_dedup/: dataset_filtered/ (macro-eye-crop subset removed, see
# filter_dataset.py) with train/validation/test rebuilt via near-duplicate
# clustering (see dedupe_split.py) -- the naive per-image random split
# put near-identical frames from the same recording session on both
# sides of the split, inflating every accuracy number measured before
# this. Whole clusters are now kept together in a single split.
TRAIN_DIR = os.path.join("dataset_dedup", "train")
VAL_DIR = os.path.join("dataset_dedup", "validation")
OUTPUT_MODEL_PATH = os.path.join("models", "drowsiness_model.keras")
EVAL_DIR = os.path.join("models", "evaluation")

BATCH_SIZE = 32
EPOCHS = 20
CLASSES = ["not_drowsy", "drowsy"]  # index 1 = drowsy = sigmoid positive class
PARAM_BUDGET = 2_000_000
USE_CLASS_WEIGHT = False  # diagnostic test: isolate the class_weight effect from preprocessing


def build_model(input_shape=SQUARE_SIZE + (3,)):
    """
    Lightweight custom CNN: 4 Conv2D+BatchNorm+MaxPooling blocks with
    increasing filter counts, followed by GlobalAveragePooling2D (instead of
    a large Flatten+Dense, which would blow up the parameter count) and a
    small dense head. Deliberately kept under 2M parameters: no transfer
    learning, no heavy networks (project constraint).
    """
    inputs = layers.Input(shape=input_shape)

    x = layers.Conv2D(32, 3, padding="same", activation="relu")(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D()(x)

    x = layers.Conv2D(64, 3, padding="same", activation="relu")(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D()(x)

    x = layers.Conv2D(128, 3, padding="same", activation="relu")(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D()(x)

    x = layers.Conv2D(192, 3, padding="same", activation="relu")(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D()(x)

    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(1, activation="sigmoid")(x)

    return models.Model(inputs, outputs, name="drowsy_cnn")


def build_generators():
    # Augmentation ONLY in training. Validation must stay "clean" to
    # measure real performance, without artificial distortions.
    # flow_from_directory loads RGB and resizes to SQUARE_SIZE (square,
    # forces the stretch if the original aspect ratio isn't 1:1); then
    # to_luminance converts to Y (YCbCr) as the preprocessing_function.
    train_datagen = ImageDataGenerator(
        rescale=1.0 / 255,
        rotation_range=15,
        width_shift_range=0.1,
        height_shift_range=0.1,
        zoom_range=0.1,
        horizontal_flip=True,
        brightness_range=[0.5, 1.5],
        channel_shift_range=40.0,
        preprocessing_function=to_luminance,
    )
    val_datagen = ImageDataGenerator(
        rescale=1.0 / 255,
        preprocessing_function=to_luminance,
    )

    train_gen = train_datagen.flow_from_directory(
        TRAIN_DIR,
        target_size=SQUARE_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="binary",
        classes=CLASSES,
        shuffle=True,
    )
    val_gen = val_datagen.flow_from_directory(
        VAL_DIR,
        target_size=SQUARE_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="binary",
        classes=CLASSES,
        shuffle=False,  # fixed order: needed to line up y_true and y_pred
    )
    return train_gen, val_gen


def plot_training_curves(history, output_path):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].plot(history.history["loss"], label="train_loss")
    axes[0].plot(history.history["val_loss"], label="val_loss")
    axes[0].set_title("Loss")
    axes[0].set_xlabel("Epoch")
    axes[0].legend()

    axes[1].plot(history.history["accuracy"], label="train_accuracy")
    axes[1].plot(history.history["val_accuracy"], label="val_accuracy")
    axes[1].set_title("Accuracy")
    axes[1].set_xlabel("Epoch")
    axes[1].legend()

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    print(f"Curve di training salvate in: {output_path}")


def plot_confusion_matrix(y_true, y_pred, output_path):
    cm = confusion_matrix(y_true, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=CLASSES)
    fig, ax = plt.subplots(figsize=(6, 6))
    disp.plot(ax=ax, cmap="Blues", colorbar=False)
    ax.set_title("Confusion Matrix (validation set)")
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    print(f"Confusion matrix salvata in: {output_path}")


def plot_roc_curve(y_true, y_prob, output_path):
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    auc = roc_auc_score(y_true, y_prob)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(fpr, tpr, label=f"ROC (AUC = {auc:.4f})")
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Random")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curve (validation set)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    print(f"ROC curve salvata in: {output_path} (AUC = {auc:.4f})")
    return auc


def evaluate(model, val_gen):
    os.makedirs(EVAL_DIR, exist_ok=True)

    y_true = val_gen.classes  # fixed order (shuffle=False)
    y_prob = model.predict(val_gen).flatten()
    y_pred = (y_prob > 0.5).astype(int)

    report = classification_report(y_true, y_pred, target_names=CLASSES, digits=4)
    print("\n--- Classification report (validation set) ---")
    print(report)

    report_path = os.path.join(EVAL_DIR, "classification_report.txt")
    with open(report_path, "w") as f:
        f.write(report)
    print(f"Report salvato in: {report_path}")

    plot_confusion_matrix(y_true, y_pred, os.path.join(EVAL_DIR, "confusion_matrix.png"))
    auc = plot_roc_curve(y_true, y_prob, os.path.join(EVAL_DIR, "roc_curve.png"))

    if auc > 0.98:
        print(
            "NOTA: AUC molto alto (>0.98) -> il modello discrimina quasi "
            "perfettamente su questo validation set. Non prova che il dataset "
            "sia troncabile, ma suggerisce che il task potrebbe non richiedere "
            "tutti i dati per convergere: valutare una learning curve "
            "(accuracy al variare della % di training set) se si vuole "
            "verificare davvero."
        )


def compute_class_weights():
    """
    Class weights ('balanced' formula: total_n / (n_classes * class_sample_count)).
    The train set is imbalanced (~1.3:1 drowsy/not_drowsy), the weights
    compensate by giving more weight to the minority class in the loss.
    """
    counts = {}
    for idx, class_name in enumerate(CLASSES):
        class_dir = os.path.join(TRAIN_DIR, class_name)
        counts[idx] = len(os.listdir(class_dir))

    total = sum(counts.values())
    n_classes = len(counts)
    weights = {idx: total / (n_classes * count) for idx, count in counts.items()}
    return weights, counts


def train():
    if not os.path.isdir(TRAIN_DIR) or not os.path.isdir(VAL_DIR):
        print(f"ERRORE: mancano '{TRAIN_DIR}' e/o '{VAL_DIR}'.")
        print("Esegui prima: python models/prepare_dataset.py")
        return

    train_gen, val_gen = build_generators()
    print(f"Class indices (0=negativa, 1=positiva): {train_gen.class_indices}")

    class_weight, class_counts = compute_class_weights()
    counts_named = {CLASSES[i]: c for i, c in class_counts.items()}
    weights_named = {CLASSES[i]: round(w, 4) for i, w in class_weight.items()}
    print(f"Conteggi classi (train): {counts_named}")
    print(f"Class weight (balanced): {weights_named} (USE_CLASS_WEIGHT={USE_CLASS_WEIGHT})")

    model = build_model(input_shape=SQUARE_SIZE + (3,))
    model.compile(
        optimizer="adam",
        loss="binary_crossentropy",
        metrics=[
            "accuracy",
            keras_metrics.Precision(name="precision"),
            keras_metrics.Recall(name="recall"),
        ],
    )
    model.summary()

    n_params = model.count_params()
    print(f"Parametri totali: {n_params:,} (budget: {PARAM_BUDGET:,})")
    if n_params > PARAM_BUDGET:
        print("ATTENZIONE: budget parametri superato.")

    early_stop = callbacks.EarlyStopping(
        monitor="val_loss",
        patience=3,
        min_delta=1e-3,  # improvements below this threshold don't count (noise)
        restore_best_weights=True,
    )

    history = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS,
        callbacks=[early_stop],
        class_weight=class_weight if USE_CLASS_WEIGHT else None,
    )

    os.makedirs(os.path.dirname(OUTPUT_MODEL_PATH), exist_ok=True)
    model.save(OUTPUT_MODEL_PATH)
    print(f"Modello salvato in: {OUTPUT_MODEL_PATH}")

    best_val_acc = max(history.history.get("val_accuracy", [0]))
    print(f"Miglior val_accuracy: {best_val_acc:.4f}")

    os.makedirs(EVAL_DIR, exist_ok=True)
    plot_training_curves(history, os.path.join(EVAL_DIR, "training_curves.png"))
    evaluate(model, val_gen)


if __name__ == "__main__":
    train()
