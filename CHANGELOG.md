# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-04-20

### Added
- Support for OKQ8 API integration alongside existing henrikhjelm.se API fallback.
- Environment variable support for OKQ8 subscription key via `.env` file.
- Home Assistant config flow for entering API key directly or using env fallback.
- Pagination support in OKQ8 API fetching to handle large datasets.
- Improved error handling for API responses and missing data.
- Compilation and validation of all Python files for syntax correctness.

### Changed
- Updated `update_prices.py` to fetch from OKQ8 API and format output as JSON.
- Modified sensor coordinator to use old API data first, then fallback to OKQ8 if data is missing or zero.
- Removed dependency on `apisvar.txt` for data persistence in the script.
- Enhanced config flow to include API key input with environment fallback.

### Fixed
- Handled NoneType addresses in API responses.
- Resolved API 401 errors by properly loading subscription key.
- Fixed corrupt data issues in previous implementations.

### Security
- Ensured API keys are loaded from environment variables or user input, not hardcoded.
- Added .gitignore to exclude sensitive files like .env.

### Author
- Victor Lindholm