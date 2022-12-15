#!/usr/bin/env python3

from datetime import datetime

import numpy
import pandas
from ml_warehouse.schema import PacBioRunWellMetrics
from sqlalchemy import select

from lang_qc.db.helper.well import WellMetrics, WellQc
from lang_qc.db.mlwh_connection import get_mlwh_db
from lang_qc.db.qc_connection import get_qc_db
from lang_qc.util.auth import get_user


def check_df_shape(df, message):
    print(message)
    print(df.shape)
    assert df.empty is False, "Dataframe is empty"


def convert_well_label(well_label):
    if isinstance(well_label, str) and well_label:
        # Drop zero from labels like D01
        return well_label.replace("0", "")
    return well_label


def get_date(date_string, well_metrics):

    # If the row does not have 'QC Complete date', fill it in from the mlwh data.
    # Ideally we want UTC timestamps, but will use whatever we have for now.

    qc_date = None
    if isinstance(date_string, str) and date_string:
        qc_date = datetime.strptime(date_string, "%d/%m/%Y")
    else:
        qc_date = well_metrics.run_complete
        if qc_date is None:
            qc_date = well_metrics.run_start
        if qc_date is None:
            raise Exception(
                f"Both run complete and start dates are missing for {run} {well}"
            )
    return qc_date


def convert_run_name(run_name):
    return run_name.replace("TRAC-", "TRACTION-")


def well_metrics_from_movie(session, movie_id):
    return session.execute(
        select(PacBioRunWellMetrics).where(
            PacBioRunWellMetrics.movie_name == movie_id,
        )
    ).scalar_one_or_none()


file = "misc/data2export-well_data.tsv"
# For now not reading columns with comments, ie
# 'Run Comments', 'Complex Comments', 'Reason for Failure'
columns = [
    "Run ID",
    "Well Location",
    "Run Date",
    "Status",
    "QC Complete date",
    "Movie ID",
]

converters = {
    "Run ID": convert_run_name,
    "Well Location": convert_well_label,
}
# "QC Complete date": convert_date

df = pandas.read_csv(
    filepath_or_buffer=file,
    sep="\t",
    on_bad_lines="warn",
    index_col=False,
    usecols=columns,
    skipinitialspace=True,
    converters=converters,
)
check_df_shape(df, "Parsed the file")
df.replace(to_replace="#REF!", value=numpy.nan, inplace=True)
# df.dropna(how="all", inplace=True)

for index, row in df.isnull().iterrows():
    # Iterating over a dataframe where True values replaced the NaNs,
    # False values replaced the rest. The values in the matrix are of type numpy.bool_,
    # which is a subtype of Python bool. These values cannot be compared to Python
    # True or False directly.
    # Are any of these values missing? Yes - delete the row from the master dataframe.
    if bool(row["Run ID"]) is True or bool(row["Status"]) is True:
        df.drop(axis=0, index=index, inplace=True)

check_df_shape(df, "Removed rows with missing data")

# Get mlwh db connection.
session = next(get_mlwh_db())
df_nulls = df.isnull()
to_drop = []

for col_name in ("Run ID", "Well Location", "Movie ID"):
    df[col_name].str.strip()

for index, row in df.iterrows():

    run = row["Run ID"]
    well = row["Well Location"]
    well_metrics = None

    if isinstance(well, str) and well != "":
        well_metrics = WellMetrics(
            run_name=run, well_label=well, session=session
        ).get_metrics()
    else:
        movie_id = row["Movie ID"]
        if isinstance(movie_id, str):
            well_metrics = well_metrics_from_movie(session, movie_id)
            if well_metrics:
                # Save well label, which we will need later.
                df.at[index, "Well Location"] = well_metrics.well_label

    # Do this run and well exist in mlwh?
    if well_metrics is None:
        # No - mark the row for deletion.
        to_drop.append(index)
    else:
        # Yes - deal with dates.
        df.at[index, "QC Complete date"] = get_date(
            row["QC Complete date"], well_metrics
        )

# Delete the rows which have been marked for deletion.
for index in to_drop:
    df.drop(axis=0, index=index, inplace=True)

check_df_shape(df, "Validated data against mlwh")

# What are distinct values in the 'Status' column and how do they map to the
# db dictionary values?
QC_OUTCOMES_MAP = {
    "PASS": ("Passed", False),
    "FAIL": ("Failed", False),
    "FAIL INSTRUMENT": ("Failed, Instrument", False),
    "ABORTED": ("Aborted", False),
    "ABORTED - NEW RUN": ("Aborted", False),
    "PENDING - PASS": ("Passed", True),
    "PENDING - FAIL": ("Failed", True),
}
for outcome in df["Status"].unique():
    assert outcome in QC_OUTCOMES_MAP, f"Unmapped QC outcome '{outcome}'"

print(df)

# Now we have a complete set of data and can assign QC outcomes.
# We do not know the user who assigned the outcomes in the spreadsheet, so we will use
# one of known users.

session = next(get_qc_db())

app_name = "BACKFILLING"
qc_type = "sequencing"

user_name = "xxx@sanger.ac.uk"
user_obj = get_user(user_name, session)
if user_obj is None:
    raise Exception(f"No user for {user_name}")

num_errors = 0
for index, row in df.iterrows():
    well_qc = WellQc(
        run_name=row["Run ID"], well_label=row["Well Location"], session=session
    )
    (qc_state, is_preliminary) = QC_OUTCOMES_MAP[row["Status"]]
    try:
        well_qc.assign_qc_state(
            user=user_obj,
            qc_state=qc_state,
            qc_type=qc_type,
            is_preliminary=is_preliminary,
            application=app_name,
            date_updated=row["QC Complete date"],
        )
    except Exception as e:
        print(f"Error for row index {index}:")
        print(e)
        num_errors += 1

print(f"Finished backfilling QC outcomes, number of errors - {num_errors}")
