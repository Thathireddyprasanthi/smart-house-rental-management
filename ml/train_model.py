import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import joblib

data = pd.read_csv("house_rent.csv")

le = LabelEncoder()

data["location"] = le.fit_transform(data["location"])

X = data[[
    "location",
    "bhk",
    "area",
    "furnished"
]]

y = data["rent"]

model = RandomForestRegressor(
    n_estimators=100,
    random_state=42
)

model.fit(X, y)

joblib.dump(model, "rent_model.pkl")
joblib.dump(le, "location_encoder.pkl")

print("Model Saved Successfully")