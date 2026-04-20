# model_pipeline.py

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from config import get_all_features


def get_model_config():
    """Return Random Forest model configuration."""
    return RandomForestClassifier(
        n_estimators=300, 
        max_depth=12, 
        class_weight='balanced',
        n_jobs=-1, 
        random_state=0
    )


def build_pipeline(model=None):
    """
    Build a complete preprocessing + classification pipeline.
    
    Args:
        model: Scikit-learn classifier instance (uses Random Forest if None)
        
    Returns:
        Pipeline object
    """
    if model is None:
        model = get_model_config()
        
    num_feats, cat_feats = get_all_features()

    numeric_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
    ])
    
    categorical_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False)),
    ])

    preprocessor = ColumnTransformer([
        ('num', numeric_transformer, num_feats),
        ('cat', categorical_transformer, cat_feats),
    ])

    return Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', model),
    ])


def get_feature_names(pipe):
    """
    Extract feature names after preprocessing.
    
    Args:
        pipe: Fitted pipeline
        
    Returns:
        list: Feature names including one-hot encoded categories
    """
    ct = pipe.named_steps['preprocessor']
    num_feats, cat_feats = get_all_features()
    
    ohe_feats = (ct.named_transformers_['cat']
                   .named_steps['encoder']
                   .get_feature_names_out(cat_feats)).tolist()
                   
    return num_feats + ohe_feats