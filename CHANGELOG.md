# Change Log for LangQC Project

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]

## [2.3.0] - 2024-07-30

### Added

* New endpoint for fetching statistics about a library pool
* Pool composition table added to the QC View for any well. Folded away by default
* Barcode names from MLWH are now available to front and back end code

### Fixed

* Well detail fetching errors now produce a visible warning that was previously lost

## [2.2.0] - 2024-06-11

### Added

* New endpoint added to support potential email notifications when QC states are finalised. `/products/qc?weeks={n}&seq_level={bool}&final={bool}`. It returns recent QC events

### Fixed

* Warehouse schema updated to match breaking change in pac_bio_product_metrics table

## [2.1.0] - 2024-04-15

### Changed

* To simplify object instantiation and fields' assignment for some
  of the response models, converted `PacBioWell` and `PacBioWellFull`
  models to pydantic dataclasses.
* Changed the response model for filtered by either QC status or run wells from
  `PacBioWell` to `PacBioWellSummary`, the latter initially being identical
  the former. In order to propagate information about a study to the tabbed
  well summary view, added a new field, study_names, to the `PacBioWellSummary`
  model.
* Added a new event to the tabbed well summary view, to the button with the well
  name. Mouse hover over this button displays study names associated with the
  well.
* Changed the colour scheme of the above mentioned button from grey to orange
  if one of the studies associated with the well is the BIOSCAN study, which
  the QC team needs to deal with slightly differently.
* Added a new QC state 'On hold external'. Semantically the new state is similar
  to the existing 'On hold' state. The intended purpose of the new QC state - to
  highlight the wells, which are waiting for a completion of some off-site
  process (example - deplexing at http://mbrave.net/).

### Added

* A new response model `PacBioWellSummary`, which replaces `PacBioWell`
  in the latest's capacity of the response model for a PacBio well
  summary.
* A new field, `study_names`, a potentially empty sorted array of
  unique study names, is added to the response model for a PacBio
  well summary.

## [2.0.0] - 2024-02-20

### Changed

* The correctness of data in the 'properties' column of the
  LangQC 'sub_product' database table is no longer guaranteed
  because of the changes introduced in v. 5.0.0 of https://github.com/wtsi-npg/npg_id_generation
  The column is made nullable and then dropped. The ORM for
  the LangQC database is updated accordingly.

* The production code no longer depends on the npg_id_generation
  package, therefore this dependency was moved to the dev section
  of pyproject.toml. The package is still used by tests and test
  fixtures.

* Upgraded some of dev dependencies: npg_id_generation to 5.0.1,
  alembic to 1.13.0 or later.

* Regenerated poetry.lock file.

## [1.5.1] - 2024-01-25

### Changed

* The 'Unknown' UI tab no longer displays the wells that have any
  sequencing QC state associated with it. This feature was requested
  by the users.

* To increase code readability, renamed qc_state_for_product_exists
  method in lang_qc::db::helper::qc to product_has_qc_state.

* Added method products_have_qc_state to lang_qc::db::helper::qc,
  used it to optimise (reduce the number of database queries) some
  of the existing back-end code.

### Fixed

* The client side JavaScript dependency, element-plus, is pinned
  to version 2.4.4. In mid-January 2024 this was the highest version
  that worked with our code. The version expression we had "^2.3.7"
  allowed for fetching the latest available version of this library.

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
