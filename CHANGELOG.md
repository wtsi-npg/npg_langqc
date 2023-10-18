# Change Log for LangQC Project

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [1.5.0]

### Added

* Back-end code for the 'Upcoming' tab. The 'Upcoming' tab is
  automatically appended to the collection of the UI tabs for
  filtering wells.

### Changed

* Increased the look-back period for the inbox query from 4 weeks to
  12 weeks. Introduced a preliminary filtering by the QC state, which is
  now available in ml warehouse. Since the ml warehouse QC state might not
  be up-to-date, a final check against the LangQC database is retained.
* Major upgrade of FastAPI, Pydantic and related dependencies.

## [1.4.1] - 2023-08-23

### Added

* Display of the release version in UI.
* A constraint for `Claimed` QC state, made it applicable for `sequencing`
  QC type only.

### Changed

* Split the code for creating and updating QC sates into PacBio-specific
  and sequencing platform independent. Converted all methods to self-
  contained functions, discontinued use of classes where no object state
  has to be maintained.

### Fixed

* UI - ensured uniqueness of the row key for the well table.
* A bug in creating a new product record in the LangQC database.
  The bug affected records with undefined value of the plate number,
  which was pushed to the database as a `'None'` string instead of `NULL`.

## [1.4.0] - 2023-08-16

### Added

* Tests for bulk retrieval of QC states
* Third dimension for describing wells added to QC Schema to support multi-plate runs

### Changed

* Browser URLs now use id_product to identify items to show in the QC Viewer instead of the combination of run, label (and plate number)
* More strict validation of checksums (id_product) when sent to backend API

### Fixed

* A bug that disregarded the value of the `sequencing_outcomes_only`
argument in what is now the `get_qc_states_by_id_product_list` function

## [1.3.0] - 2023-08-02

### Added

* Instrument name and type and plate number concatenated with the
  well label is added to QC View and table of wells
* Loading concentration is added to the QC View

### Changed

* plate_number and id_product is added to API JSON feeds for well data

## [1.2.0] - 2023-07-12

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
