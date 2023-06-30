# Background

`npg_langqc` comprises an API server, a DB schema and a frontend GUI to enable users to assess long-read sequencing outcomes. In principle we are able to expand to support any post-sequencing QC assessments. The "long-read" distinguishes between our primarily Illumina short-read sequencing pipeline and the later adopted ONT, Pac Bio etc. machines. The Illumina short-read QC system cannot be reasonably extended to support other non-Illumina sequencers due to deeply embedded assumptions about operations and naming conventions.

## Tech choices

### Backend

A Python FastAPI server was developed to protect the interface from needing to understand the highly volatile multi-LIMS warehouse (MLWH) schema. It would also allow programatic querying of the QC schema, but there is no immediate demand for that. FastAPI automatically generates OpenAPI definitions.

The MLWH schema is hosted on a MySQL server, so the QC schema owned by this application was deployed to MySQL as well. `sqlalchemy` can support other DB engines.

### Frontend

The frontend was developed as a single page application using the `Vue 3` framework. Vue was chosen on account of the amount of other Vue applications developed within the institute. A prototype was trialled with Svelte but we had no supportive culture to help fledgling development along. Vue 3 was chosen in preference to Vue 2 in the hope of supporting `typescript` amongst other things, but it proved very difficult for an inexperienced web developer to integrate Vue 3 and typescript together with other features. Attempts to use the OpenAPI spec of the backend to generate a client library were unsuccessful, and the client code lacks a "nice" way to access the data. Further effort might be rewarded, see [fastapi docs](https://fastapi.tiangolo.com/advanced/generate-clients/).

### Environment

The whole application has been containerised with Docker and the development and production instances are hosted on virtual machines in OpenStack.

Deployment has been automated to a degree via OpenStack API and Ansible playbook, see the gitlab-hosted `langqc_deploy` project for deployment instructions.

### Authentication

Authentication is managed by Okta and a reverse-proxy server (Apache) that redirects users as required. The application can therefore be opened to all staff without risk to data integrity, and both backend and frontend components do not need to implement authentication. Authorisation is handled by a manually curated user list in the QC DB. The backend API can then control who is allowed make changes to QC outcomes.

As a consequence, development outside of the institutional network requires an Okta.com dev account. As of 2023 we have not needed granular authorisation.
