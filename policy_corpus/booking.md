Complete Transaction (Frontend):
Redirect user to Paystack hosted checkout page (or inline via popup). User enters card/bank details. Paystack handles 3DS/OTP.
Verify Transaction (Backend – Webhook + Polling):
Paystack sends webhook (POST to our /webhook endpoint) on success/failed.
Verify signature & status via GET /transaction/verify/:reference.
On 'success': Update booking status to "Confirmed", notify hotel/user.
Log all events securely (see Information Security Policy).


Page 4 of 6
4. Fraud Detection and Prevention Rules
NSR combines Paystack's built-in fraud tools with custom rules to address common Nigerian risks (card-not-present fraud, friendly fraud, stolen credentials, chargeback abuse).









































Rule TypeDescriptionAction on TriggerResponsiblePaystack AutomatedReal-time monitoring, velocity checks, device fingerprinting, blacklistsBlock/flag transactionAuto (Paystack)Custom Velocity>3 attempts in 5 min from same IP/device; multiple failed cardsBlock IP temporarily, require OTPBackend logicAmount/Location MismatchBooking amount > user budget profile; location jump (e.g., Lagos to Kano in minutes)Flag for manual reviewPre-payment checkHigh-Risk PatternsRepeated chargebacks on user; new card + high-value bookingRequire additional verification (BVN/phone)Rule engineFriendly Fraud MitigationClear booking confirmation page; timestamped logs; metadata for evidencePrepare for disputesAll steps

Monitoring: Dashboard alerts for spikes (>5% fraud rate).
Response: Auto-decline high-risk; manual review queue for borderline cases.

Page 5 of 6
5. Refund and Chargeback Procedures
5.1 Refunds (Merchant-Initiated)

Policy: Refunds processed within 48 hours of approval (target); full/partial allowed.
Triggers: Hotel cancellation, user request (pre-check-in), overcharge, service failure.
Procedure:
User submits via in-app/support (see Customer Service Policy).
Verify eligibility (e.g., within hotel cancellation window).
Backend calls Paystack Refund API (POST /refund): transaction reference, amount (optional for partial).
Funds reversed to original method; notify user (email/SMS).
Update booking status to "Refunded".
Example: Full refund processes in ~1-5 business days per Paystack.

5.2 Chargebacks / Disputes

Timeline: Respond within 16 hours (CBN/Paystack Nigeria rule) or auto-accepted (customer refunded, funds debited from NSR).
Process:
Paystack notifies via email/Dashboard/webhook.
Review evidence: transaction logs, IP/device, metadata, confirmation emails.
Respond via Dashboard/API: Accept (refund + forfeit) or Decline (provide evidence).
If fraud claim: Emphasize authorization (e.g., OTP confirmation).
Track metrics; recurring issues trigger user blacklisting or policy review.


Page 6 of 6
6. Responsibilities and Monitoring

























RoleResponsibilitiesEngineering TeamMaintain integration, webhooks, fraud rules; test quarterly.Finance / OpsMonitor payouts, handle refunds/chargebacks; monthly reconciliation.Customer ServiceProcess refund requests; escalate disputes.ComplianceEnsure NDPA compliance on payment data; report high fraud to NITDA if needed.

Auditing: Monthly transaction audit; annual penetration testing.
Training: Staff trained on fraud indicators and Paystack Dashboard.

Revision History

v1.0 – Initial release – March 10, 2026

Approval Signatures
CTO: _______________________ Date: __________
Finance Lead: _______________ Date: __________
End of Document
Confidential – Internal Use Only