from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class Node:
    regime: int
    depth: int
    previous_position: float
    equity: float = 1.0
    peak: float = 1.0
    reward_from_parent: float = 0.0
    visits: int = 0
    value: float = 0.0
    children: dict[float, "Node"] = field(default_factory=dict)

    @property
    def average_value(self) -> float:
        return self.value / self.visits if self.visits else 0.0


@dataclass
class TemplateNode:
    regime: int
    depth: int
    previous_template: int
    equity: float = 1.0
    peak: float = 1.0
    reward_from_parent: float = 0.0
    visits: int = 0
    value: float = 0.0
    children: dict[int, "TemplateNode"] = field(default_factory=dict)

    @property
    def average_value(self) -> float:
        return self.value / self.visits if self.visits else 0.0


class MarketAttractorMCTS:
    def __init__(
        self,
        positions: list[float],
        horizon: int,
        simulations_per_day: int,
        exploration_constant: float,
        drawdown_penalty: float,
        transaction_cost_bps: float,
        seed: int,
        sampler: str = "path",
        use_full_action_grid: bool = False,
        prior_band: float = 0.25,
        opportunity_cost_weight: float = 0.2,
    ) -> None:
        self.positions = positions
        self.horizon = horizon
        self.simulations_per_day = simulations_per_day
        self.exploration_constant = exploration_constant
        self.drawdown_penalty = drawdown_penalty
        self.transaction_cost = transaction_cost_bps / 10_000.0
        self.sampler = sampler
        self.use_full_action_grid = use_full_action_grid
        self.prior_band = prior_band
        self.opportunity_cost_weight = opportunity_cost_weight
        self.rng = np.random.default_rng(seed)
        self.transition_matrix: np.ndarray | None = None
        self.regime_returns: dict[int, np.ndarray] = {}
        self.regime_paths: dict[int, np.ndarray] = {}
        self.regime_next_20d: dict[int, float] = {}
        self.regimes: list[int] = []

    def fit(self, spy_returns: pd.Series, regimes: pd.Series) -> None:
        aligned = pd.concat(
            {"returns": spy_returns, "regime": regimes},
            axis=1,
        ).dropna()
        aligned["regime"] = aligned["regime"].astype(int)
        self.regimes = sorted(aligned["regime"].unique().tolist())
        regime_to_idx = {regime: idx for idx, regime in enumerate(self.regimes)}

        matrix = np.ones((len(self.regimes), len(self.regimes)))
        regime_values = aligned["regime"].to_numpy()
        for current_regime, next_regime in zip(regime_values[:-1], regime_values[1:]):
            matrix[regime_to_idx[current_regime], regime_to_idx[next_regime]] += 1.0
        self.transition_matrix = matrix / matrix.sum(axis=1, keepdims=True)

        for regime in self.regimes:
            samples = aligned.loc[aligned["regime"] == regime, "returns"].dropna().to_numpy()
            self.regime_returns[regime] = samples if len(samples) else np.array([0.0])

        path_frame = pd.concat(
            {
                step: spy_returns.shift(-step)
                for step in range(1, self.horizon + 1)
            },
            axis=1,
        )
        path_frame.columns = [f"step_{step}" for step in range(1, self.horizon + 1)]
        path_frame["regime"] = regimes
        path_frame = path_frame.dropna()
        path_frame["regime"] = path_frame["regime"].astype(int)
        for regime in self.regimes:
            paths = path_frame.loc[path_frame["regime"] == regime].drop(columns="regime").to_numpy()
            if len(paths):
                self.regime_paths[regime] = paths

        next_20d_paths = pd.concat(
            {step: spy_returns.shift(-step) for step in range(1, 21)},
            axis=1,
        )
        next_20d = (1.0 + next_20d_paths).prod(axis=1) - 1.0
        next_20d = next_20d.where(next_20d_paths.notna().all(axis=1))
        forward = pd.concat({"next_20d": next_20d, "regime": regimes}, axis=1).dropna()
        forward["regime"] = forward["regime"].astype(int)
        self.regime_next_20d = forward.groupby("regime")["next_20d"].mean().to_dict()

    def choose_position(
        self,
        current_regime: int,
        previous_position: float,
        prior_position: float | None = None,
    ) -> float:
        root = Node(regime=int(current_regime), depth=0, previous_position=previous_position)
        actions = self._candidate_actions(prior_position)
        for _ in range(self.simulations_per_day):
            path = [root]
            node = root
            reward_so_far = 0.0
            sampled_path = self._sample_return_path(root.regime)

            while node.depth < self.horizon and len(node.children) == len(actions):
                node = self._select_child(node)
                path.append(node)
                reward_so_far += node.reward_from_parent

            if node.depth < self.horizon:
                untried = [position for position in actions if position not in node.children]
                action = float(self.rng.choice(untried))
                next_node, step_reward = self._advance(node, action, sampled_path)
                node.children[action] = next_node
                node = next_node
                path.append(node)
                reward = reward_so_far + step_reward + self._rollout(node, actions, sampled_path)
            else:
                reward = reward_so_far

            for visited in path:
                visited.visits += 1
                visited.value += reward

        if not root.children:
            return previous_position
        return max(root.children.items(), key=lambda item: item[1].average_value)[0]

    def choose_position_with_diagnostics(
        self,
        current_regime: int,
        previous_position: float,
        prior_position: float | None = None,
    ) -> tuple[float, dict[str, float | int | None]]:
        position, root = self._search_root(current_regime, previous_position, prior_position)
        row: dict[str, float | int | None] = {
            "regime": int(current_regime),
            "prior_position": prior_position,
            "chosen_position": position,
        }
        for level in self.positions:
            child = root.children.get(level)
            suffix = int(level * 100)
            row[f"value_{suffix}"] = None if child is None or child.visits == 0 else child.average_value
            row[f"visits_{suffix}"] = 0 if child is None else int(child.visits)
        return position, row

    def _search_root(
        self,
        current_regime: int,
        previous_position: float,
        prior_position: float | None = None,
    ) -> tuple[float, Node]:
        root = Node(regime=int(current_regime), depth=0, previous_position=previous_position)
        actions = self._candidate_actions(prior_position)
        for _ in range(self.simulations_per_day):
            path = [root]
            node = root
            reward_so_far = 0.0
            sampled_path = self._sample_return_path(root.regime)

            while node.depth < self.horizon and len(node.children) == len(actions):
                node = self._select_child(node)
                path.append(node)
                reward_so_far += node.reward_from_parent

            if node.depth < self.horizon:
                untried = [position for position in actions if position not in node.children]
                action = float(self.rng.choice(untried))
                next_node, step_reward = self._advance(node, action, sampled_path)
                node.children[action] = next_node
                node = next_node
                path.append(node)
                reward = reward_so_far + step_reward + self._rollout(node, actions, sampled_path)
            else:
                reward = reward_so_far

            for visited in path:
                visited.visits += 1
                visited.value += reward

        if not root.children:
            return previous_position, root
        return max(root.children.items(), key=lambda item: item[1].average_value)[0], root

    def _select_child(self, node: Node) -> Node:
        log_parent = np.log(max(node.visits, 1))

        def uct(child: Node) -> float:
            exploration = self.exploration_constant * np.sqrt(log_parent / max(child.visits, 1))
            return child.average_value + exploration

        return max(node.children.values(), key=uct)

    def _advance(
        self,
        node: Node,
        position: float,
        sampled_path: np.ndarray | None = None,
    ) -> tuple[Node, float]:
        next_regime = node.regime if self.sampler == "path" else self._sample_next_regime(node.regime)
        asset_return = self._sample_return(next_regime, node.depth, sampled_path)
        cost = abs(position - node.previous_position) * self.transaction_cost
        simple_reward = position * asset_return - cost
        equity = node.equity * (1.0 + simple_reward)
        peak = max(node.peak, equity)
        drawdown = min(0.0, equity / peak - 1.0)
        opportunity_cost = self._opportunity_cost(node.regime, position)
        reward = simple_reward - self.drawdown_penalty * abs(drawdown) - opportunity_cost
        return (
            Node(
                regime=next_regime,
                depth=node.depth + 1,
                previous_position=position,
                equity=equity,
                peak=peak,
                reward_from_parent=reward,
            ),
            reward,
        )

    def _rollout(
        self,
        node: Node,
        actions: list[float],
        sampled_path: np.ndarray | None = None,
    ) -> float:
        total_reward = 0.0
        rollout_node = node
        while rollout_node.depth < self.horizon:
            action = self._guided_action(rollout_node.regime, actions)
            rollout_node, reward = self._advance(rollout_node, action, sampled_path)
            total_reward += reward
        return total_reward

    def _guided_action(self, regime: int, actions: list[float]) -> float:
        samples = self.regime_returns.get(regime, np.array([0.0]))
        mean_return = float(np.mean(samples))
        if mean_return <= 0:
            return min(actions)
        if mean_return >= np.quantile([np.mean(v) for v in self.regime_returns.values()], 0.75):
            return max(actions)
        return float(self.rng.choice(actions))

    def _sample_next_regime(self, regime: int) -> int:
        if self.transition_matrix is None:
            return regime
        if regime not in self.regimes:
            return int(self.rng.choice(self.regimes))
        idx = self.regimes.index(regime)
        return int(self.rng.choice(self.regimes, p=self.transition_matrix[idx]))

    def _sample_return(
        self,
        regime: int,
        depth: int = 0,
        sampled_path: np.ndarray | None = None,
    ) -> float:
        if self.sampler == "path" and sampled_path is not None and depth < len(sampled_path):
            return float(sampled_path[depth])
        samples = self.regime_returns.get(regime, np.array([0.0]))
        return float(self.rng.choice(samples))

    def _sample_return_path(self, regime: int) -> np.ndarray | None:
        if self.sampler != "path":
            return None
        paths = self.regime_paths.get(regime)
        if paths is None or len(paths) == 0:
            return None
        return paths[int(self.rng.integers(0, len(paths)))]

    def _candidate_actions(self, prior_position: float | None) -> list[float]:
        if self.use_full_action_grid or prior_position is None:
            return self.positions
        lower = prior_position - self.prior_band
        upper = prior_position + self.prior_band
        actions = [position for position in self.positions if lower <= position <= upper]
        return actions or self.positions

    def _opportunity_cost(self, regime: int, position: float) -> float:
        next_20d = max(0.0, float(self.regime_next_20d.get(regime, 0.0)))
        return (1.0 - position) * next_20d * self.opportunity_cost_weight / 20.0


