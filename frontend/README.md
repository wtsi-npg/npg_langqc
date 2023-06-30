# npg-longue-vue

This is a user interface intended to aid manual QC. It aims to fulfill the same role as npg_qc_viewer does for Illumina QC data.

It is written in Javascript using the Vue 3 framework, and expects to interact with a backend API for retrieving and annotating QC data. The backend API will demand Okta authentication before any data will be transferred.

## Recommended IDE Setup

[VSCode](https://code.visualstudio.com/) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur)
ESLint, Pylance, isort

## Customize configuration

See [Vite Configuration Reference](https://vitejs.dev/config/).

## Project Setup

- Install node.js, perhaps using `nvm`
- npm install
- npm run test

### Compile and Hot-Reload for Development

```sh
npm run dev
```

The dockerdev run action exists to be run in the full-stack dev environment.
Running in dev mode as above will immediately expose challenges w.r.t. CORS
restrictions and for the backend host. Good luck with that.

### Compile and Minify for Production

```sh
npm run build
```

### Lint with [ESLint](https://eslint.org/)

```sh
npm run lint
```
