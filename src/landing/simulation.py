"""
Simulation runner and orchestrator for Starship Phase 7 terminal landing dynamics.
"""

from typing import Dict, Any, List, Tuple, Optional
import math
import csv
import json
import os
from src.landing.state import LandingState, EventRecord
from src.landing.vehicle import StarshipLandingVehicle
from src.landing.propulsion import RaptorLandingPropulsion
from src.landing.flip import AerodynamicFlipManeuver
from src.landing.guidance import TerminalLandingGuidance
from src.landing.events import LandingStateMachine
from src.landing.touchdown import TouchdownAssessor, TouchdownReport
from src.landing.dynamics import rk4_step


class LandingSimulation:
    """Orchestrates the terminal landing simulation from scenario configuration."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.scenario_id: str = config.get("scenario_id", "synthetic_landing")

        # Initialize Vehicle
        veh_cfg = config.get("vehicle", {})
        self.vehicle = StarshipLandingVehicle(
            dry_mass_kg=float(veh_cfg.get("dry_mass_kg", 99980.0)),
            usable_propellant_kg=float(veh_cfg.get("usable_propellant_kg", 25000.0)),
            reserve_propellant_kg=float(veh_cfg.get("reserve_propellant_kg", 1500.0)),
            reference_area_m2=float(veh_cfg.get("reference_area_m2", 63.62)),
            broadside_area_m2=float(veh_cfg.get("broadside_area_m2", 450.0)),
            axial_drag_coeff=float(veh_cfg.get("axial_drag_coeff", 0.30)),
            crossflow_drag_coeff=float(veh_cfg.get("crossflow_drag_coeff", 1.15)),
            lift_coeff_max=float(veh_cfg.get("lift_coeff_max", 0.25)),
            pitch_inertia_nom_kg_m2=float(veh_cfg.get("pitch_inertia_kg_m2", 2.5e7)),
            gimbal_arm_m=float(veh_cfg.get("gimbal_arm_m", 20.0)),
            max_control_torque_Nm=float(veh_cfg.get("max_control_torque_Nm", 5.0e6)),
            pitch_rate_damping_Nm_s=float(veh_cfg.get("pitch_rate_damping_Nm_s", 8.0e5)),
        )

        # Initialize Propulsion
        prop_cfg = config.get("propulsion", {})
        self.propulsion = RaptorLandingPropulsion(
            engine_count=int(prop_cfg.get("engine_count", 3)),
            thrust_per_engine_nominal_N=float(prop_cfg.get("thrust_per_engine_nominal_N", 2250000.0)),
            specific_impulse_s=float(prop_cfg.get("specific_impulse_s", 327.0)),
            minimum_throttle=float(prop_cfg.get("minimum_throttle", 0.40)),
            maximum_throttle=float(prop_cfg.get("maximum_throttle", 1.00)),
            throttle_slew_rate_limit=float(prop_cfg.get("throttle_slew_rate_limit", 0.60)),
            ignition_delay_s=float(prop_cfg.get("ignition_delay_s", 1.0)),
            thrust_ramp_duration_s=float(prop_cfg.get("thrust_ramp_duration_s", 0.8)),
            gimbal_limit_deg=float(prop_cfg.get("gimbal_limit_deg", 15.0)),
            gimbal_slew_rate_deg_s=float(prop_cfg.get("gimbal_slew_rate_deg_s", 20.0)),
        )

        # Initialize Flip Maneuver
        flip_cfg = config.get("flip_maneuver", {})
        self.flip = AerodynamicFlipManeuver(
            mode=flip_cfg.get("mode", "prescribed_kinematic_flip"),
            trigger_altitude_m=float(flip_cfg.get("trigger_altitude_m", 800.0)),
            duration_s=float(flip_cfg.get("duration_s", 4.0)),
            target_pitch_deg=float(flip_cfg.get("target_pitch_deg", 0.0)),
            kp_pitch=float(flip_cfg.get("kp_pitch", 3.5e6)),
            kd_pitch=float(flip_cfg.get("kd_pitch", 1.2e6)),
        )

        # Initialize Guidance
        guid_cfg = config.get("guidance", {})
        target_pos = guid_cfg.get("target_position_m", [0.0, 0.0])
        self.guidance = TerminalLandingGuidance(
            target_x_m=float(target_pos[0]),
            target_z_m=float(target_pos[1]),
            target_deceleration_mps2=float(guid_cfg.get("target_deceleration_mps2", 12.0)),
            touchdown_velocity_mps=float(guid_cfg.get("touchdown_velocity_mps", 1.5)),
            kp_vertical=float(guid_cfg.get("kp_vertical", 0.40)),
            kd_vertical=float(guid_cfg.get("kd_vertical", 0.80)),
            kp_horizontal=float(guid_cfg.get("kp_horizontal", 0.05)),
            kd_horizontal=float(guid_cfg.get("kd_horizontal", 0.15)),
            max_tilt_deg=float(guid_cfg.get("max_tilt_deg", 10.0)),
        )

        # Initialize Touchdown Assessor
        crit_cfg = config.get("touchdown_criteria", {})
        self.assessor = TouchdownAssessor(
            max_vertical_speed_mps=crit_cfg.get("max_vertical_speed_mps", 3.0),
            max_horizontal_speed_mps=crit_cfg.get("max_horizontal_speed_mps", 1.5),
            max_pitch_error_deg=crit_cfg.get("max_pitch_error_deg", 5.0),
            max_pitch_rate_deg_s=crit_cfg.get("max_pitch_rate_deg_s", 2.0),
            max_radial_error_m=crit_cfg.get("max_radial_error_m", 25.0),
        )

        # State Machine
        self.state_machine = LandingStateMachine()

        # Initial State
        init_cfg = config.get("initial_state", {})
        pos = init_cfg.get("position_m", [0.0, 1500.0])
        vel = init_cfg.get("velocity_mps", [0.0, -95.0])
        init_mass = float(init_cfg.get("mass_kg", self.vehicle.total_initial_mass_kg))
        init_pitch = float(init_cfg.get("attitude_deg", -90.0))
        init_rate = float(init_cfg.get("pitch_rate_deg_s", 0.0))

        self.initial_state = LandingState(
            time_s=0.0,
            x=float(pos[0]),
            z=float(pos[1]),
            vx=float(vel[0]),
            vz=float(vel[1]),
            mass_kg=init_mass,
            pitch_deg=init_pitch,
            pitch_rate_deg_s=init_rate,
            event="APPROACH"
        )

        # Integrator settings
        int_cfg = config.get("integrator", {})
        self.dt_s: float = float(int_cfg.get("dt_s", 0.01))
        self.max_time_s: float = float(int_cfg.get("max_time_s", 40.0))

    def run(self) -> Tuple[List[LandingState], TouchdownReport, List[EventRecord]]:
        """
        Execute full terminal landing simulation.
        Returns: (history, touchdown_report, event_log)
        """
        current_state = self.initial_state
        history: List[LandingState] = [current_state]

        # Tracking variables
        ignition_altitude_m: Optional[float] = None
        burn_start_altitude_m: Optional[float] = None
        peak_apparent_g: float = 1.0
        max_thrust_N: float = 0.0

        step_count = int(self.max_time_s / self.dt_s)

        for step in range(step_count):
            t = current_state.time_s

            # 1. Check Flip Trigger
            flip_just_triggered = self.flip.check_trigger(current_state.z, t, current_state.pitch_deg)

            # 2. Check Engine Ignition Condition
            # Ignite engines during flip rotation once vehicle pitches towards upright or reaches altitude threshold
            if not self.propulsion.ignition_commanded:
                if self.flip.is_triggered and (current_state.z <= 450.0 or current_state.pitch_deg >= -20.0):
                    self.propulsion.command_ignition(t)
                    ignition_altitude_m = current_state.z

            # Record burn start altitude when ramp completes
            if self.propulsion.engine_state in ("RAMPING", "BURNING") and burn_start_altitude_m is None:
                burn_start_altitude_m = current_state.z

            # Engine staging: 3 engines during flip deceleration, 1 engine for terminal vertical descent
            if self.propulsion.engine_count == 3 and (current_state.vz >= -18.0 or current_state.z <= 80.0) and abs(current_state.pitch_deg) <= 10.0:
                self.propulsion.engine_count = 1

            # 3. Determine Attitude and Moments
            applied_torque = 0.0
            if self.flip.mode == "prescribed_kinematic_flip":
                target_pitch, target_rate = self.flip.get_kinematic_pitch(t)
                next_step_pitch = target_pitch
                next_step_rate = target_rate
            else:
                # Planar dynamic flip (L2)
                applied_torque = self.flip.compute_dynamic_torque(
                    current_state.pitch_deg, current_state.pitch_rate_deg_s,
                    self.vehicle.max_control_torque_Nm
                )
                next_step_pitch = current_state.pitch_deg
                next_step_rate = current_state.pitch_rate_deg_s

            # 4. Guidance: Compute Throttle and TVC Commands
            rem_prop = max(0.0, self.vehicle.usable_propellant_kg - self.propulsion.propellant_consumed_kg)
            throttle_cmd, gimbal_cmd_deg, vz_des = self.guidance.compute_commands(
                current_state, self.vehicle, self.propulsion
            )

            # 5. Update Propulsion System
            self.propulsion.update(t, self.dt_s, throttle_cmd, gimbal_cmd_deg, rem_prop)
            if self.propulsion.current_thrust_N > max_thrust_N:
                max_thrust_N = self.propulsion.current_thrust_N

            # 6. Update State Machine
            active_event = self.state_machine.update(
                current_state,
                self.flip.is_triggered,
                self.flip.is_completed,
                self.propulsion.engine_state,
                rem_prop
            )
            current_state.event = active_event

            # 7. Step Equations of Motion
            next_state = rk4_step(
                current_state,
                self.vehicle,
                self.propulsion,
                self.dt_s,
                next_step_pitch,
                next_step_rate,
                mode=self.flip.mode,
                applied_torque_Nm=applied_torque
            )

            if next_state.apparent_g > peak_apparent_g:
                peak_apparent_g = next_state.apparent_g

            # 8. Check Surface Crossing (Touchdown Detection)
            touchdown_state = self.state_machine.detect_surface_crossing(current_state, next_state)
            if touchdown_state is not None:
                history.append(touchdown_state)
                current_state = touchdown_state
                break

            current_state = next_state
            history.append(current_state)

            # Check if simulation should abort due to fuel exhaustion or negative altitude runaway
            if current_state.z < -5.0:
                break

        # Compute summary metrics
        final_state = history[-1]
        burn_duration = 0.0
        if self.propulsion.actual_burn_start_s is not None:
            burn_duration = max(0.0, final_state.time_s - self.propulsion.actual_burn_start_s)

        alt_loss_delay = 0.0
        if ignition_altitude_m is not None and burn_start_altitude_m is not None:
            alt_loss_delay = max(0.0, ignition_altitude_m - burn_start_altitude_m)

        report = self.assessor.assess(
            touchdown_state=final_state,
            vehicle=self.vehicle,
            propellant_consumed_kg=self.propulsion.propellant_consumed_kg,
            burn_duration_s=burn_duration,
            ignition_delay_altitude_loss_m=alt_loss_delay,
            peak_apparent_g=peak_apparent_g,
            max_thrust_N=max_thrust_N
        )

        return history, report, self.state_machine.event_log

    def export_results(self, output_dir: str,
                       history: List[LandingState],
                       report: TouchdownReport,
                       event_log: List[EventRecord]) -> Dict[str, str]:
        """Write simulation artifacts to output directory."""
        os.makedirs(output_dir, exist_ok=True)

        traj_csv = os.path.join(output_dir, f"{self.scenario_id}_trajectory.csv")
        with open(traj_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "time_s", "x_m", "z_m", "vx_mps", "vz_mps", "speed_mps", "mass_kg",
                "pitch_deg", "pitch_rate_deg_s", "thrust_N", "throttle", "gimbal_deg",
                "engine_state", "event", "drag_N", "apparent_g"
            ])
            writer.writeheader()
            for s in history:
                writer.writerow(s.to_dict())

        event_csv = os.path.join(output_dir, f"{self.scenario_id}_events.csv")
        with open(event_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "event_id", "time_s", "altitude_m", "vertical_speed_mps",
                "horizontal_speed_mps", "pitch_deg", "mass_kg", "details"
            ])
            writer.writeheader()
            for e in event_log:
                writer.writerow(e.to_dict())

        summary_json = os.path.join(output_dir, f"{self.scenario_id}_summary.json")
        with open(summary_json, "w") as f:
            json.dump(report.to_dict(), f, indent=2)

        return {
            "trajectory_csv": traj_csv,
            "events_csv": event_csv,
            "summary_json": summary_json
        }
