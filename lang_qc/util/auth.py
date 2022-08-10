from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from lang_qc.db.qc_connection import get_qc_db
from lang_qc.db.qc_schema import User
from lang_qc.db.utils import get_user


def check_user(
    oidc_claim_email: str | None = Header(default=None, convert_underscores=False),
    qcdb_session: Session = Depends(get_qc_db),
) -> User:
    """Check that a user provided in a header is registered and return the user, or error."""

    if oidc_claim_email is None:
        raise HTTPException(
            status_code=401, detail="No user provided, is the user logged in?"
        )

    user = get_user(oidc_claim_email, qcdb_session)
    if user is None:
        raise HTTPException(
            status_code=400,
            detail="User has not been found in the QC database. Have they been registered?",
        )

    return user
