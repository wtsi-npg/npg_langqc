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

  syncFetch(route, method='GET', body) {
    // Don't use this if you want async efficiency.
    // Returns a promise that ought to contain backend data

    let requestMeta = {
      headers: this.commonHeaders,
    }

    if (method == 'POST') {
      requestMeta.method = method;
      requestMeta.headers = {
        'Content-type': 'application/json',
        'Accept': 'application/json'
      };
      requestMeta.body = JSON.stringify(body);
    }

    return fetch(
      route,
      requestMeta
    ).then(
      response => {
        if (response.ok) {
          return response.json()
        } else {
          throw new Error(`API ${requestMeta.method} error "` + response.statusText);
        }
      }
    )
  }

  getInboxPromise(qc_status='inbox', page_number=1, page_size=10) {
    return this.syncFetch(
      this.buildUrl(
        '/wells',
        [`qc_status=${qc_status}`, `page_size=${page_size}`, `page_number=${page_number}`]
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
    return this.syncFetch(
      this.buildUrl(['run', name, 'well', well, 'qc_claim']),
      'POST',
      {
        "qc_type": "sequencing"
      }
    )
  }
}
