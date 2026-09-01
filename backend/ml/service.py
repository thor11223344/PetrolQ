import os
import json
import joblib
import pandas as pd
import numpy as np

class HazardPredictionService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HazardPredictionService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Loads artifacts into memory upon initialization."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        artifacts_dir = os.path.join(base_dir, 'artifacts')
        
        self.model = None
        self.explainer = None
        self.metadata = {}
        
        # Load Model
        model_path = os.path.join(artifacts_dir, 'lgbm_hazard_model.joblib')
        if os.path.exists(model_path):
            self.model = joblib.load(model_path)
            
        # Load Metadata
        meta_path = os.path.join(artifacts_dir, 'model_metadata.json')
        if os.path.exists(meta_path):
            with open(meta_path, 'r') as f:
                self.metadata = json.load(f)
                
        # Load SHAP Explainer
        shap_path = os.path.join(artifacts_dir, 'shap_explainer.joblib')
        if os.path.exists(shap_path):
            try:
                self.explainer = joblib.load(shap_path)
                
                # Warmup SHAP to prevent the first request from taking >1s and blocking websockets
                if self.model and self.metadata:
                    print("Warming up ML model and SHAP explainer...")
                    dummy_params = {'wob': 10, 'rpm': 100, 'rop': 20, 'torque': 10000, 'ecd': 1.1}
                    self.predict_risk(dummy_params, [])
                    print("Warmup complete.")
                    
            except Exception as e:
                print(f"Warning: Failed to load SHAP explainer: {e}")

    def calculate_mse(self, wob, rpm, rop, torque):
        """Simplistic Mechanical Specific Energy estimation."""
        if rop == 0: return 0.0
        # Generic fallback formulation for missing exact bit diameter
        return (wob * 1000) / 10.0 + (rpm * torque * 100) / (rop * 10.0)

    def calculate_d_xc(self, rop, rpm, wob, ecd):
        """Corrected d-exponent estimation."""
        if rpm == 0 or wob == 0: return 0.0
        # Guard against negative/zero logarithms
        if rop / (rpm * 60) <= 0 or wob / 1000.0 <= 0: return 0.0
        return (np.log(rop / (rpm * 60)) / np.log(wob / 1000.0)) * (9.0 / ecd) if ecd else 0.0

    def get_feature_description(self, feature_name, is_positive):
        """Generates human-readable descriptions for SHAP factors based on impact direction."""
        # A positive SHAP value implies the feature *increased* the hazard probability.
        # However, the physical reality is specific (e.g. high torque = bad, low ROP = bad).
        # We simplify to "Elevated/Reduced" for UI demonstrative purposes.
        direction = "Elevated" if is_positive else "Reduced"
        
        descriptions = {
            'torque': f"{direction} surface torque",
            'rop': f"{direction} rate of penetration",
            'wob': f"{direction} weight on bit",
            'rpm': f"{direction} rotary speed",
            'mud_weight': f"{direction} mud weight",
            'ecd': f"{direction} equivalent circulating density",
            'mse': f"{direction} mechanical specific energy",
            'd_xc': f"{direction} corrected d-exponent",
            'torque_roll_std_5': f"{direction} torque volatility",
            'rop_roll_mean_5': f"{direction} rolling rate of penetration",
        }
        
        return descriptions.get(feature_name, f"{direction} {feature_name.replace('_', ' ')}")

    def predict_risk(self, current_params: dict, history_params: list = None) -> dict:
        """
        Runs ML prediction and SHAP explainability on a single point in real-time.
        history_params is an optional list of recent param dicts to calculate rolling features.
        """
        if not self.model or not self.metadata:
            return {"error": "Model artifacts not loaded."}
            
        features_required = self.metadata.get("features", [])
        baselines = self.metadata.get("default_baselines", {})
        
        # 1. Parameter parsing
        wob = float(current_params.get('wob') if current_params.get('wob') is not None else baselines.get('wob', 0.0))
        rpm = float(current_params.get('rpm') if current_params.get('rpm') is not None else baselines.get('rpm', 0.0))
        rop = float(current_params.get('rop') if current_params.get('rop') is not None else baselines.get('rop', 0.0))
        torque = float(current_params.get('torque') if current_params.get('torque') is not None else baselines.get('torque', 0.0))
        ecd = float(current_params.get('ecd') if current_params.get('ecd') is not None else baselines.get('ecd', 0.0))
        
        # 2. On-the-fly derived metrics
        mse = self.calculate_mse(wob, rpm, rop, torque)
        d_xc = self.calculate_d_xc(rop, rpm, wob, ecd)
        
        current_params['mse'] = current_params.get('mse', mse)
        current_params['d_xc'] = current_params.get('d_xc', d_xc)
        
        # Calculate rolling metrics if history provided, else fallback to baseline
        if history_params and len(history_params) >= 4:
            history_rop = [float(h.get('rop', 0)) for h in history_params] + [rop]
            history_torque = [float(h.get('torque', 0)) for h in history_params] + [torque]
            
            current_params['rop_roll_mean_5'] = float(np.mean(history_rop[-5:]))
            current_params['torque_roll_std_5'] = float(np.std(history_torque[-5:]))
        
        # 3. Vectorize inputs
        input_data = {}
        for f in features_required:
            val = current_params.get(f)
            input_data[f] = [float(val) if val is not None else float(baselines.get(f, 0.0))]
            
        df_input = pd.DataFrame(input_data)
        
        # 4. Model Prediction
        risk_probability = float(self.model.predict_proba(df_input)[0, 1])
        
        # 5. Risk Level Assignment
        if risk_probability < 0.40:
            risk_level = "LOW"
        elif risk_probability <= 0.75:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
            
        # 6. Local SHAP Values Calculation
        top_shap_factors = []
        if self.explainer is not None:
            try:
                shap_values = self.explainer.shap_values(df_input)
                
                # Extract SHAP array for positive class (index 1)
                if isinstance(shap_values, list):
                    sv = shap_values[1][0]
                elif len(shap_values.shape) == 3:
                    sv = shap_values[0, :, 1]
                elif len(shap_values.shape) == 2:
                    sv = shap_values[0, :]
                else:
                    sv = shap_values
                        
                # Map values to features
                feature_impacts = []
                for i, feat_name in enumerate(features_required):
                    val = float(sv[i])
                    if abs(val) > 0.0001:
                        feature_impacts.append({
                            'feature': feat_name,
                            'impact': val,
                            'abs_impact': abs(val)
                        })
                        
                # Sort by absolute impact and take top 3
                feature_impacts.sort(key=lambda x: x['abs_impact'], reverse=True)
                
                for item in feature_impacts[:3]:
                    is_positive_impact = item['impact'] > 0
                    top_shap_factors.append({
                        'feature': item['feature'],
                        'impact': float(item['abs_impact']), # Return absolute impact value
                        'direction': 'INCREASES_RISK' if is_positive_impact else 'DECREASES_RISK'
                    })
            except Exception as e:
                print(f"SHAP local calculation failed: {e}")
                
        return {
            'risk_probability': risk_probability,
            'risk_level': risk_level,
            'top_factors': top_shap_factors
        }
