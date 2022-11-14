#!/usr/bin/env python3

from datetime import datetime

from npg_id_generation.pac_bio import PacBioEntity
from sqlalchemy import select

import lang_qc.util.qc_state_helpers as qsh
from lang_qc.db.qc_connection import get_qc_db
from lang_qc.db.qc_schema import QcState as QcStateDB
from lang_qc.db.qc_schema import SeqProduct, User
from lang_qc.db.utils import get_qc_state_dict, get_qc_type, get_user

"""
This script loads QC outcomes for a small number of wells to
lang_qc database. It does not create historical entries, therefore
should not be used for loading production data.
"""

# In runs up to 290 all wells have multiple samples.
# In runs above 290 all wells have one sample.

flat_list = [
    "TRACTION-RUN-295",
    "B1",
    "TRACTION-RUN-295",
    "A1",
    "TRACTION-RUN-296",
    "B1",
    "TRACTION-RUN-296",
    "A1",
    "TRACTION-RUN-298",
    "A1",
    "TRACTION-RUN-298",
    "B1",
    "TRACTION-RUN-299",
    "B1",
    "TRACTION-RUN-299",
    "A1",
    "TRACTION-RUN-297",
    "B1",
    "TRACTION-RUN-297",
    "A1",
    "TRACTION-RUN-294",
    "B1",
    "TRACTION-RUN-294",
    "A1",
    "TRACTION-RUN-293",
    "B1",
    "TRACTION-RUN-293",
    "A1",
    "TRACTION-RUN-291",
    "D1",
    "TRACTION-RUN-291",
    "C1",
    "TRACTION-RUN-291",
    "B1",
    "TRACTION-RUN-291",
    "A1",
    "TRACTION-RUN-292",
    "D1",
    "TRACTION-RUN-292",
    "C1",
    "TRACTION-RUN-290",
    "D1",
    "TRACTION-RUN-290",
    "C1",
    "TRACTION-RUN-290",
    "B1",
    "TRACTION-RUN-290",
    "A1",
    "TRACTION-RUN-263",
    "D1",
    "TRACTION-RUN-263",
    "C1",
    "TRACTION-RUN-263",
    "B1",
    "TRACTION-RUN-263",
    "A1",
]

user_name = "user_1"
qc_type = "sequencing"
session = next(get_qc_db())  # QCDB_URL env. variable should be set
qc_state_dict_obj = get_qc_state_dict("Claimed", session)
qc_type_obj = get_qc_type(qc_type, session)

user_obj = get_user(user_name, session)
if user_obj is None:
    user_obj = User(username=user_name)
    session.add(user_obj)

states = []

num_wells = int(len(flat_list) / 2)
for i in range(num_wells):
    index = 2 * i
    run = flat_list[index]
    label = flat_list[index + 1]
    id = PacBioEntity(run_name=run, well_label=label).hash_product_id()

    # Find or create the product record
    seq_product = session.execute(
        select(SeqProduct).where(SeqProduct.id_product == id)
    ).scalar_one_or_none()
    if seq_product is None:
        seq_product = qsh.construct_seq_product_for_well(run, label, session)

    # Find or create the QC record
    id_seq_product = seq_product.id_seq_product
    qc_state_obj = session.execute(
        select(QcStateDB).where(QcStateDB.id_seq_product == id_seq_product)
    ).scalar_one_or_none()
    if qc_state_obj is None:
        # claim QC for every well
        qc_state_obj = QcStateDB(
            created_by="loader",
            is_preliminary=True,
            qc_state_dict=qc_state_dict_obj,
            qc_type=qc_type_obj,
            id_seq_product=id_seq_product,
            user=user_obj,
        )
        session.add(qc_state_obj)

    states.append(qc_state_obj)

dict_states = [
    "Passed",
    "Failed",
    "Failed, SMRT cell",
    "Failed",
    "Undecided",
    "On hold",
]

if (num_wells - 3) < len(dict_states):
    raise Exception("Need more input wells")

count = 0
# Assign a different state to most of entities.
# In each group naively finalise some states.
for dict_state in dict_states:
    for i in range(4):
        obj = states[count]
        is_preliminary = True
        if i == 0:
            is_preliminary = False
        obj.date_updated = datetime.now()
        obj.qc_state_dict = get_qc_state_dict(dict_state, session)
        obj.is_preliminary = is_preliminary
        session.add(qc_state_obj)  # Some objects are added second time.
        # Will this work?
        count = count + 1

session.commit()
