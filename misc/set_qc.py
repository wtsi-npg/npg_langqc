import argparse

from sqlalchemy import select

from lang_qc.db.helper.qc import assign_qc_state_to_product, claim_qc_for_product
from lang_qc.db.helper.well import well_seq_product_find_or_create
from lang_qc.db.helper.wells import WellWh
from lang_qc.db.mlwh_connection import get_mlwh_db
from lang_qc.db.qc_connection import get_qc_db
from lang_qc.db.qc_schema import User
from lang_qc.models.qc_state import QcStateBasic

cli_parser = argparse.ArgumentParser(
    description="""
    Script for overriding/creating a QC outcome without needing to go
    through Okta or the GUI.
    """
)
cli_parser.add_argument(
    "--id_product", required=True, help="SHA256 digest of a product ID"
)
cli_parser.add_argument(
    "--preliminary", type=bool, action=argparse.BooleanOptionalAction
)
cli_parser.add_argument(
    "--user",
    required=True,
    help="Email for who we're masquerading as. Must be registered in the QC DB",
)
cli_parser.add_argument(
    "--state",
    required=True,
    help="The QC outcome we're looking to set, e.g. Passed, 'On-hold'",
)
cli_parser.add_argument("--ticket", required=True, help="Supply a ticket ID")


def main():
    args = cli_parser.parse_args()
    # TODO: Allow manual input of run, well and plate at CLI
    mlwh_session = next(get_mlwh_db())
    qc_session = next(get_qc_db())

    helper = WellWh(session=mlwh_session)
    mlwh_well = helper.get_mlwh_well_by_product_id(args.id_product)
    if mlwh_well is None:
        print("id_product not present in the MLWH")
        exit(1)

    user = (
        qc_session.execute(select(User).where(User.username == args.user))
        .scalars()
        .one()
    )
    seq_product = well_seq_product_find_or_create(qc_session, mlwh_well)

    claim_qc_for_product(qc_session, seq_product, user=user)

    new_qc_state = assign_qc_state_to_product(
        qc_session,
        seq_product,
        QcStateBasic(
            qc_state=args.state, is_preliminary=args.preliminary, qc_type="sequencing"
        ),
        user,
        application=f"Script-{args.ticket}",
    )
    print(f"Change made to: {new_qc_state}")
    exit()


if __name__ == "__main__":
    main()
