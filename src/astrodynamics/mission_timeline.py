"""
Flight 14 Canonical Mission Timeline & State Integration
========================================================
Manages the reconstructed mission sequence for Starship Flight 14,
integrating Phase 3/4 SECO burnout states into Phase 5 orbital propagation,
payload deployment, and early deorbit disposal scenarios.
"""

import csv
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import numpy as np

from .time_systems import DEFAULT_MISSION_EPOCH, parse_iso_epoch, format_iso_epoch
from .state import OrbitalState


@dataclass
class MissionEvent:
    event_id: str
    event_name: str
    t_plus_s: float
    utc_epoch: Optional[datetime]
    category: str  # 'ACTUAL', 'PLANNED', 'SYNTHETIC'
    confidence: str
    notes: str


class CanonicalMissionTimeline:
    """
    Canonical mission timeline registry for Flight 14 reconstruction.
    """
    def __init__(self, events_csv_path: Optional[str] = None):
        self.events: List[MissionEvent] = []
        self.launch_epoch: datetime = DEFAULT_MISSION_EPOCH

        if events_csv_path and os.path.exists(events_csv_path):
            self.load_from_csv(events_csv_path)
        else:
            self._load_built_in_events()

    def load_from_csv(self, path: str):
        """Loads events from actual events CSV file."""
        self.events = []
        with open(path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                t_plus = float(row.get("t_plus_seconds", 0.0))
                utc_str = row.get("utc_time_if_known", "").strip()
                utc_dt = parse_iso_epoch(utc_str) if utc_str else (self.launch_epoch + timedelta(seconds=t_plus))
                
                self.events.append(MissionEvent(
                    event_id=row.get("event_id", ""),
                    event_name=row.get("event_name", ""),
                    t_plus_s=t_plus,
                    utc_epoch=utc_dt,
                    category=row.get("planned_or_actual", "ACTUAL"),
                    confidence=row.get("confidence", "MEDIUM"),
                    notes=row.get("notes", "")
                ))
        self.events.sort(key=lambda ev: ev.t_plus_s)

    def _load_built_in_events(self):
        """Fallback built-in canonical Flight 14 milestones."""
        milestones = [
            ("EVT-ACT-003", "Liftoff", 0.0, "ACTUAL", "HIGH", "Cleared OLM"),
            ("EVT-ACT-006", "Booster MECO", 140.0, "ACTUAL", "HIGH", "MECO at T+140s"),
            ("EVT-ACT-007", "Hot-Staging Separation", 142.0, "ACTUAL", "HIGH", "Stage separation"),
            ("EVT-ACT-010", "Starship Engine Shutdown Anomaly", 255.0, "ACTUAL", "HIGH", "Premature shutdown of 1 Raptor"),
            ("EVT-ACT-013", "Starship SECO", 522.35, "ACTUAL", "HIGH", "Orbital insertion burnout"),
            ("EVT-ACT-015", "Starlink Deployment Start", 1320.0, "ACTUAL", "HIGH", "Release of 26 Starlink satellites"),
            ("EVT-ACT-016", "Starlink Deployment Complete", 1680.0, "ACTUAL", "HIGH", "26 satellites deployed"),
            ("EVT-ACT-017", "Early Deorbit Decision", 5400.0, "ACTUAL", "HIGH", "Mission shortened due to engine anomaly"),
            ("EVT-ACT-018", "Deorbit Burn Startup", 8100.0, "ACTUAL", "MEDIUM", "Retrograde deorbit maneuver"),
            ("EVT-ACT-020", "Atmospheric Entry Interface (120 km)", 9900.0, "ACTUAL", "MEDIUM", "Hypersonic entry"),
            ("EVT-ACT-023", "Pacific Ocean Splashdown", 11280.0, "ACTUAL", "HIGH", "Expended splashdown")
        ]
        for eid, name, t_s, cat, conf, notes in milestones:
            self.events.append(MissionEvent(
                event_id=eid,
                event_name=name,
                t_plus_s=t_s,
                utc_epoch=self.launch_epoch + timedelta(seconds=t_s),
                category=cat,
                confidence=conf,
                notes=notes
            ))

    def get_event(self, event_id: str) -> Optional[MissionEvent]:
        for ev in self.events:
            if ev.event_id == event_id or ev.event_name.lower() == event_id.lower():
                return ev
        return None

    def get_phase_duration(self, start_event_id: str, end_event_id: str) -> float:
        ev1 = self.get_event(start_event_id)
        ev2 = self.get_event(end_event_id)
        if not ev1 or not ev2:
            raise KeyError(f"Events '{start_event_id}' or '{end_event_id}' not found.")
        return ev2.t_plus_s - ev1.t_plus_s

    def build_phase5_insertion_state(
        self,
        seco_r: Optional[np.ndarray] = None,
        seco_v: Optional[np.ndarray] = None,
        mass_kg: float = 220850.0,
        area_m2: float = 63.617,
        cd: float = 2.20
    ) -> OrbitalState:
        """
        Creates the canonical OrbitalState at SECO handoff.
        Default values derived from Phase 4 SECO output:
        r = [967660.5, -5900231.6, 2617085.1] m
        v = [7698.6, 678.7, -1311.5] m/s
        """
        if seco_r is None:
            seco_r = np.array([967660.5, -5900231.6, 2617085.1], dtype=np.float64)
        if seco_v is None:
            seco_v = np.array([7698.6, 678.7, -1311.5], dtype=np.float64)

        seco_event = self.get_event("EVT-ACT-013")
        seco_epoch = seco_event.utc_epoch if seco_event and seco_event.utc_epoch else (
            self.launch_epoch + timedelta(seconds=522.35)
        )

        return OrbitalState(
            r=np.asarray(seco_r, dtype=np.float64),
            v=np.asarray(seco_v, dtype=np.float64),
            epoch=seco_epoch,
            frame="ECI_J2000",
            mass_kg=mass_kg,
            area_m2=area_m2,
            cd=cd
        )
