import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import GridSearchCV, StratifiedKFold, KFold
from sklearn.metrics import classification_report, mean_squared_error, mean_absolute_error
from risk_dataset import generate_risk_dataset_from_market_data
import numpy as np

def train_and_save_risk_models():
    # 🔄 Carrega os dados com sinal e confiança simulados ou reais
    data = generate_risk_dataset_from_market_data()

    X_train = data["X_train"]
    X_test = data["X_test"]

    # Parâmetros comuns para GridSearchCV
    param_grid_clf = {
        'n_estimators': [50, 100, 200],
        'max_depth': [5, 10, 15, None],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4]
    }
    param_grid_reg = {
        'fit_intercept': [True, False]
    }

    cv_clf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_reg = KFold(n_splits=5, shuffle=True, random_state=42)

    # 🎯 Modelo 1: ação de risco (enter, reduce, avoid)
    print("🔧 Iniciando busca de hiperparâmetros para o modelo de ação de risco...")
    grid_search_action = GridSearchCV(
        estimator=RandomForestClassifier(random_state=42),
        param_grid=param_grid_clf,
        cv=cv_clf,
        scoring='f1_weighted',
        n_jobs=-1,
        verbose=1
    )
    grid_search_action.fit(X_train, data["y_action_train"])
    action_model = grid_search_action.best_estimator_
    print(f"✅ Melhores parâmetros (Ação): {grid_search_action.best_params_}")
    print(f"📈 Melhor score F1-weighted (Ação): {grid_search_action.best_score_:.4f}")
    y_pred_action = action_model.predict(X_test)
    print("📊 Modelo de Ação:")
    print(classification_report(data["y_action_test"], y_pred_action))
    joblib.dump(action_model, "models/risk_management/model/risk_action_model.pkl")

    # 🎯 Modelo 2: nível de risco (low, medium, high)
    print("🔧 Iniciando busca de hiperparâmetros para o modelo de nível de risco...")
    grid_search_risk = GridSearchCV(
        estimator=RandomForestClassifier(random_state=42, class_weight="balanced"),
        param_grid=param_grid_clf,
        cv=cv_clf,
        scoring='f1_weighted',
        n_jobs=-1,
        verbose=1
    )
    grid_search_risk.fit(X_train, data["y_risk_train"])
    risk_model = grid_search_risk.best_estimator_
    print(f"✅ Melhores parâmetros (Nível de Risco): {grid_search_risk.best_params_}")
    print(f"📈 Melhor score F1-weighted (Nível de Risco): {grid_search_risk.best_score_:.4f}")
    y_pred_risk = risk_model.predict(X_test)
    print("📊 Modelo de Nível de Risco:")
    print(classification_report(data["y_risk_test"], y_pred_risk))
    joblib.dump(risk_model, "models/risk_management/model/risk_level_model.pkl")

    # 🎯 Modelo 3: tamanho da posição
    print("🔧 Iniciando busca de hiperparâmetros para o modelo de tamanho da posição...")
    grid_search_pos = GridSearchCV(
        estimator=LinearRegression(),
        param_grid=param_grid_reg,
        cv=cv_reg,
        scoring='neg_mean_absolute_error',
        n_jobs=-1,
        verbose=1
    )
    y_pos_train_rounded = np.round(data["y_pos_train"], 3)
    grid_search_pos.fit(X_train, y_pos_train_rounded)
    position_model = grid_search_pos.best_estimator_
    print(f"✅ Melhores parâmetros (Tamanho da Posição): {grid_search_pos.best_params_}")
    print(f"📈 Melhor MAE (Tamanho da Posição): {-grid_search_pos.best_score_:.4f}")
    y_pred_pos = position_model.predict(X_test)
    print("📈 Erro médio (position_size):")
    print(mean_absolute_error(data["y_pos_test"], y_pred_pos))
    joblib.dump(position_model, "models/risk_management/model/position_size_model.pkl")

    # 🎯 Modelo 4: Stop Loss (%)
    print("🔧 Iniciando busca de hiperparâmetros para o modelo de Stop Loss...")
    grid_search_stop = GridSearchCV(
        estimator=LinearRegression(),
        param_grid=param_grid_reg,
        cv=cv_reg,
        scoring='neg_mean_absolute_error',
        n_jobs=-1,
        verbose=1
    )
    y_stop_train_rounded = np.round(data["y_stop_train"], 3)
    grid_search_stop.fit(X_train, y_stop_train_rounded)
    stop_model = grid_search_stop.best_estimator_
    print(f"✅ Melhores parâmetros (Stop Loss): {grid_search_stop.best_params_}")
    print(f"📈 Melhor MAE (Stop Loss): {-grid_search_stop.best_score_:.4f}")
    y_pred_sl = stop_model.predict(X_test)
    print("📈 Erro médio (stop_loss_pct):")
    print(mean_absolute_error(data["y_stop_test"], y_pred_sl))
    joblib.dump(stop_model, "models/risk_management/model/stop_loss_model.pkl")

    # 🎯 Modelo 5: Take Profit (%)
    print("🔧 Iniciando busca de hiperparâmetros para o modelo de Take Profit...")
    grid_search_tp = GridSearchCV(
        estimator=LinearRegression(),
        param_grid=param_grid_reg,
        cv=cv_reg,
        scoring='neg_mean_absolute_error',
        n_jobs=-1,
        verbose=1
    )
    y_tp_train_rounded = np.round(data["y_tp_train"], 3)
    grid_search_tp.fit(X_train, y_tp_train_rounded)
    tp_model = grid_search_tp.best_estimator_
    print(f"✅ Melhores parâmetros (Take Profit): {grid_search_tp.best_params_}")
    print(f"📈 Melhor MAE (Take Profit): {-grid_search_tp.best_score_:.4f}")
    y_pred_tp = tp_model.predict(X_test)
    print("📈 Erro médio (take_profit_pct):")
    print(mean_absolute_error(data["y_tp_test"], y_pred_tp))
    joblib.dump(tp_model, "models/risk_management/model/take_profit_model.pkl")

    print("✅ Modelos de gerenciamento de risco salvos com sucesso!")

if __name__ == "__main__":
    train_and_save_risk_models()
