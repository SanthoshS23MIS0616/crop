import numpy as np

def parse_range(val):
    """Parse '25-35' into (25, 35) or single number."""
    if isinstance(val, str) and '-' in val:
        parts = val.split('-')
        try:
            return float(parts[0]), float(parts[1])
        except:
            return None, None
    try:
        v = float(val)
        return v, v
    except:
        return None, None

def range_midpoint(val):
    lo, hi = parse_range(val)
    if lo is not None and hi is not None:
        return (lo + hi) / 2
    return None

def climate_risk_score(actual_temp, actual_rainfall, ideal_temp_str, ideal_rainfall_str):
    """Calculate climate risk 0-1. Lower = safer."""
    ideal_temp_lo, ideal_temp_hi = parse_range(ideal_temp_str)
    ideal_rain_lo, ideal_rain_hi = parse_range(ideal_rainfall_str)

    if None in (ideal_temp_lo, ideal_temp_hi, ideal_rain_lo, ideal_rain_hi):
        return 0.5  # unknown

    # Temperature deviation
    if ideal_temp_lo <= actual_temp <= ideal_temp_hi:
        temp_dev = 0
    else:
        temp_dev = min(abs(actual_temp - ideal_temp_lo), abs(actual_temp - ideal_temp_hi))
    temp_risk = min(temp_dev / 15, 1.0)  # normalize, 15°C max deviation

    # Rainfall deviation
    ideal_rain_mid = (ideal_rain_lo + ideal_rain_hi) / 2
    rain_dev = abs(actual_rainfall - ideal_rain_mid)
    rain_range = (ideal_rain_hi - ideal_rain_lo) / 2
    rain_risk = min(rain_dev / max(ideal_rain_mid, 1), 1.0)

    risk = 0.5 * temp_risk + 0.5 * rain_risk
    return round(risk, 3)

def risk_label(score):
    if score < 0.3:
        return "Low"
    elif score < 0.6:
        return "Medium"
    else:
        return "High"

def sustainability_score(n, p, k, crop_n, crop_p, crop_k):
    """Check nutrient match — closer match = more sustainable."""
    try:
        cn, cp, ck = float(crop_n), float(crop_p), float(crop_k)
    except:
        return 0.5
    
    diff_n = abs(n - cn) / max(cn, 1)
    diff_p = abs(p - cp) / max(cp, 1)
    diff_k = abs(k - ck) / max(ck, 1)

    avg_diff = (diff_n + diff_p + diff_k) / 3
    score = max(0, 1 - avg_diff)
    return round(score, 3)

def sustainability_label(score):
    if score >= 0.7:
        return "Good"
    elif score >= 0.4:
        return "Moderate"
    else:
        return "Poor"
