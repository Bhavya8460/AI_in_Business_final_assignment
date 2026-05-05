"""Live agent-status panel."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import streamlit as st

from ui.components import render_agent_card


@dataclass
class ProgressPanel:
    agent_ids: list[str]
    placeholders: dict = field(default_factory=dict)
    statuses: dict[str, str] = field(default_factory=dict)
    details: dict[str, str] = field(default_factory=dict)

    def render_initial(self) -> None:
        cols = st.columns(len(self.agent_ids)) if self.agent_ids else []
        for col, agent_id in zip(cols, self.agent_ids):
            with col:
                ph = st.empty()
                self.placeholders[agent_id] = ph
                self.statuses[agent_id] = "pending"
                self.details[agent_id] = ""
                with ph:
                    render_agent_card(agent_id, "pending", "")

    def update(self, agent_id: str, status: str, detail: str = "") -> None:
        if agent_id not in self.placeholders:
            return
        self.statuses[agent_id] = status
        self.details[agent_id] = detail
        with self.placeholders[agent_id]:
            render_agent_card(agent_id, status, detail)


def make_panel(agent_ids: Iterable[str]) -> ProgressPanel:
    panel = ProgressPanel(list(agent_ids))
    panel.render_initial()
    return panel