def build_mcts_weights(
    prices: pd.DataFrame,
    regimes: pd.DataFrame,
    config: dict,
    method: str = "hmm_regime",
    prior_weights: pd.DataFrame | None = None,
    root_values_path: str | Path | None = None,
) -> pd.DataFrame:
    mcts_config = config["mcts"]
    model = MarketAttractorMCTS(
        positions=[float(x) for x in mcts_config["positions"]],
        horizon=int(mcts_config["horizon"]),
        simulations_per_day=int(mcts_config["simulations_per_day"]),
        exploration_constant=float(mcts_config["exploration_constant"]),
        drawdown_penalty=float(mcts_config["drawdown_penalty"]),
        transaction_cost_bps=float(mcts_config["transaction_cost_bps"]),
        seed=int(config["project"]["seed"]),
        sampler=str(mcts_config.get("sampler", "path")),
        use_full_action_grid=bool(mcts_config.get("use_full_action_grid", False)),
        prior_band=float(mcts_config.get("prior_band", 0.25)),
        opportunity_cost_weight=float(mcts_config.get("opportunity_cost_weight", 0.2)),
    )

    spy_returns = prices[mcts_config["asset"]].pct_change(fill_method=None)
    labels = regimes[method].reindex(prices.index).ffill()
    model.fit(spy_returns, labels)

    weights = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    prior_positions = None
    if prior_weights is not None and mcts_config["asset"] in prior_weights:
        prior_positions = prior_weights[mcts_config["asset"]].reindex(prices.index).ffill().fillna(0.0)

    previous_position = 0.0
    root_value_rows = []
    for date, regime in labels.dropna().items():
        prior_position = None if prior_positions is None else float(prior_positions.loc[date])
        if root_values_path is None:
            position = model.choose_position(int(regime), previous_position, prior_position)
        else:
            position, diagnostics = model.choose_position_with_diagnostics(
                int(regime),
                previous_position,
                prior_position,
            )
            diagnostics["date"] = date
            root_value_rows.append(diagnostics)
        weights.loc[date, mcts_config["asset"]] = position
        previous_position = position

    if root_values_path is not None:
        root_values = pd.DataFrame(root_value_rows)
        first_cols = ["date", "regime", "prior_position", "chosen_position"]
        suffixes = [int(position * 100) for position in model.positions]
        value_cols = [f"value_{suffix}" for suffix in suffixes]
        visit_cols = [f"visits_{suffix}" for suffix in suffixes]
        root_values = root_values[first_cols + value_cols + visit_cols]
        root_values.to_csv(root_values_path, index=False)

    return weights.ffill().fillna(0.0)


