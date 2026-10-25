# Starship Flight 14 Digital Engineering Lab — Mass & Propulsion Reconciliation Report

**Document ID:** `DOC-AUDIT-MASS-001`  
**Classification:** Mass Properties & Propulsion Systems Audit  
**Status:** **FULLY RECONCILED (Residual = 0.000 kg)**  

---

## 1. Investigation of Historical Mass Conflation

The user raised a critical red flag:
> *"The reported 220.85 t insertion mass, 4.577 t payload removal, and 177.27 t entry mass do not reconcile without additional mass changes. The model must account for every kilogram."*

### Root Cause Analysis:
During the development of Phase 5 and Phase 6, an informal textual summary conflated the **payload mass** with the **deorbit burn propellant mass**. Specifically:
- A summary text stated: *"4.577 t payload removal"*
- This was an error in summary phrasing. The value **$4,577.29\,\text{kg}$ ($4.577\,\text{t}$)** was NOT the payload mass; it was the **propellant consumed during the deorbit disposal burn** calculated via the Tsiolkovsky rocket equation.
- The actual modeled deployed payload was **$39,000.0\,\text{kg}$ ($39.0\,\text{t}$)**, representing 26 Starlink V3 direct-to-cell satellites at $1,500\,\text{kg}$ each.

### Full Mass Reconciliation Calculation:
1. **SECO Insertion Mass (T+522.35 s):**
   $$m_{\text{SECO}} = 220,850.00\,\text{kg} \quad (220.85\,\text{t})$$
   Breakdown: $99,975\,\text{kg}$ dry + $39,000\,\text{kg}$ payload + $81,875\,\text{kg}$ reserve propellant.
2. **Payload Deployment (T+1500.0 s):**
   $$\Delta m_{\text{payload}} = -39,000.00\,\text{kg} \quad (-39.0\,\text{t})$$
   $$m_{\text{post-deploy}} = 220,850.00 - 39,000.00 = 181,850.00\,\text{kg} \quad (181.85\,\text{t})$$
3. **Targeted Deorbit Disposal Burn (T+5900.0 s):**
   - Retrograde delta-v: $\Delta v = 95.00\,\text{m/s}$
   - Specific impulse: $I_{\text{sp}} = 380.00\,\text{s}$ (Raptor vacuum)
   - Standard gravity: $g_0 = 9.80665\,\text{m/s}^2$
   - Propellant consumed (Tsiolkovsky):
     $$\Delta m_{\text{burn}} = m_{\text{post-deploy}} \left[1 - \exp\left(-\frac{\Delta v}{g_0 I_{\text{sp}}}\right)\right] = 181,850.00 \times \left[1 - \exp\left(-\frac{95.00}{9.80665 \times 380.00}\right)\right] = 4,577.29\,\text{kg}$$
4. **Post-Deorbit Mass (Crossing 120 km Entry Interface at T+6527.315 s):**
   $$m_{\text{entry}} = 181,850.00 - 4,577.29 = 177,272.71\,\text{kg} \quad (177.27\,\text{t})$$
   Breakdown: $99,975\,\text{kg}$ dry + $0\,\text{kg}$ payload + $77,297.71\,\text{kg}$ residual propellant.
5. **Mass Balance Residual:**
   $$\text{Residual} = 220,850.00 - 39,000.00 - 4,577.29 - 177,272.71 = \mathbf{0.000\,\text{kg}}$$

Every single kilogram is strictly accounted for without unexplained mass loss.

---

## 2. Propulsion System Performance Accounting

| Parameter | Super Heavy Booster (33x Raptor 3) | Starship Upper Stage (6x Raptor 3) |
| :--- | :--- | :--- |
| **Engine Count** | 33 engines (13 gimbal center, 20 fixed outer) | 6 engines (3 center sea-level, 3 vacuum) |
| **Sea-Level Thrust per Engine** | $2.75\,\text{MN}$ ($280\,\text{tf}$) | $2.75\,\text{MN}$ (center) / $2.95\,\text{MN}$ (vacuum) |
| **Vacuum Thrust per Engine** | $3.00\,\text{MN}$ | $3.25\,\text{MN}$ |
| **Specific Impulse ($I_{\text{sp}}$)** | $327\,\text{s}$ (sea-level) to $350\,\text{s}$ (vacuum) | $327\,\text{s}$ (SL) to $380\,\text{s}$ (Vac) |
| **Total Liftoff Thrust** | $90.75\,\text{MN}$ ($9,250\,\text{tf}$) | $18.00\,\text{MN}$ ($1,835\,\text{tf}$) |
| **Liftoff Thrust-to-Weight Ratio**| $1.87$ ($90.75\,\text{MN} / (4,939.8\,\text{t} \times 9.80665)$) | $1.37$ at stage separation |
| **Propellant Type** | Liquid Oxygen (LOX) / Liquid Methane ($\text{LCH}_4$) | Liquid Oxygen (LOX) / Liquid Methane ($\text{LCH}_4$) |
| **Mixture Ratio (O/F)** | $3.60 : 1.00$ | $3.60 : 1.00$ |
| **Total Propellant Capacity** | $3,400.0\,\text{t}$ | $1,200.0\,\text{t}$ |
