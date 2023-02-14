# QC Process

## Human interaction

The following manual workflow applies:

1. A member of the QC team claims a task of qc-ing a well for themselves.
2. A member of the QC team assigns a preliminary QC state to a well,
which they claimed. This action can be performed repeatedly.
3. A member of the QC team marks the current state of the well as final
(this is not applicable to the `Claimed`, `On hold` and `Aborted` states).

The following rules will be implemented on the back-end:

- Only those in the user table can change the QC state of the well.
- Only the person who claimed the well's QC can perform further updates of
the state.
- 'Unclaimed' wells cannot change their QC state. This might change later
in order to enable automation of the QC process.

Further versions of the application will implement a feature that transfers
the ownership of the well's QC to a different member of the QC team.

## Automation

Periodically a PacBio loader tool will attempt to upload the QC results to
the warehouse. Due to upstream processes, the related content of the warehouse
can not be relied upon to remain static. A sliding window of 180 days of
products will be updated using the latest state from the QC database.

In order to support a bulk refresh of QC states in the warehouse, the loader
will routinely request large numbers of QC results by `id_product`. An API
endpoint (/api/products/qc) is implemented to support this and can be queried
without authentication:

```bash
curl -X POST -H "Accept: application/json" -H "Content-Type: application/json" https://my_server/api/products/qc -d '["2c5d78744a4af61ac6d8fe287d50abdf10a36b57b0f5df3e155995178c58d96e"]'

> {"2c5d78744a4af61ac6d8fe287d50abdf10a36b57b0f5df3e155995178c58d96e":[{"qc_state":"Passed","is_preliminary":false,"qc_type":"sequencing","outcome":true,"id_product":"2c5d78744a4af61ac6d8fe287d50abdf10a36b57b0f5df3e155995178c58d96e","date_created":"2022-11-14T09:57:14","date_updated":"2022-11-11T00:00:00","user":"user@my_domain.com","created_by":"BACKFILLING"}]}
```
