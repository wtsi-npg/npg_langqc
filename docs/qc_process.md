# QC Process

The following manual workflow will be implemented in the first production
version of the application:

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

Further versions of the application might implement a feature that transfers
the ownership of the well's QC to a different member of the QC team. 


