# Sales Dashboard - Requirements Questionnaire

**Project:** Monday.com to Excel Sync & Sales Dashboard
**Client:** TAG Urbanic
**Date:** December 2025
**Prepared by:** Drishti Consulting

---

## Introduction

This document outlines the key decisions needed to finalize the Sales Dashboard application. Please review each section and provide your responses to ensure the system meets your business requirements.

---

## Section 1: Access & Security

| # | Question | Your Response |
|---|----------|---------------|
| 1.1 | How many people from the company will have access to the app? | |
| 1.2 | What level of security is required for access? | [ ] Email & Password<br>[ ] Single Sign-On (SSO)<br>[ ] Two-Factor Authentication (2FA)<br>[ ] Other: _____________ |
| 1.3 | Should there be different user roles with different permissions? | [ ] Yes<br>[ ] No<br><br>If yes, please specify roles: |
| 1.4 | Do you require an audit log tracking who accessed the app and when? | [ ] Yes<br>[ ] No |
| 1.5 | Should users be restricted to viewing specific projects only? | [ ] Yes<br>[ ] No |

---

## Section 2: Data Synchronization

| # | Question | Your Response |
|---|----------|---------------|
| 2.1 | What should trigger the data sync between Monday.com and Excel? | [ ] Real-time (any update in Monday.com)<br>[ ] Scheduled (hourly, daily, etc.)<br>[ ] When opening the app<br>[ ] Manual button click only<br>[ ] Combination: _____________ |
| 2.2 | If scheduled, how often should the sync run? | [ ] Every hour<br>[ ] Every 4 hours<br>[ ] Daily at ___:___ AM/PM<br>[ ] Other: _____________ |
| 2.3 | Should the sync be one-way or two-way? | [ ] One-way: Monday.com → Excel only<br>[ ] Two-way: Changes in both directions |
| 2.4 | If there's a conflict between Monday.com and Excel data, which should take priority? | [ ] Monday.com (source of truth)<br>[ ] Excel<br>[ ] Alert user to resolve manually |
| 2.5 | Should empty values in Monday.com overwrite existing Excel data? | [ ] Yes<br>[ ] No (preserve Excel data) |

---

## Section 3: Data Storage & Backup

| # | Question | Your Response |
|---|----------|---------------|
| 3.1 | Where should the updated Excel file be saved? | [ ] Local server<br>[ ] Google Drive<br>[ ] Microsoft OneDrive/SharePoint<br>[ ] GitHub repository<br>[ ] Other: _____________ |
| 3.2 | Do you need automatic backups of the Excel file before each sync? | [ ] Yes<br>[ ] No |
| 3.3 | How long should change logs be retained? | [ ] 30 days<br>[ ] 90 days<br>[ ] 1 year<br>[ ] Indefinitely |
| 3.4 | Should backup copies be stored in a separate location? | [ ] Yes - Location: _____________<br>[ ] No |

---

## Section 4: Data Scope

### 4.1 Please Approve the Current Sync Configuration

**Monday.com Boards to Excel Sheets Mapping:**

| Monday.com Board | Monday.com Group | Target Excel Sheet | Approve? |
|------------------|------------------|-------------------|----------|
| Data Base_Clients | Sales_Horizon | SAL D'OURO HORIZON (9) | [ ] Yes [ ] No |
| Data Base_Clients | Sal D'Ouro_Coast | SAL D'OURO COAST (10) | [ ] Yes [ ] No |

**Field Mapping:**

| Monday.com Field | Excel Column | Include in Sync? |
|------------------|--------------|------------------|
| Client Name | Client | [ ] Yes [ ] No |
| Unit | Unit | [ ] Yes [ ] No |
| Fraction | Fraction | [ ] Yes [ ] No |
| Layout | Layout | [ ] Yes [ ] No |
| Floor | Floor | [ ] Yes [ ] No |
| Status | Status | [ ] Yes [ ] No |
| Broker | Brokers company | [ ] Yes [ ] No |
| Date Signed | Date of CPCV | [ ] Yes [ ] No |
| Nationality | Client Nationality | [ ] Yes [ ] No |
| Email | Email | [ ] Yes [ ] No |
| Phone | Phone | [ ] Yes [ ] No |

