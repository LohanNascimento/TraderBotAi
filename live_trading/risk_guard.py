import json
import os

class RiskGuard:
    def __init__(self, initial_capital, max_drawdown=0.25, max_consecutive_losses=3, cooldown_steps=3):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.drawdown = 0.0
        self.recent_losses = 0
        self.max_consecutive_losses = max_consecutive_losses
        self.max_drawdown = max_drawdown
        self.cooldown_active = False
        self.cooldown_counter = 0
        self.cooldown_steps = cooldown_steps

    def update_after_trade(self, profit_pct):
        """Atualiza estado após uma operação"""
        self.capital *= (1 + profit_pct)
        self.drawdown = 1 - (self.capital / self.initial_capital)

        if profit_pct < 0:
            self.recent_losses += 1
            self.cooldown_active = True
            self.cooldown_counter = 0
        else:
            self.recent_losses = 0
            self.cooldown_active = False
            self.cooldown_counter = 0

    def is_blocked(self):
        """Verifica se o robô deve ser bloqueado"""
        if self.drawdown > self.max_drawdown:
            return "drawdown_exceeded"
        if self.recent_losses >= self.max_consecutive_losses:
            return "too_many_losses"
        return None

    def check_cooldown(self):
        """Verifica e atualiza cooldown"""
        if self.cooldown_active:
            self.cooldown_counter += 1
            if self.cooldown_counter >= self.cooldown_steps:
                self.cooldown_active = False
                self.cooldown_counter = 0
            return True
        return False

    def reset(self):
        self.capital = self.initial_capital
        self.drawdown = 0
        self.recent_losses = 0
        self.cooldown_active = False
        self.cooldown_counter = 0

    def save(self, path="risk_state.json"):
        state = {
            "initial_capital": self.initial_capital,
            "capital": self.capital,
            "drawdown": self.drawdown,
            "recent_losses": self.recent_losses,
            "max_consecutive_losses": self.max_consecutive_losses,
            "max_drawdown": self.max_drawdown,
            "cooldown_active": self.cooldown_active,
            "cooldown_counter": self.cooldown_counter,
            "cooldown_steps": self.cooldown_steps
        }
        with open(path, "w") as f:
            json.dump(state, f)

    @classmethod
    def load(cls, path="risk_state.json"):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Nenhum estado salvo encontrado em {path}")

        with open(path, "r") as f:
            state = json.load(f)

        guard = cls(
            initial_capital=state["initial_capital"],
            max_drawdown=state["max_drawdown"],
            max_consecutive_losses=state["max_consecutive_losses"],
            cooldown_steps=state["cooldown_steps"]
        )
        guard.capital = state["capital"]
        guard.drawdown = state["drawdown"]
        guard.recent_losses = state["recent_losses"]
        guard.cooldown_active = state["cooldown_active"]
        guard.cooldown_counter = state["cooldown_counter"]
        return guard
