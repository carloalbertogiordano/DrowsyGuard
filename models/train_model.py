"""
Allena una CNN custom leggera (<2M parametri, niente transfer learning) per la
classificazione binaria drowsy / not_drowsy, usando dataset/train e
dataset/validation (vedi prepare_dataset.py).

Preprocessing: nessun crop, nessun filtro. Solo resize a immagine quadrata +
conversione a luminanza (canale Y di YCbCr, vedi preprocessing.py). L'idea
del crop occhio via Haar cascade e' stata abbandonata (troppi falsi
rilevamenti/scarti sul dataset reale).

L'output del modello e' un singolo neurone sigmoid: P(drowsy). Per garantirlo
in modo esplicito (non affidandosi all'ordine alfabetico automatico), le
classi vengono passate esplicitamente a flow_from_directory nell'ordine
["not_drowsy", "drowsy"], cosi' "drowsy" e' sempre l'indice 1 (classe
positiva del sigmoid) -- coerente con il resto della pipeline
(DrowsinessMonitor tratta la confidence come P(drowsy)).

Dopo il training, valuta il modello sul validation set (mai visto in training,
niente augmentation) e produce:
  - models/evaluation/training_curves.png   (loss/val_loss, accuracy/val_accuracy)
  - models/evaluation/confusion_matrix.png
  - models/evaluation/roc_curve.png         (con AUC)
  - models/evaluation/classification_report.txt (precision/recall/f1 per classe)
"""

import os

import matplotlib

matplotlib.use("Agg")  # niente display, salviamo solo su file (container headless)
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

# --- CONFIGURAZIONE ---
TRAIN_DIR = os.path.join("dataset", "train")
VAL_DIR = os.path.join("dataset", "validation")
OUTPUT_MODEL_PATH = os.path.join("models", "drowsiness_model.keras")
EVAL_DIR = os.path.join("models", "evaluation")

BATCH_SIZE = 32
EPOCHS = 20
CLASSES = ["not_drowsy", "drowsy"]  # indice 1 = drowsy = classe positiva del sigmoid
PARAM_BUDGET = 2_000_000
USE_CLASS_WEIGHT = False  # test diagnostico: isolare effetto class_weight dal preprocessing


def build_model(input_shape=SQUARE_SIZE + (3,)):
    """
    CNN custom leggera: 4 blocchi Conv2D+BatchNorm+MaxPooling con filtri
    crescenti, seguiti da GlobalAveragePooling2D (al posto di Flatten+Dense
    grande, che farebbe esplodere il conteggio parametri) e una piccola testa
    densa. Tenuta volutamente sotto i 2M parametri: niente transfer learning,
    niente reti pesanti (vincolo di progetto).
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
    # Augmentation SOLO in training. La validation deve restare "pulita" per
    # misurare le prestazioni reali, senza distorsioni artificiali.
    # flow_from_directory carica RGB e ridimensiona a SQUARE_SIZE (quadrato,
    # forza lo stretch se l'aspect ratio originale non e' 1:1); poi
    # to_luminance converte a Y (YCbCr) come preprocessing_function.
    train_datagen = ImageDataGenerator(
        rescale=1.0 / 255,
        rotation_range=15,
        width_shift_range=0.1,
        height_shift_range=0.1,
        zoom_range=0.1,
        horizontal_flip=True,
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
        shuffle=False,  # ordine fisso: serve per far combaciare y_true e y_pred
    )
    return train_gen, val_gen


def plot_training_curves(history, output_path):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].plot(history.history["loss"], label="train_loss")
    axes[0].plot(history.history["val_loss"], label="val_loss")
    axes[0].set_title("Loss")
    axes[0].set_xlabel("Epoca")
    axes[0].legend()

    axes[1].plot(history.history["accuracy"], label="train_accuracy")
    axes[1].plot(history.history["val_accuracy"], label="val_accuracy")
    axes[1].set_title("Accuracy")
    axes[1].set_xlabel("Epoca")
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

    y_true = val_gen.classes  # ordine fisso (shuffle=False)
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
    Pesi di classe (formula 'balanced': n_totale / (n_classi * n_campioni_classe)).
    Il train set e' sbilanciato (~1.3:1 drowsy/not_drowsy), i pesi
    compensano dando piu' peso alla classe minoritaria in loss.
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
        min_delta=1e-3,  # miglioramenti sotto questa soglia non contano (rumore)
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
