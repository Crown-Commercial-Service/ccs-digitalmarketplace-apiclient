# CCS Digital Marketplace API clients changelog

Records breaking changes from major version bumps

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
