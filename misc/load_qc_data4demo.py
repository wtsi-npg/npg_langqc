#!/usr/bin/env python3


import random

from lang_qc.db.helper.well import WellQc
from lang_qc.db.qc_connection import get_qc_db
from lang_qc.db.qc_schema import User
from lang_qc.util.auth import get_user

"""
This script loads QC outcomes for a small number of wells to the LangQC
database.

QCDB_URL environment variable should be set to point to the dev database.
"""

flat_list = [
    "TRACTION-RUN-125",
    "A1",
    "TRACTION-RUN-125",
    "B1",
    "TRACTION-RUN-125",
    "C1",
    "TRACTION-RUN-125",
    "D1",
    "TRACTION-RUN-126",
    "A1",
    "TRACTION-RUN-126",
    "B1",
    "TRACTION-RUN-126",
    "C1",
    "TRACTION-RUN-126",
    "D1",
    "TRACTION-RUN-128",
    "B1",
    "TRACTION-RUN-128",
    "A1",
    "TRACTION-RUN-128",
    "C1",
    "TRACTION-RUN-128",
    "D1",
    "TRACTION-RUN-129",
    "B1",
    "TRACTION-RUN-129",
    "A1",
    "TRACTION-RUN-129",
    "D1",
    "TRACTION-RUN-129",
    "C1",
    "TRACTION-RUN-131",
    "B1",
    "TRACTION-RUN-131",
    "C1",
    "TRACTION-RUN-131",
    "D1",
    "TRACTION-RUN-132",
    "C1",
    "TRACTION-RUN-132",
    "D1",
    "TRACTION-RUN-132",
    "A1",
    "TRACTION-RUN-132",
    "B1",
    "TRACTION-RUN-133",
    "A1",
    "TRACTION-RUN-133",
    "D1",
    "TRACTION-RUN-133",
    "C1",
    "TRACTION-RUN-133",
    "B1",
    "TRACTION-RUN-134",
    "A1",
    "TRACTION-RUN-134",
    "B1",
    "TRACTION-RUN-134",
    "C1",
]

application = "DB LOADER"
user_name = "user_1"
session = next(get_qc_db())

user_obj = get_user(user_name, session)
if user_obj is None:
    user_obj = User(username=user_name)
    session.add(user_obj)

states = []

num_wells = int(len(flat_list) / 2)

dict_states = [
    "Passed",
    "Failed",
    "Failed, SMRT cell",
    "Failed",
    "Undecided",
    "On hold",
]

for i in range(num_wells):
    index = 2 * i
    run = flat_list[index]
    label = flat_list[index + 1]
    helper = WellQc(run_name=run, well_label=label, session=session)
    helper.assign_qc_state(user=user_obj, application=application)
    index = random.randint(0, len(dict_states) - 1)
    state_name = dict_states[index]
    prelim = True
    if state_name != "On hold" and i / 2 == 0:
        prelim = False
    helper.assign_qc_state(
        user=user_obj,
        qc_state=state_name,
        is_preliminary=prelim,
        application=application,
    )
