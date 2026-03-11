# NaijaStay Recommender (NSR)  
Business Continuity and Disaster Recovery Plan

**Document Title:** Business Continuity and Disaster Recovery Plan (BCP/DRP)  
**Version:** 1.0  
**Effective Date:** March 10, 2026  
**Approved by:** CTO and CEO, NSR  
**Review Frequency:** Annually or after major incidents  

**Confidential – Internal Use Only**  
**Page 1 of 7**

## 1. Introduction
### 1.1 Purpose
This plan ensures NSR can maintain or rapidly resume critical operations during and after disruptive events. It minimizes downtime for the hotel recommendation and booking platform, protects user data (location, age, gender, preferences, budget), and safeguards revenue from partner hotel commissions.

### 1.2 Scope
Covers all NSR systems: web/mobile app (React Native/Next.js frontend, Node.js backend, PostgreSQL database), AI recommendation engine, payment integrations (Paystack), cloud infrastructure (AWS primary), and office operations in Lagos/Abuja.

Excludes force majeure events requiring full government intervention.

### 1.3 Objectives
- Achieve defined Recovery Time Objective (RTO) and Recovery Point Objective (RPO) for critical functions.  
- Minimize financial/reputational damage.  
- Comply with NDPA 2023, NITDA guidelines, and best practices (aligned with ISO 22301 principles).

**Page 2 of 7**

## 2. Risk Assessment
NSR faces unique Nigerian and tech-sector risks. Key threats identified via annual risk register (last updated Q1 2026):

| Risk Category          | Description                                                                 | Likelihood | Impact | Mitigation Owner |
|------------------------|-----------------------------------------------------------------------------|------------|--------|------------------|
| Power Failure / Grid Collapse | Frequent national grid failures (multiple collapses/year), voltage fluctuations, blackouts lasting hours–days. | High      | High   | Infrastructure Team |
| Cyber Attack           | Ransomware, phishing, DDoS, credential stuffing (Nigeria averages thousands of attacks/week on businesses). | High      | Critical | Security Team (see Information Security Policy) |
| Flooding / Natural Disaster | Seasonal flooding in Lagos, Abuja flash floods; affects data centers/offices. | Medium    | High   | Facilities & BCP Coordinator |
| Hardware/Cloud Outage  | AWS region issues, provider failure, or local server faults.                | Low       | High   | DevOps Team |
| Human Error / Insider Threat | Misconfiguration, accidental data deletion, or malicious insider.           | Medium    | Medium | HR & Security |
| Third-Party Failure    | Paystack downtime, hotel API unavailability, telco/SMS gateway issues.      | Medium    | Medium | Vendor Management |

**Page 3 of 7**

## 3. Recovery Objectives (RTO & RPO)
Targets based on business impact analysis (BIA) for a recommendation/booking platform:

| Critical Function                  | RTO (Max Downtime) | RPO (Max Data Loss) | Rationale |
|------------------------------------|---------------------|----------------------|-----------|
| Core Platform (App/Web Access & Recommendations) | 4 hours            | 15 minutes          | Users expect near-real-time service; prolonged outage loses trust/bookings. |
| User Profile & Preference Data     | 2 hours            | 5 minutes           | Sensitive personal data; frequent changes. |
| Booking & Payment Processing       | 1 hour             | 1 minute            | Financial transactions; compliance risk. |
| Recommendation Engine (AI/ML)      | 6 hours            | 30 minutes          | Can operate in degraded mode with cached/static suggestions. |
| Administrative Back-office (Emails, Support) | 8 hours          | 1 hour              | Lower urgency. |
| Full Business Recovery (All Systems) | 24 hours         | N/A                 | Worst-case target. |

These align with AWS DR strategies (backup & restore → pilot light → warm standby).

**Page 4 of 7**

## 4. Continuity Strategies
### 4.1 Infrastructure Redundancy
- **Primary Hosting:** AWS Africa (Cape Town) region – Multi-AZ for compute (EC2/ECS), database (RDS Multi-AZ), S3 cross-AZ replication.  
- **Backup Location:** Local on-prem servers in Lagos (for critical read-only caches) + AWS Africa backups replicated to another region if needed.  
- **Power Resilience:** UPS + diesel generators (minimum 48-hour fuel) at office; AWS handles cloud power. Auto-failover scripts for grid outages.  
- **Network:** Multiple ISPs (MTN, Airtel, Spectranet) with SD-WAN failover.

### 4.2 Data Protection & Backups
- Daily automated snapshots (RDS, EBS) + continuous replication.  
- AWS Backup for centralized management; retention: 30 days daily, 12 months monthly.  
- Offsite: Cross-region replication to AWS Europe (Frankfurt) for extreme scenarios.  
- Encryption: AES-256 at rest, TLS 1.3 in transit.

### 4.3 Failover & Recovery Procedures
1. **Detection:** Monitoring (CloudWatch + Datadog) alerts on downtime/power loss/cyber events.  
2. **Activation:** BCP Coordinator declares incident; Crisis Management Team assembles (via WhatsApp/Slack backup channels).  
3. **Recovery Steps (example for grid outage):**  
   - Switch to generator/UPS within 10 min.  
   - If >30 min outage, trigger AWS auto-scaling; use cached recommendations.  
   - For cyber: Isolate affected systems, restore from clean backups (RPO-compliant).  
4. **Failback:** Test before returning to primary.

**Page 5 of 7**

## 5. Roles & Responsibilities
| Role                        | Responsibilities |
|-----------------------------|------------------|
| CEO / Executive Sponsor     | Approve plan; declare major incidents. |
| BCP/DR Coordinator (CTO)    | Lead planning, testing, updates. |
| Crisis Management Team      | Activate plan; communicate internally/externally. |
| DevOps/Security Team        | Execute technical recovery; forensics post-cyber. |
| Customer Service            | Manage user communications (in-app notices, emails). |
| All Employees               | Follow procedures; report incidents immediately. |

See Employee Code of Conduct and Information Security Policy for related duties.

**Page 6 of 7**

## 6. Testing & Maintenance
### 6.1 Testing Schedule
- **Tabletop Exercises:** Quarterly (simulate scenarios like grid collapse or ransomware).  
- **Technical Drills:** Biannually (failover to backup region, restore from snapshots).  
- **Full Simulation:** Annually (include office evacuation for flooding/power).  
- **Chaos Engineering:** Ad-hoc (inject failures via AWS Fault Injection Simulator).  

All tests documented; lessons incorporated into updates.

### 6.2 Plan Maintenance
- Annual review (or post-incident).  
- Version control in Git/internal wiki.  
- Training: All staff inducted; key personnel certified in AWS DR.

**Page 7 of 7**

## 7. Appendices
- Contact List (emergency numbers, vendors).  
- Incident Response Playbooks (cyber, power, flood).  
- Recovery Checklists (step-by-step).  
- Revision History  
  - v1.0 – Initial release – March 10, 2026  

**Approval Signatures**  
CTO: _______________________ Date: __________  
CEO: ________________________ Date: __________

**End of Document**  
**Confidential – Internal Use Only**