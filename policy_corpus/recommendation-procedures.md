# Hotel Recommendation Algorithm Procedures

**Version:** 1.0  
**Date:** March 10, 2026  

## 1. Overview
Hybrid system: Content-based filtering + collaborative filtering + rule-based personalization.

## 2. Inputs
- User: Location (geocode), age bucket, gender flag, budget max, preference vector (one-hot encoded amenities)
- Hotel: Features (price, rating, amenities, location score, gender-safety tags)

## 3. Processing Steps
1. Filter by location + budget  
2. Score via weighted sum (distance 30%, price fit 25%, preference match 30%, rating 15%)  
3. Apply bias mitigation (e.g., boost diverse options for gender/age)  
4. Rank top 10–20  

## 4. Bias & Fairness
Regular audits for gender/age/location bias. No discriminatory proxies.

## 5. Updates
Monthly retraining on anonymized data. A/B testing new models.

(Expand with pseudocode, metrics like NDCG, ~7 pages.)