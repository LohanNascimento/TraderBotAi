import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.metrics import classification_report, confusion_matrix
from market_dataset import load_market_dataset


def train_market_model():
    # Carrega dados
    X_train, X_test, y_train, y_test, vol_train, vol_test = load_market_dataset()

    # Define o modelo base
    base_model = RandomForestClassifier(random_state=42, class_weight="balanced")

    # Define os parâmetros para o GridSearchCV
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [5, 10, 15, None],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4]
    }

    # Configura o StratifiedKFold para validação cruzada
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    # Configura o GridSearchCV
    grid_search = GridSearchCV(
        estimator=base_model,
        param_grid=param_grid,
        cv=cv,
        scoring='f1_weighted',  # Ou 'accuracy', 'roc_auc_ovr', etc.
        n_jobs=-1,  # Usa todos os cores disponíveis
        verbose=1
    )

    print("🔧 Iniciando busca de hiperparâmetros para o modelo de mercado...")
    grid_search.fit(X_train, y_train)

    model = grid_search.best_estimator_
    print(f"✅ Melhores parâmetros encontrados: {grid_search.best_params_}")
    print(f"📈 Melhor score F1-weighted: {grid_search.best_score_:.4f}")

    print("🔧 Treinando modelo final com os melhores parâmetros...")

    # Avalia geral
    y_pred = model.predict(X_test)
    print("\n📊 Classification Report (Geral):")
    print(classification_report(y_test, y_pred))
    print("🧱 Matriz de confusão:")
    print(confusion_matrix(y_test, y_pred))

    # Avalia apenas exemplos com alta volatilidade
    confidence_threshold = 0.005
    mask_confident = vol_test > confidence_threshold
    if mask_confident.sum() > 0:
        print(f"\n📊 Classification Report (volatility_score > {confidence_threshold}):")
        print(classification_report(y_test[mask_confident], y_pred[mask_confident]))
        print("🧱 Matriz de confusão (alta volatilidade):")
        print(confusion_matrix(y_test[mask_confident], y_pred[mask_confident]))
    else:
        print(f"\nNenhum exemplo com volatility_score > {confidence_threshold} no conjunto de teste.")

    # Salva modelo
    joblib.dump(model, "models/market_analysis/model/model_market.pkl")
    print("✅ Modelo salvo em: models/market_analysis/model/model_market.pkl")


if __name__ == "__main__":
    train_market_model()
