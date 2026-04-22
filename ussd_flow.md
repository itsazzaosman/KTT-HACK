# Ikimina Digital Trust Index: USSD Flow & Business Adaptation

## 1. Core Workflow & USSD Trigger
**Target User:** Ikimina Secretary (feature phone, intermittent data, low-bandwidth).
**Action:** The secretary dials `*654*MEMBER_ID#` to query a member's reliability tier before approving a pool loan.
**Per-Request Cost:** 10 RWF (deducted from the secretary's airtime/mobile money wallet).

## 2. Consent & Privacy Trade-off
* **Consent Capture:** Upon dialing, the first screen displays: *"1. By continuing, I confirm I have verbal consent from the member to check their score. Reply 1 to Accept."*
* **SS7 Privacy Vulnerability:** Transmitting an unencrypted `MEMBER_ID` over SS7 telecom networks leaves the query vulnerable to interception or spoofing. 
* **Mitigation:** To protect user privacy, the USSD response *never* transmits raw financial data, missed payment counts, or borrowed amounts. It only returns the abstracted reliability score and tier. 

## 3. USSD Response Templates
Once the score is calculated on the server (e.g., Member 412 scores 99 - Low Risk), the secretary receives an immediate flash USSD message. 

**Kinyarwanda (Primary):**
> *"Amanota y'icyizere: Umunyamuryango 412 afite 99/100 (Yizewe). Yemerewe inguzanyo."*
> *(Translation: Trust Score: Member 412 has 99/100 (Reliable). Approved for loan.)*

**French (Fallback/Option 2):**
> *"Score de Confiance: Le membre 412 a 99/100 (Risque Faible). Approuvé pour prêt."*

## 4. Failure Modes & Fallback UX
Designing for intermittent network reliability in rural areas means we must handle drops gracefully.

* **Failure Mode 1: Network Timeout (Session Drop)**
  * **Issue:** The USSD session times out before the server can return the XGBoost score.
  * **Fallback UX:** The system catches the timeout and asynchronously sends a standard SMS once the calculation finishes: *"Ikimina Alert: Your request for Member 412 was delayed. Score: 99/100 (Yizewe)."*
* **Failure Mode 2: Invalid Member ID**
  * **Issue:** The secretary mistypes the ID (e.g., dialing a member that doesn't exist).
  * **Fallback UX:** The USSD menu does not crash. It loops back with a clear error: *"Umunyamuryango ntariho. (Member not found). Reply 1 to re-enter ID, or 0 to exit."*