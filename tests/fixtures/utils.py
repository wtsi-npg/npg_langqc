from sqlalchemy import delete

from lang_qc.db.mlwh_schema import (
    PacBioProductMetrics,
    PacBioRun,
    PacBioRunWellMetrics,
    Sample,
    Study,
)
from lang_qc.db.qc_schema import (
    ProductLayout,
    QcState,
    QcStateDict,
    QcType,
    SeqPlatform,
    SeqProduct,
    SubProduct,
    SubProductAttr,
    User,
)


def clean_mlwhdb(session):
    print("\nCLEAN mlwh schema")
    with session.begin():
        session.execute(delete(PacBioProductMetrics))
        session.execute(delete(PacBioRun))
        session.execute(delete(Study))
        session.execute(delete(Sample))
        session.execute(delete(PacBioRunWellMetrics))
        session.commit()


def clean_qcdb(session):
    with session.begin():
        print("\nCLEAN QC DB")
        session.execute(delete(QcState))
        session.execute(delete(ProductLayout))
        session.execute(delete(SeqProduct))
        session.execute(delete(SubProduct))
        session.execute(delete(QcType))
        session.execute(delete(SubProductAttr))
        session.execute(delete(SeqPlatform))
        session.execute(delete(User))
        session.execute(delete(QcStateDict))
        session.commit()
