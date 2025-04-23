# CCS Digital Marketplace API clients changelog

Records breaking changes from major version bumps

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