class MarketAttractorMultiAssetMCTS:
    def __init__(
        self,
        templates: list[dict[str, float]],
        horizon: int,
        simulations_per_day: int,
        exploration_constant: float,
        drawdown_penalty: float,
        transaction_cost_bps: float,
        seed: int,
    ) -> None:
        self.templates = templates
        self.actions = list(range(len(templates)))
        self.horizon = horizon
        self.simulations_per_day = simulations_per_day
        self.exploration_constant = exploration_constant
        self.drawdown_penalty = drawdown_penalty
        self.transaction_cost = transaction_cost_bps / 10_000.0
        self.rng = np.random.default_rng(seed)
        self.assets = sorted({asset for template in templates for asset in template})
        self.regime_paths: dict[int, np.ndarray] = {}
        self.regimes: list[int] = []

    def fit(self, asset_returns: pd.DataFrame, regimes: pd.Series) -> None:
        aligned = pd.concat([asset_returns, regimes.rename("regime")], axis=1).dropna()
        aligned["regime"] = aligned["regime"].astype(int)
        self.regimes = sorted(aligned["regime"].unique().tolist())

        path_parts = []
        for step in range(1, self.horizon + 1):
            shifted = asset_returns[self.assets].shift(-step)
            shifted.columns = pd.MultiIndex.from_product([[step], shifted.columns])
            path_parts.append(shifted)
        path_frame = pd.concat(path_parts, axis=1)
        path_frame["regime"] = regimes
        path_frame = path_frame.dropna()
        path_frame["regime"] = path_frame["regime"].astype(int)

        for regime in self.regimes:
            regime_frame = path_frame.loc[path_frame["regime"] == regime].drop(columns="regime")
            if len(regime_frame):
                self.regime_paths[regime] = regime_frame.to_numpy().reshape(
                    len(regime_frame),
                    self.horizon,
                    len(self.assets),
                )

    def choose_template(self, current_regime: int, previous_template: int) -> int:
        root = TemplateNode(
            regime=int(current_regime),
            depth=0,
            previous_template=previous_template,
        )
        for _ in range(self.simulations_per_day):
            path = [root]
            node = root
            reward_so_far = 0.0
            sampled_path = self._sample_return_path(root.regime)

            while node.depth < self.horizon and len(node.children) == len(self.actions):
                node = self._select_child(node)
                path.append(node)
                reward_so_far += node.reward_from_parent

            if node.depth < self.horizon:
                untried = [action for action in self.actions if action not in node.children]
                action = int(self.rng.choice(untried))
                next_node, step_reward = self._advance(node, action, sampled_path)
                node.children[action] = next_node
                node = next_node
                path.append(node)
                reward = reward_so_far + step_reward + self._rollout(node, sampled_path)
            else:
                reward = reward_so_far

            for visited in path:
                visited.visits += 1
                visited.value += reward

        if not root.children:
            return previous_template
        return max(root.children.items(), key=lambda item: item[1].average_value)[0]

    def _select_child(self, node: TemplateNode) -> TemplateNode:
        log_parent = np.log(max(node.visits, 1))

        def uct(child: TemplateNode) -> float:
            exploration = self.exploration_constant * np.sqrt(log_parent / max(child.visits, 1))
            return child.average_value + exploration

        return max(node.children.values(), key=uct)

    def _advance(
        self,
        node: TemplateNode,
        action: int,
        sampled_path: np.ndarray | None,
    ) -> tuple[TemplateNode, float]:
        asset_returns = self._sample_asset_returns(node.depth, sampled_path)
        current_weights = self._template_vector(action)
        previous_weights = self._template_vector(node.previous_template)
        portfolio_return = float(current_weights @ asset_returns)
        turnover = float(np.abs(current_weights - previous_weights).sum())
        cost = turnover * self.transaction_cost
        simple_reward = portfolio_return - cost
        equity = node.equity * (1.0 + simple_reward)
        peak = max(node.peak, equity)
        drawdown = min(0.0, equity / peak - 1.0)
        reward = simple_reward - self.drawdown_penalty * abs(drawdown)
        return (
            TemplateNode(
                regime=node.regime,
                depth=node.depth + 1,
                previous_template=action,
                equity=equity,
                peak=peak,
                reward_from_parent=reward,
            ),
            reward,
        )

    def _rollout(self, node: TemplateNode, sampled_path: np.ndarray | None) -> float:
        total_reward = 0.0
        rollout_node = node
        while rollout_node.depth < self.horizon:
            action = int(self.rng.choice(self.actions))
            rollout_node, reward = self._advance(rollout_node, action, sampled_path)
            total_reward += reward
        return total_reward

    def _sample_return_path(self, regime: int) -> np.ndarray | None:
        paths = self.regime_paths.get(regime)
        if paths is None or len(paths) == 0:
            return None
        return paths[int(self.rng.integers(0, len(paths)))]

    def _sample_asset_returns(self, depth: int, sampled_path: np.ndarray | None) -> np.ndarray:
        if sampled_path is not None and depth < len(sampled_path):
            return sampled_path[depth]
        return np.zeros(len(self.assets))

    def _template_vector(self, action: int) -> np.ndarray:
        template = self.templates[action]
        return np.array([template.get(asset, 0.0) for asset in self.assets], dtype=float)


