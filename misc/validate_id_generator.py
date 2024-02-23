#!/usr/bin/env python3

from npg_id_generation.pac_bio import PacBioEntity, concatenate_tags
from sqlalchemy import select

from lang_qc.db.mlwh_connection import get_mlwh_db
from lang_qc.db.mlwh_schema import PacBioRunWellMetrics

session = next(get_mlwh_db())

count = 0
num_mismatches = 0
for well in session.execute(select(PacBioRunWellMetrics)).scalars():
    id_generated = PacBioEntity(
        run_name=well.pac_bio_run_name,
        well_label=well.well_label,
        plate_number=well.plate_number,
    ).hash_product_id()
    if well.id_pac_bio_product != id_generated:
        num_mismatches += 1
        print(f"Mismatch for stored ID {well.id_pac_bio_product}")
    count += 1

print(f"{count} PacBioRunWellMetrics records examined, {num_mismatches} mismatches")

count = 0
num_mismatches = 0
unlinked = 0
for well in session.execute(select(PacBioRunWellMetrics)).scalars():
    for product in well.pac_bio_product_metrics:
        run = product.pac_bio_run
        if run is None:
            unlinked += 1
            continue
        tags = []
        if run.tag_sequence is not None:
            tags.append(run.tag_sequence)
            if run.tag2_sequence is not None:
                tags.append(run.tag2_sequence)
        tags_string = concatenate_tags(tags) if len(tags) else None
        id_generated = PacBioEntity(
            run_name=well.pac_bio_run_name,
            well_label=well.well_label,
            plate_number=well.plate_number,
            tags=tags_string,
        ).hash_product_id()
        if product.id_pac_bio_product != id_generated:
            num_mismatches += 1
            print(f"Mismatch for stored ID {well.id_pac_bio_product}")
        count += 1

print(f"{count} PacBioProductlMetrics records examined, {num_mismatches} mismatches")
print(f"{unlinked} product rows are not linked to LIMS data")
