# Change Log for LangQC Project

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased] - yyyy-mm-dd

### Added

* Display the library_tube_barcode / Pool name in the QC View
* Calculate and display deplexing percentages when appropriate

### Changed

* Modified the search-by-run interface to allow multiple runs to be shown at once

## [1.1.0] - 2023-05-30

### Added

* Bookmarkable URLs
* Support for back/forward browser buttons
* Dedicated per-run view via /ui/run/$RUN_NAME
* Search box to jump to the per-run view (exact match only)
* QC View well now links to SMRTLink to help users find demux data more easily

### Changed

* ORM for ML warehouse selectively cloned into this repo to remove dependency on unsupported code
* Warehouse mapping updated to include additional PacBio-related columns

### Fixed

Run table was rendering the same data for all tabs. Now it only renders once for the selected tab

## [1.0.1] - 2022-03-14

### Changed

UI colour scheme and layout, the former to make it more coherent, the latter
to reduce unused white space on the top of the page.

## [1.0.0] - 2022-03-06

First production release.
