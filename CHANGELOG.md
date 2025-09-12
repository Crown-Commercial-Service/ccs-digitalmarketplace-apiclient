# CCS Digital Marketplace API clients changelog

Records breaking changes from major version bumps

## 37.0.1

Make sure the `DataInsightsAPIError` inherit from the `Exception` class

## 37.0.0

**BREAKING:** Rename `SpotlightAPIClient` to `DataInsightsAPIClient` as not all methods on it are specifically for spotlight
Add the `get_cyber_essentials_certificate` for getting Cyber Essentials certificates from the cert number

## 36.0.2

Refactor the evaluation lot section a bit

## 36.0.1

Update to evaluation lot section to be locked

## 36.0.0

Major changes to the way lot question models (Evaluation, TAC and Lot Pricing) work
Add modes to the API client to limit watch endpoints can be called

## 35.0.1

Remove endpoints for logging tasks in the audit logs

## 35.0.0

Add the tasks API client for the background jobs
Add endpoints for logging tasks in the audit logs

## 34.2.0

Revert partial update of the calls to export suppliers and users
Allow optional lot parts to be called with `get_supplier_frameworks`

## 34.1.0

Update the calls to export suppliers and users

## 34.0.0

Update calls to supplier frameworks to not include data from joined tables by default

## 33.1.0

Pass the organisation name when sending the Spotlight warmup request

## 33.0.0

Add new Spotlight FVRA Clients for warm up call and checking multiple DUNS
Update the Spotlight FVRA API Client to be a single client which calls the different clients

## 32.2.0

Add the Spotlight FVRA API client to the other API clients

## 32.0.0

Add the Spotlight DUNS API client to the other API clients

## 31.0.0

Make major changes for communications methods

## 30.0.0

Add the Central Digital Platform (CDP) API client to the other API clients

## 29.12.2

Update the `pyproject.toml` to add dev dependancies

## 29.0.0

Update the lot questions reponses routes
Remove old evaluator questions routes
Add routes relating to evaluations

## 28.0.0

Make Python 3.11 the minimum supported version
Add support for Python 3.13

## 27.3.0

Replace `setup.py` with `pyproject.toml`

## 27.0.0

Require the agreement details when creating a framework agreement

## 26.0.0

Rename Supplier Evaluation methods to Lot Questions Response

## 25.9.0

Add support for Python 3.12

## 25.4.0

Rename `conversation` methods to `communication` as this is the term we are using for the model and routes now

## 25.3.0

Add the API client methods for the conversation messages routes

## 25.2.0

Add new audit types for conversation messages

## 25.1.0

Allow for use with all currently maintained Python versions:
- 3.9
- 3.10
- 3.11

Note, because request-mock does not support 3.12 yet, neither can we.

## 25.0.0

Create the ccs-digitalmarketplace-apiclient from the original [digitalmarketplace-apiclient](https://github.com/Crown-Commercial-Service/digitalmarketplace-apiclient/pulls).

For all changes before this version, please see the [digitalmarketplace-apiclient CHANGELOG](https://github.com/Crown-Commercial-Service/digitalmarketplace-apiclient/blob/main/CHANGELOG.md).
