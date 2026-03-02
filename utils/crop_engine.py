import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import MinMaxScaler
from utils.risk_calculator import (
    parse_range, range_midpoint, climate_risk_score, risk_label,
    sustainability_score, sustainability_label
)

class CropEngine:
    def __init__(self, csv_path="data/crop_data.csv"):
        self.df = pd.read_csv(csv_path)
        self._prepare_data()
        self._train_models()

    def _prepare_data(self):
        """Parse range columns into midpoints for training."""
        df = self.df.copy()
        
        # Parse numeric midpoints
        numeric_cols = {
            'N': 'N (kg/ha)', 'P': 'P (kg/ha)', 'K': 'K (kg/ha)',
            'pH': 'pH', 'Temp': 'Temperature (°C)', 'Humidity': 'Humidity (%)',
            'Rainfall': 'Rainfall (mm)', 'Yield': 'Yield (tons/ha)',
            'Price': 'Price_per_ton (Rs)', 'IdealTemp': 'Ideal_Temp (°C)',
            'IdealRainfall': 'Ideal_Rainfall (mm)'
        }

        self.parsed = pd.DataFrame()
        self.parsed['Crop'] = df['Crop']

        for key, col in numeric_cols.items():
            self.parsed[key] = df[col].apply(lambda x: range_midpoint(str(x)))

        # Store raw strings for risk calc
        self.parsed['IdealTemp_raw'] = df['Ideal_Temp (°C)']
        self.parsed['IdealRainfall_raw'] = df['Ideal_Rainfall (mm)']
        self.parsed['N_raw'] = df['N (kg/ha)']
        self.parsed['P_raw'] = df['P (kg/ha)']
        self.parsed['K_raw'] = df['K (kg/ha)']

        # Drop rows where key values are None (Controlled/NA entries)
        self.valid = self.parsed.dropna(subset=['N', 'P', 'K', 'pH', 'Temp', 'Humidity', 'Rainfall', 'Yield']).copy()
        self.valid.reset_index(drop=True, inplace=True)

    def _train_models(self):
        """Train Random Forest Classifier (crop) and Regressor (yield)."""
        features = ['N', 'P', 'K', 'pH', 'Temp', 'Humidity', 'Rainfall']
        X = self.valid[features].values
        
        # Crop labels
        self.crop_labels = self.valid['Crop'].values
        
        # Scaler
        self.scaler = MinMaxScaler()
        X_scaled = self.scaler.fit_transform(X)

        # --- Classifier: predict crop ---
        self.clf = RandomForestClassifier(n_estimators=100, random_state=42)
        self.clf.fit(X_scaled, self.crop_labels)

        # --- Regressor: predict yield ---
        y_yield = self.valid['Yield'].values
        self.reg = RandomForestRegressor(n_estimators=100, random_state=42)
        self.reg.fit(X_scaled, y_yield)

        self.feature_names = features

    def predict(self, n, p, k, ph, temp, humidity, rainfall, area):
        """Full prediction pipeline."""
        input_arr = np.array([[n, p, k, ph, temp, humidity, rainfall]])
        input_scaled = self.scaler.transform(input_arr)

        # 1. Crop recommendation - top 3 with probabilities
        proba = self.clf.predict_proba(input_scaled)[0]
        classes = self.clf.classes_
        top_indices = np.argsort(proba)[::-1][:3]

        results = []
        for idx in top_indices:
            crop_name = classes[idx]
            probability = round(proba[idx] * 100, 1)

            # Get crop data row
            crop_row = self.valid[self.valid['Crop'] == crop_name].iloc[0]

            # 2. Yield prediction
            crop_features = np.array([[
                crop_row['N'], crop_row['P'], crop_row['K'],
                crop_row['pH'], temp, humidity, rainfall
            ]])
            crop_scaled = self.scaler.transform(crop_features)
            predicted_yield = self.reg.predict(crop_scaled)[0]
            
            # Confidence interval (±std from tree predictions)
            tree_preds = np.array([t.predict(crop_scaled)[0] for t in self.reg.estimators_])
            yield_std = np.std(tree_preds)
            yield_lower = max(0, predicted_yield - 1.96 * yield_std)
            yield_upper = predicted_yield + 1.96 * yield_std

            # 3. Total yield
            total_yield = predicted_yield * area

            # 4. Profit
            price = crop_row['Price'] if crop_row['Price'] else 0
            profit = total_yield * price

            # 5. Climate risk
            risk = climate_risk_score(
                temp, rainfall,
                str(crop_row['IdealTemp_raw']),
                str(crop_row['IdealRainfall_raw'])
            )

            # 6. Sustainability
            sust = sustainability_score(
                n, p, k,
                crop_row['N'], crop_row['P'], crop_row['K']
            )

            # 7. Multi-objective optimization score
            # Normalize yield (0-1)
            max_yield = self.valid['Yield'].max()
            yield_score = predicted_yield / max_yield if max_yield > 0 else 0

            # Normalize profit (0-1)
            max_possible_profit = self.valid['Yield'].max() * area * self.valid['Price'].max()
            profit_score = profit / max_possible_profit if max_possible_profit > 0 else 0

            risk_score_inv = 1 - risk  # lower risk = better
            sust_score = sust

            final_score = (
                0.4 * yield_score +
                0.3 * profit_score +
                0.2 * risk_score_inv +
                0.1 * sust_score
            )

            results.append({
                "crop": crop_name,
                "probability": probability,
                "yield_per_ha": round(predicted_yield, 2),
                "yield_lower": round(yield_lower, 2),
                "yield_upper": round(yield_upper, 2),
                "total_yield": round(total_yield, 2),
                "price_per_ton": int(price),
                "profit": int(profit),
                "risk": round(risk, 3),
                "risk_label": risk_label(risk),
                "sustainability": round(sust, 3),
                "sustainability_label": sustainability_label(sust),
                "final_score": round(final_score, 3),
                "yield_score": round(yield_score, 3),
                "profit_score": round(profit_score, 3),
            })

        # Sort by final_score descending
        results.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Mark best
        best_crop = results[0]['crop']

        return {
            "results": results,
            "best_crop": best_crop,
            "input": {
                "n": n, "p": p, "k": k, "ph": ph,
                "temp": temp, "humidity": humidity,
                "rainfall": rainfall, "area": area
            }
        }
