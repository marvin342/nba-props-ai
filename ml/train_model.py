import pandas as pd
import joblib
from sklearn.ensemble import GradientBoostingRegressor

# Load logged results
df = pd.read_csv("../results_log.csv")

# Drop rows without final result
df = df[df["Result"].notna()]

# Features
X = df[[
    "ProjPts",
    "ProbOver",
    "Edge"
]]

# Target (actual points must be filled later)
y = df["ActualPts"]

# Train model
model = GradientBoostingRegressor(
    n_estimators=200,
    learning_rate=0.05,
    max_depth=3,
    random_state=42
)

model.fit(X, y)

# Save model
joblib.dump(model, "model.pkl")

print("Model trained and saved.")
