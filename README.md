Digital Marketplace API client
=========================

![Python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)
![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)

## What's in here?

API clients for Digital Marketplace [Data API](https://github.com/Crown-Commercial-Service/ccs-digitalmarketplace-api) and
[Search API](https://github.com/Crown-Commercial-Service/ccs-digitalmarketplace-search-api).

Originally was part of [Digital Marketplace Utils](https://github.com/Crown-Commercial-Service/ccs-digitalmarketplace-utils).


## Running the tests

Install Python dependencies:

```
make bootstrap
invoke requirements-dev
```

Run the tests:

```
invoke test
```

## Usage examples

```python

data_client = apiclient.DataAPIClient(api_url, api_access_token)
services = data_client.find_services_iter(framework=frameworks)

```

## Releasing a new version

To update the package version, edit the `__version__ = ...` string in `dmapiclient/__init__.py`,
commit and push the change and wait for CI to create a new version tag.

Once the tag is available on GitHub, the new version can be used by the apps by adding the following
line to the app `requirements.txt` (replacing `X.Y.Z` with the current version number):

```
git+https://github.com/Crown-Commercial-Service/ccs-digitalmarketplace-apiclient.git@X.Y.Z#egg=ccs-digitalmarketplace-apiclient==X.Y.Z
```

When changing a major version number consider adding a record to the `CHANGELOG.md` with a
description of the change and an example of the upgrade process for the client apps.

## Licence

Unless stated otherwise, the codebase is released under [the MIT License][mit].
This covers both the codebase and any sample code in the documentation.

The documentation is [&copy; Crown copyright][copyright] and available under the terms
of the [Open Government 3.0][ogl] licence.

[mit]: LICENCE
[copyright]: http://www.nationalarchives.gov.uk/information-management/re-using-public-sector-information/uk-government-licensing-framework/crown-copyright/
[ogl]: http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/
