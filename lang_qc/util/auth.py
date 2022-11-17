from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from lang_qc.db.qc_connection import get_qc_db
from lang_qc.db.qc_schema import User


def check_user(
    oidc_claim_email: str | None = Header(default=None, convert_underscores=False),
    qcdb_session: Session = Depends(get_qc_db),
) -> User:
    """
    Check that an email provided the request header belongs to a person who is
    authorized to perform manual QC or other operations that require authorization.
    Return the lang_qc.db.qc_schema.User object.

    Raises an HTTPException error if the user email is not present in the header
    or if the authenticated user is authorized to perform whatever operation was
    requested.

    While it looks like a new session will be created here to resolve
    """

    # Status code 407 might be more appropriate, 401 is fine for now.
    if oidc_claim_email is None:
        raise HTTPException(
            status_code=401, detail="No user provided, is the user logged in?"
        )

    user = get_user(oidc_claim_email, qcdb_session)
    if user is None:
        raise HTTPException(
            status_code=403,
            detail="The user is not authorized to perform this operation.",
        )

    return user


def get_user(username: str, session: Session) -> User | None:
    """
    Returns a lang_qc.db.qc_schema.User object or None if the user with
    this username does not exist.
    """

    return session.execute(
        select(User).filter(User.username == username)
    ).scalar_one_or_none()
