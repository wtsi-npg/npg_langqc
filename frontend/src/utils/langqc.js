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

  fetchWrapper(route, method='GET', body) {
    // Don't use this if you want async efficiency.
    // Returns a promise that ought to contain backend data

    console.log(`Fetching from ${route}`);
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
        // console.log(response);
        if (response.ok) {
          // console.log(response.json());
          return response.json();
        } else {
          throw new Error(`API ${requestMeta.method} error "` + response.statusText);
        }
      }
    ).catch(
      (e) => {console.log(e); throw new Error("It's all gone wrong in the fetch: "+e)}
    );
  }

  getInboxPromise(qc_status='inbox', page_number=1, page_size=10) {
    return this.fetchWrapper(
      this.buildUrl(
        '/wells',
        [`qc_status=${qc_status}`, `page_size=${page_size}`, `page_number=${page_number}`]
      )
    );
  }

  getRunWellPromise(name, well) {
    return this.fetchWrapper(this.buildUrl(['run', name,'well',well]));
  }

  getClientConfig() {
    return this.fetchWrapper('/api/config');
  }

  claimWell(name, well) {
    return this.fetchWrapper(
      this.buildUrl(['run', name, 'well', well, 'qc_claim']),
      'POST',
      {
        "qc_type": "sequencing"
      }
    )
  }
}