### 4.2 Additional Data Questions

| # | Question | Your Response |
|---|----------|---------------|
| 4.2.1 | Are there additional Monday.com boards that should be included? | [ ] Yes - Board names: _____________<br>[ ] No |
| 4.2.2 | Are there additional Excel sheets that need to be updated from Monday.com? | [ ] Yes - Sheet names: _____________<br>[ ] No |
| 4.2.3 | Should the summary sheet ("sales report - general") auto-recalculate after sync? | [ ] Yes<br>[ ] No |
| 4.2.4 | Are there any fields that should NEVER be overwritten by the sync? | [ ] Yes - Fields: _____________<br>[ ] No |

---

## Section 5: Notifications & Alerts

| # | Question | Your Response |
|---|----------|---------------|
| 5.1 | Should users receive notifications when sync completes? | [ ] Yes<br>[ ] No |
| 5.2 | How should notifications be delivered? | [ ] In-app notification<br>[ ] Email<br>[ ] Both |
| 5.3 | Should there be alerts for sync errors or data conflicts? | [ ] Yes<br>[ ] No |
| 5.4 | Who should receive error notifications? | Email addresses:<br>1. _____________<br>2. _____________<br>3. _____________ |
| 5.5 | Do you want a daily/weekly summary report of all changes? | [ ] Daily<br>[ ] Weekly<br>[ ] No |

---

## Section 6: Deployment & Hosting

| # | Question | Your Response |
|---|----------|---------------|
| 6.1 | Where should the application be hosted? | [ ] Local server (your infrastructure)<br>[ ] Cloud - AWS<br>[ ] Cloud - Microsoft Azure<br>[ ] Cloud - Google Cloud<br>[ ] Streamlit Cloud<br>[ ] Other: _____________ |
| 6.2 | Do you need a custom domain? | [ ] Yes - Preferred domain: _____________<br>[ ] No (default URL is fine) |
| 6.3 | What is the expected uptime requirement? | [ ] 24/7 availability<br>[ ] Business hours only<br>[ ] Best effort |
| 6.4 | Do you need a staging/test environment separate from production? | [ ] Yes<br>[ ] No |

---

## Section 7: Future Considerations

| # | Question | Your Response |
|---|----------|---------------|
| 7.1 | Do you anticipate adding more projects to the system in the future? | [ ] Yes - Estimated: ___ projects<br>[ ] No |
| 7.2 | Will additional team members need access in the future? | [ ] Yes - Estimated: ___ users<br>[ ] No |
| 7.3 | Are there other Monday.com boards you may want to integrate later? | [ ] Yes - Board names: _____________<br>[ ] No |
| 7.4 | Do you need mobile access to the dashboard? | [ ] Yes<br>[ ] No<br>[ ] Nice to have |
| 7.5 | Are there any other integrations you'd like to consider? | [ ] Power BI<br>[ ] Google Sheets<br>[ ] Salesforce<br>[ ] Other: _____________ |

---

## Section 8: Additional Comments

Please provide any additional requirements, concerns, or questions:

```
_______________________________________________________________________________

_______________________________________________________________________________

_______________________________________________________________________________

_______________________________________________________________________________

_______________________________________________________________________________
```

---

## Sign-Off

By signing below, you confirm that the responses provided accurately reflect your requirements.

| | |
|---|---|
| **Client Name:** | _________________________ |
| **Title:** | _________________________ |
| **Date:** | _________________________ |
| **Signature:** | _________________________ |

---

**Thank you for completing this questionnaire.**

Please return the completed document to Drishti Consulting.
For questions, contact: [Your Contact Information]

---

*Document Version: 1.0*
*Prepared by: Drishti Consulting*
