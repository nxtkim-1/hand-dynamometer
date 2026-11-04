"""
train_quality.py - Train and evaluate the trial-quality classifier.
"""

import random

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (ConfusionMatrixDisplay, accuracy_score,
                             classification_report)
from sklearn.model_selection import train_test_split

import fake_data
import filters
import quality

def make_dataset(n_per_kind=500, seed=0):
    random.seed(seed)
    rows = []
    for kind in fake_data.TRIAL_KINDS:
        for _ in range(n_per_kind):
            peak = random.uniform(20, 50)            # many different people
            readings = fake_data.lines_to_readings(fake_data.generate_curve(peak, kind))
            smooth = filters.filter_readings(readings)
            features = quality.extract_features(smooth)
            features["label"] = kind
            rows.append(features)
    return pd.DataFrame(rows)

if __name__ == "__main__":
    df = make_dataset()
    print(f"Dataset: {len(df)} curves")
    print(df.groupby("label")[quality.FEATURE_NAMES].mean().round(2), "\n")
    
    X = df[quality.FEATURE_NAMES]
    y = df["label"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=0)

    model = RandomForestClassifier(n_estimators=200, random_state=0)
    model.fit(X_train, y_train)

    ml_pred = model.predict(X_test)
    rule_pred = [quality.rule_check(row) for row in X_test.to_dict("records")]

    print(f"Rule-based accuracy:    {accuracy_score(y_test, rule_pred):.3f}")
    print(f"Random Forest accuracy: {accuracy_score(y_test, ml_pred):.3f}\n")
    print(classification_report(y_test, ml_pred))
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    ConfusionMatrixDisplay.from_predictions(y_test, ml_pred, ax=ax1, colorbar=False)
    ax1.set_title("Random Forest - test set")
    importance = pd.Series(model.feature_importances_, index=quality.FEATURE_NAMES)
    importance.sort_values().plot.barh(ax=ax2)
    ax2.set_title("Feature importance")
    plt.tight_layout()
    fig.savefig("images/quality_model.png")

    quality.MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(model, quality.MODEL_PATH)
    print(f"Saved model to {quality.MODEL_PATH.name}")
    plt.show()