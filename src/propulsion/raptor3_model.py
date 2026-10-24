"""
Propulsion Module — SpaceX Raptor 3 Full-Flow Staged Combustion (FFSC) Model
=============================================================================
Implements detailed thermodynamic and thrust models for Raptor 3 rocket engines:
- Sea-level and vacuum expansion nozzle performance
- Altitude-dependent thrust and specific impulse (Isp)
- Propellant mass flow rate ODE: dm/dt = - F / (Isp * g0)
- 33-engine Super Heavy booster cluster with throttle profiles
- Single-engine failure / contingency scenario injection
"""

import math
import numpy as np

G0 = 9.80665 # Standard gravity (m/s^2)

class Raptor3Engine:
    """
    Raptor 3 Full-Flow Staged Combustion rocket engine model.
    """
    def __init__(self, variant="SL"):
        """
        variant : str, 'SL' (Sea-Level) or 'VAC' (Vacuum)
        """
        self.variant = variant.upper()

        if self.variant == "SL":
            self.thrust_vac = 2.90e6      # 2.90 MN (N)
            self.thrust_sl = 2.75e6       # 2.75 MN (N)
            self.isp_vac = 350.0          # seconds
            self.isp_sl = 330.0           # seconds
            self.exit_diameter = 1.30     # m
            self.dry_mass = 1525.0        # kg
        elif self.variant == "VAC":
            self.thrust_vac = 2.90e6      # 2.90 MN (N)
            self.thrust_sl = 2.30e6       # Flow-separated at 1 atm
            self.isp_vac = 380.0          # seconds
            self.isp_sl = 290.0           # seconds
            self.exit_diameter = 2.30     # m
            self.dry_mass = 1800.0        # kg
        else:
            raise ValueError(f"Unknown Raptor variant: {variant}")

        self.exit_area = 0.25 * math.pi * (self.exit_diameter ** 2)
        # Nominal mass flow rate is constant across altitudes for fixed chamber conditions
        self.mass_flow_nominal = self.thrust_vac / (self.isp_vac * G0) # kg/s (~844.9 kg/s for SL)
        self.of_ratio = 3.60 # LOX / LCH4 mass ratio

    def compute_performance(self, ambient_pressure_pa, throttle=1.0):
        """
        Computes instantaneous thrust and Isp at given ambient pressure and throttle.

        Parameters:
        -----------
        ambient_pressure_pa : float
            Atmospheric pressure (Pa)
        throttle : float
            Throttle setting [0.40 to 1.0]

        Returns:
        --------
        thrust_n : float
            Thrust produced (N)
        isp_s : float
            Specific impulse (s)
        mdot_kg_s : float
            Mass flow rate (kg/s)
        """
        throttle = max(0.0, min(float(throttle), 1.0))
        if throttle == 0.0:
            return 0.0, 0.0, 0.0

        # Thrust = F_vac - A_e * P_a
        # At throttle < 1.0, chamber pressure scales with throttle
        f_vac_throttled = self.thrust_vac * throttle
        f_inst = f_vac_throttled - self.exit_area * ambient_pressure_pa
        # Prevent negative thrust under extreme over-expansion
        f_inst = max(f_inst, 0.1 * f_vac_throttled)

        mdot = self.mass_flow_nominal * throttle
        isp = f_inst / (mdot * G0)

        return f_inst, isp, mdot


class BoosterCluster33:
    """
    Super Heavy Booster 33-Raptor 3 Propulsion System.
    Layout: 1 Center, 2 Inner, 10 Middle, 20 Outer.
    """
    def __init__(self, enable_anomaly=False, anomaly_time_s=35.0, anomaly_engine_id=17):
        self.engines = [Raptor3Engine(variant="SL") for _ in range(33)]
        self.enable_anomaly = enable_anomaly
        self.anomaly_time_s = anomaly_time_s
        self.anomaly_engine_id = anomaly_engine_id # 0-indexed: engine 17 is outer ring

    def get_throttle_schedule(self, t, dynamic_pressure_pa):
        """
        Determines baseline cluster throttle based on mission event time and dynamic pressure.
        """
        if t < 0.0:
            return 0.0

        # Liftoff ignition ramp (0 to 2 s)
        if t < 2.0:
            return 0.90 + 0.10 * (t / 2.0)

        # Full liftoff thrust (2 to 30 s)
        if t < 30.0:
            return 1.00

        # Max-Q throttle bucket (target q ~ 36 kPa between 30 s and 68 s)
        if t < 68.0:
            return 0.60

        # Upper ascent throttle to manage structural acceleration (< 3.2g)
        if t < 132.0:
            return 0.75

        # MECO throttle ramp-down (outer rings cut off, 3 center engines maintain hot-staging thrust)
        if t <= 140.0:
            return 0.12 * ((140.0 - t) / 8.0) + 0.091

        # Post-MECO (staging)
        return 0.0

    def compute_cluster_state(self, t, ambient_pressure_pa, dynamic_pressure_pa):
        """
        Computes total cluster thrust, net mass flow rate, and active engine count.

        Returns:
        --------
        total_thrust_n : float
        total_mdot_kg_s : float
        effective_isp_s : float
        active_engines : int
        """
        base_throttle = self.get_throttle_schedule(t, dynamic_pressure_pa)
        if base_throttle <= 0.0 or t > 140.0:
            return 0.0, 0.0, 0.0, 0

        active_count = 0
        total_thrust = 0.0
        total_mdot = 0.0

        # Check if single engine anomaly is active
        anomaly_active = self.enable_anomaly and (t >= self.anomaly_time_s)

        for i, eng in enumerate(self.engines):
            if anomaly_active and (i == self.anomaly_engine_id):
                # Anomaly engine shut down
                continue

            # If anomaly is active, remaining engines throttle up slightly (by factor 33/32)
            # if within allowable throttle limit (max 1.0)
            if anomaly_active and base_throttle < 0.96:
                eng_throttle = min(base_throttle * (33.0 / 32.0), 1.0)
            else:
                eng_throttle = base_throttle

            thrust_i, isp_i, mdot_i = eng.compute_performance(ambient_pressure_pa, eng_throttle)
            total_thrust += thrust_i
            total_mdot += mdot_i
            active_count += 1

        effective_isp = total_thrust / (total_mdot * G0) if total_mdot > 0.0 else 0.0
        return total_thrust, total_mdot, effective_isp, active_count
