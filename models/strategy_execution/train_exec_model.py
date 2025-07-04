import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from exec_dataset import generate_exec_dataset_from_market
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
import joblib

def train_and_save_exec_model():
    # 🔄 Carrega os dados reais ou simulados com base no .parquet
    data = generate_exec_dataset_from_market()

    X = data["X"]
    y = data["y"]
    label_map = data["label_map"]  # Opcional, pode ser salvo também

    # 🧪 Divide treino e teste
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Parâmetros para GridSearchCV
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [5, 10, 15, None],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4]
    }

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    # 🎯 Treina o modelo de execução com GridSearchCV
    print("🔧 Iniciando busca de hiperparâmetros para o modelo de execução...")
    grid_search_exec = GridSearchCV(
        estimator=RandomForestClassifier(random_state=42),
        param_grid=param_grid,
        cv=cv,
        scoring='f1_weighted',
        n_jobs=-1,
        verbose=1
    )
    grid_search_exec.fit(X_train, y_train)
    exec_model = grid_search_exec.best_estimator_
    print(f"✅ Melhores parâmetros (Execução): {grid_search_exec.best_params_}")
    print(f"📈 Melhor score F1-weighted (Execução): {grid_search_exec.best_score_:.4f}")

    # 💾 Salva o modelo
    joblib.dump(exec_model, "models/strategy_execution/model/exec_model.pkl")

    # 📊 Avaliação
    print("\n✅ Modelo de EXECUÇÃO treinado")
    print(classification_report(y_test, exec_model.predict(X_test), zero_division=0))

    # 🔖 (Opcional) Salvar o dicionário de rótulos para decodificação posterior
    joblib.dump(label_map, "models/strategy_execution/model/exec_label_map.pkl")

if __name__ == "__main__":
    train_and_save_exec_model()

