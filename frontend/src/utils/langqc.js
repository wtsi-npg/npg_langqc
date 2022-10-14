import { join } from "lodash";

export default class LangQc {
  constructor() {
    this.urls = {
      run: this.buildUrl('/run')
    };
    this.commonHeaders = {
      'Accept': 'application/json'
    };
  }

  buildUrl(path = '', args) {
    let base = '/api/pacbio'; // Get app base path from build stage
    let search = '';

    if (Array.isArray(path)) {
      path = '/' + path.join('/');
    }
    if (Array.isArray(args)) {
      search = '?' + join(args, "&");
    }
    return base + path + search;
  }

  getUrl(alias) {
    return this.urls[alias];
  }

  syncFetch(route) {
    // Don't use this if you want async efficiency.
    // Returns a promise that ought to contain backend data
    return fetch(
      route,
      {
        headers: this.commonHeaders
      }
    ).then(
      response => {
        if (response.ok) {
          return response.json()
        } else {
          throw new Error("API fetch error " + response.statusText);
        }
      }
    )
  }

  getInboxPromise(qc_status='inbox', weeks=1, page_number=1, page_size=10) {
    return this.syncFetch(
      this.buildUrl(
        '/wells',
        [`qc_status=${qc_status}`, `weeks=${weeks}`, `page_size=${page_size}`, `page_number=${page_number}`]
      )
    );
  }

  getRunWellPromise(name, well) {
    return this.syncFetch(this.buildUrl(['run', name,'well',well]));
  }

  getClientConfig() {
    return this.syncFetch('/api/config');
  }

  claimWell(name, well) {
    throw Error('Not implemented');
  }
}