def default_multi_asset_templates() -> list[dict[str, float]]:
    return [
        {"SPY": 1.0},
        {"SPY": 0.75, "TLT": 0.25},
        {"SPY": 0.50, "TLT": 0.25, "GLD": 0.25},
        {"TLT": 0.50, "GLD": 0.50},
        {},
    ]


def build_multi_asset_mcts_weights(
    prices: pd.DataFrame,
    regimes: pd.DataFrame,
    config: dict,
    method: str = "hmm_regime",
) -> pd.DataFrame:
    mcts_config = config["mcts"]
    templates = default_multi_asset_templates()
    model = MarketAttractorMultiAssetMCTS(
        templates=templates,
        horizon=int(mcts_config["horizon"]),
        simulations_per_day=int(mcts_config["simulations_per_day"]),
        exploration_constant=float(mcts_config["exploration_constant"]),
        drawdown_penalty=float(mcts_config.get("drawdown_penalty", 0.1)),
        transaction_cost_bps=float(mcts_config["transaction_cost_bps"]),
        seed=int(config["project"]["seed"]) + 17,
    )

    labels = regimes[method].reindex(prices.index).ffill()
    asset_returns = prices[["SPY", "TLT", "GLD"]].pct_change(fill_method=None)
    model.fit(asset_returns, labels)

    weights = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    previous_template = len(templates) - 1
    for date, regime in labels.dropna().items():
        template_id = model.choose_template(int(regime), previous_template)
        for asset, weight in templates[template_id].items():
            weights.loc[date, asset] = weight
        previous_template = template_id

    return weights.ffill().fillna(0.0)
