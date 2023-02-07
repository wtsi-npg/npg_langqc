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

    let requestMeta = {
      headers: this.commonHeaders,
    }

    if (method == 'POST') {
      requestMeta.method = method;
      requestMeta.headers = {
        'Content-type': 'application/json',
        'Accept': 'application/json'
      };
      if (body != null) {
        requestMeta.body = JSON.stringify(body);
      }
    }

    return fetch(
      route,
      requestMeta
    ).then(
      async (response) => {
        if (response.ok) {
          return response.json();
        } else {
          let error = "";
          if (response.status == 401) {
            // May or may not be the only way to get a 401 from the API...
            error = "Please log in to modify data";
          } else {
            let errorMethod = requestMeta.method ? requestMeta.method : "GET";
            error = `API ${errorMethod} error "${response.statusText}"`;
          }
          if (response.headers.get("content-type") == "application/json") {
            let body = await response.json();
            error += `, "${body.detail}"`;
          }
          throw new Error(error);
        }
      }
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
      'POST'
    )
  }

  setWellQcState(name, well, state, final=false) {
    return this.fetchWrapper(
      this.buildUrl(['run', name, 'well', well, 'qc_assign']),
      'POST',
      {
        qc_state: state,
        is_preliminary: !final,
        qc_type: 'sequencing'
      }
    )
  }
}
