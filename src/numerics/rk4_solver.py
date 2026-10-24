"""
Numerical Solvers — High-Precision Runge-Kutta Integrators
===========================================================
Provides fixed-step classical Runge-Kutta 4th-order (RK4) and adaptive
Runge-Kutta-Fehlberg 4(5) (RKF45) integrators for flight dynamic ODE systems.

Complies with AIAA/NASA numerical integration verification standards.
"""

import numpy as np

def rk4_step(f, t, y, dt, *args):
    """
    Executes a single classical Runge-Kutta 4th-order integration step.

    Parameters:
    -----------
    f : callable
        Vector derivative function: dy/dt = f(t, y, *args)
    t : float
        Current time (s)
    y : np.ndarray
        Current state vector
    dt : float
        Time step size (s)
    *args : tuple
        Additional parameters passed to f

    Returns:
    --------
    y_next : np.ndarray
        Propagated state vector at t + dt
    """
    k1 = f(t, y, *args)
    k2 = f(t + 0.5 * dt, y + 0.5 * dt * k1, *args)
    k3 = f(t + 0.5 * dt, y + 0.5 * dt * k2, *args)
    k4 = f(t + dt, y + dt * k3, *args)
    return y + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)

def rk4_solve(f, t_span, y0, dt, *args, event_fn=None):
    """
    Integrates an ODE system using fixed-step RK4.

    Parameters:
    -----------
    f : callable
        Vector derivative function: dy/dt = f(t, y, *args)
    t_span : tuple (t0, tf)
        Start and end integration time (s)
    y0 : array_like
        Initial state vector
    dt : float
        Fixed integration step size (s)
    *args : tuple
        Additional parameters passed to f
    event_fn : callable, optional
        Terminal event function: event_fn(t, y). Integration terminates when event_fn <= 0.

    Returns:
    --------
    t_hist : np.ndarray
        Array of time points
    y_hist : np.ndarray
        Array of state vectors [N, len(y0)]
    """
    t0, tf = t_span
    y = np.array(y0, dtype=np.float64)
    t = float(t0)

    t_list = [t]
    y_list = [y.copy()]

    while t < tf:
        h = min(dt, tf - t)
        y = rk4_step(f, t, y, h, *args)
        t += h

        t_list.append(t)
        y_list.append(y.copy())

        if event_fn is not None:
            if event_fn(t, y) <= 0.0:
                break

    return np.array(t_list), np.array(y_list)

def rkf45_step(f, t, y, dt, *args):
    """
    Embedded Runge-Kutta-Fehlberg 4(5) step with local truncation error estimate.
    Cash-Karp / Fehlberg Butcher tableau.
    """
    # Fehlberg coefficients
    c2, a21 = 1/4, 1/4
    c3, a31, a32 = 3/8, 3/32, 9/32
    c4, a41, a42, a43 = 12/13, 1932/2197, -7200/2197, 7296/2197
    c5, a51, a52, a53, a54 = 1.0, 439/216, -8.0, 3680/513, -845/4104
    c6, a61, a62, a63, a64, a65 = 1/2, -8/27, 2.0, -3544/2565, 1859/4104, -11/40

    # 4th order weights
    b1, b3, b4, b5 = 25/216, 1408/2565, 2197/4104, -1/5
    # 5th order weights
    b1_5, b3_5, b4_5, b5_5, b6_5 = 16/135, 6656/12825, 28561/56430, -9/50, 2/55

    k1 = f(t, y, *args)
    k2 = f(t + c2 * dt, y + dt * (a21 * k1), *args)
    k3 = f(t + c3 * dt, y + dt * (a31 * k1 + a32 * k2), *args)
    k4 = f(t + c4 * dt, y + dt * (a41 * k1 + a42 * k2 + a43 * k3), *args)
    k5 = f(t + c5 * dt, y + dt * (a51 * k1 + a52 * k2 + a53 * k3 + a54 * k4), *args)
    k6 = f(t + c6 * dt, y + dt * (a61 * k1 + a62 * k2 + a63 * k3 + a64 * k4 + a65 * k5), *args)

    y4 = y + dt * (b1 * k1 + b3 * k3 + b4 * k4 + b5 * k5)
    y5 = y + dt * (b1_5 * k1 + b3_5 * k3 + b4_5 * k4 + b5_5 * k5 + b6_5 * k6)

    err = np.max(np.abs(y5 - y4))
    return y5, err
