# The QC schema is *very* generic

See also ./langqc_db_schema_*.pdf

The sequencing platforms have their own terminology and technology. Their differences are important, but not for the generalised question of "Did the experiment work?". Therefore an uncomfortable level of generalisation is required in the QC database to accommodate different platforms and granularities of quality control of their outputs. It is also challenging to choose good names for the generalisations!

## Products

A product in our schema is a "data output we feel needs some QC". It can consist of one or more observations (sic. `sub_product`). Typically a single `sub_product` may represent the data of a single flowcell or well of an instrument during a specific run, e.g. Well "A1" of run "TRACTION-RUN-123" (for PacBio), or position 2 of id_run 15703 (for Illumina). In order to support different platforms, the names for these two descriptors are defined in a separate table: `sub_product_attr`.

We reserve the possibility for unbundling multiplexed data, so that individual samples that go through the instrument in the same flowcell can be evaluated individually after the requisit processing. This is what the `tags` column is for.

Example: TRACTION-RUN-123 contains wells A1 and B1 (2 sub_products). That gives two QC records. If well A1 sequenced a multiplex of tagged DNA, we might then have multiple sub-products with the same labels. They can be evaluated together for the entire run, or on an individual basis defined via a `seq_product` and the many-to-many linker table `product_layout`.

## QC

A single `seq_product` can have several iterations of QC performed on it. Therefore we have a history table `qc_state_hist` that lists all of the QC states over time (including the latest), and the current state `qc_state`. The QC type relationship defines the focus of the QC, e.g. library assessment, or sequencing assessment. All QC states are set by a user (or script with a user account), can be marked as preliminary, and the possible settings are constrained to a vocabulary defined in `qc_state_dict`

## The Benefit

A `seq_product` is an arbitrary but useful combination of various data. Individual observations can inform multiple `seq_product`s, and each `seq_product` can receive QC of the types defined in `qc_type`. In this way we can allow QC on very specific pieces of data, and also support QC on collections of the data at a higher level without encoding the complexity into an explicit (and rigid) hierarchy in our database. We are somewhat future-proofed.
