# Copyright (c) 2022 Genome Research Ltd.
#
# Author: Adam Blanchet <ab59@sanger.ac.uk>
#
# This file is part of npg_langqc.
#
# npg_langqc is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.

from typing import List, Tuple

from ml_warehouse.schema import PacBioRunWellMetrics
from sqlalchemy import and_, not_, or_, select
from sqlalchemy.orm import Session

from lang_qc.db.qc_schema import (
    ProductLayout,
    QcState,
    QcStateDict,
    QcType,
    SeqProduct,
    SubProduct,
    User,
)
from lang_qc.models.pacbio.well import WellStatusEnum


def grab_wells_from_db(db_session: Session) -> List[PacBioRunWellMetrics]:
    """Get completed wells from the from the database."""

    ######
    # It is important not to show aborted wells in the inbox.
    #
    # The well can be complete as in Illumina 'run complete' but that's not
    # the same as analysis complete which the other conditions are trying for.
    # It potentially gets a bit easier with v11 but those conditions should
    # still work ok.
    #
    stmt = select(PacBioRunWellMetrics).filter(
        and_(
            PacBioRunWellMetrics.polymerase_num_reads is not None,
            or_(
                and_(
                    PacBioRunWellMetrics.ccs_execution_mode.in_(
                        ("OffInstrument", "OnInstrument")
                    ),
                    PacBioRunWellMetrics.hifi_num_reads is not None,
                ),
                PacBioRunWellMetrics.ccs_execution_mode == "None",
            ),
            PacBioRunWellMetrics.well_status == WellStatusEnum.COMPLETE,
        )
    )

    return db_session.execute(stmt).scalars().all()


def extract_well_label_and_run_name_from_state(state: QcState):
    """Get the well label and run name from a QcState.

    This assumes there is a 1-1 SeqProduct-SubProduct mapping.
    """

    return (
        state.seq_product.product_layout[0].sub_product.value_attr_one,
        state.seq_product.product_layout[0].sub_product.value_attr_two,
    )


def get_well_metrics_from_qc_states(
    qc_states: List[QcState], mlwh_db_session: Session
) -> List[PacBioRunWellMetrics]:
    """Get a list of PacBioRunWellMetrics corresponding to QC states.

    This assumes there is a 1-1 SeqProduct-SubProduct mapping.
    """

    # if qc_states is empty then there are no corresponding states.
    if len(qc_states) == 0:
        return []

    state_info = [
        extract_well_label_and_run_name_from_state(state) for state in qc_states
    ]
    filters = [
        and_(
            PacBioRunWellMetrics.pac_bio_run_name == run_name,
            PacBioRunWellMetrics.well_label == well_label,
        )
        for run_name, well_label in state_info
    ]

    stmt = select(PacBioRunWellMetrics).where(or_(*filters))

    wells: List[PacBioRunWellMetrics] = mlwh_db_session.execute(stmt).scalars()
    return wells


def get_inbox_wells_and_states(qcdb_session: Session, mlwh_session: Session):
    """Get a pair of lists of inbox PacBioRunWellMetrics and QcState.

    The list of states will always be empty.
    """

    # Get wells, then filter out all those that already have QC state assigned.

    recent_wells = grab_wells_from_db(mlwh_session)

    stmt = (
        select(QcState)
        .join(SeqProduct)
        .join(ProductLayout)
        .join(SubProduct)
        .where(
            or_(
                *[
                    and_(
                        SubProduct.value_attr_one == well.pac_bio_run_name,
                        SubProduct.value_attr_two == well.well_label,
                    )
                    for well in recent_wells
                ]
            )
        )
    )

    already_there = [
        extract_well_label_and_run_name_from_state(state)
        for state in qcdb_session.execute(stmt).scalars().all()
    ]

    wells = [
        record
        for record in recent_wells
        if (record.pac_bio_run_name, record.well_label) not in already_there
    ]

    return (wells, [])


def get_on_hold_wells_and_states(
    qcdb_session: Session, mlwh_session: Session
) -> Tuple[List[PacBioRunWellMetrics], List[QcState]]:
    """Get a pair of lists of on_hold PacBioRunWellMetrics and QcState."""

    # Get wells which have a state that is "On hold".
    states = (
        qcdb_session.execute(
            select(QcState).join(QcStateDict).where(QcStateDict.state == "On hold")
        )
        .scalars()
        .all()
    )
    wells = get_well_metrics_from_qc_states(states, mlwh_session)

    return (wells, states)


def get_in_progress_wells_and_states(
    qcdb_session: Session, mlwh_session: Session
) -> Tuple[List[PacBioRunWellMetrics], List[QcState]]:
    """Get a pair of lists of in_progress PacBioRunWellMetrics and QcState."""

    # Get wells which have a state that is not "On hold" or preliminary.
    states = (
        qcdb_session.execute(
            select(QcState)
            .join(QcStateDict)
            .where(and_(QcStateDict.state != "On hold", QcState.is_preliminary))
        )
        .scalars()
        .all()
    )
    wells = get_well_metrics_from_qc_states(states, mlwh_session)

    return (wells, states)


def get_qc_complete_wells_and_states(
    qcdb_session: Session, mlwh_session: Session
) -> Tuple[List[PacBioRunWellMetrics], List[QcState]]:
    """Get a pair of lists of qc_complete PacBioRunWellMetrics and QcState."""

    # Get wells which have a state that is not "On hold" or "Claimed" and that
    # is not preliminary.
    states = (
        qcdb_session.execute(
            select(QcState)
            .join(QcStateDict)
            .where(
                and_(
                    not_(QcState.is_preliminary),
                    not_(QcStateDict.state.in_(["On hold", "Claimed"])),
                )
            )
        )
        .scalars()
        .all()
    )

    wells = get_well_metrics_from_qc_states(states, mlwh_session)

    return (wells, states)


def get_user(username: str, qcdb_session: Session) -> User | None:
    """Get a user from the database."""

    return qcdb_session.execute(
        select(User).filter(User.username == username)
    ).scalar_one_or_none()


def get_well_metrics(
    run_name: str, well_label: str, mlwh_session: Session
) -> PacBioRunWellMetrics | None:
    """Get a well from the metrics database."""

    return mlwh_session.execute(
        select(PacBioRunWellMetrics).where(
            and_(
                PacBioRunWellMetrics.pac_bio_run_name == run_name,
                PacBioRunWellMetrics.well_label == well_label,
            )
        )
    ).scalar_one_or_none()


def get_qc_state_dict(state_name: str, qcdb_session: Session) -> QcStateDict | None:
    """Get a QC state variant from a name."""

    return qcdb_session.execute(
        select(QcStateDict).where(QcStateDict.state == state_name)
    ).scalar_one_or_none()


def get_qc_type(type_name: str, qcdb_session: Session) -> QcType | None:
    """Get a QC type from a name."""
    return qcdb_session.execute(
        select(QcType).where(QcType.qc_type == type_name)
    ).scalar_one_or_none()
