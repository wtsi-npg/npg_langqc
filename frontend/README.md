# npg-longue-vue

This is a user interface intended to aid manual QC. It aims to fulfill the same role as npg_qc_viewer does for Illumina QC data.

It is written in Javascript using the Vue 3 framework, and expects to interact with a backend API for retrieving and annotating QC data. The backend API will demand Okta authentication before any data will be transferred.

## Recommended IDE Setup

[VSCode](https://code.visualstudio.com/) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur) + [TypeScript Vue Plugin (Volar)](https://marketplace.visualstudio.com/items?itemName=Vue.vscode-typescript-vue-plugin).

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

### Run End-to-End Tests with [Cypress](https://www.cypress.io/)

```sh
npm run build
npm run test:e2e # or `npm run test:e2e:ci` for headless testing
```

### Lint with [ESLint](https://eslint.org/)

```sh
npm run lint
```

Note that ESLint, cypress config files and vue3 components do not get on.
Expect to see warnings like "props is not defined" and similar, and the
format settings for config.js files versus modules causes one or the other to
fail. Improve `.eslintrc.json` at your leisure.
