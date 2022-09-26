import { join } from "lodash";

export default class LangQc {
  constructor() {
    this.urls = {
      inbox: this.buildUrl('/inbox', ['weeks=1']),
      run: this.buildUrl('/run'),
      wells_inbox: this.buildUrl('/wells', ['qc_status=inbox'])
    };
    this.commonHeaders = {
      'Accept': 'application/json'
    };
  }

  buildUrl(path, args) {
    let base = '/pacbio'; // Get app base path from build stage
    let search = '';

    if (Array.isArray(path)) {
      path = path.join('/');
    }
    if (Array.isArray(args)) {
      search = '?' + join(args, "&");
    }
    return base + path + search;
  }

  getUrl(alias) {
    return this.urls[alias];
  }

  getInboxPromise() {
    return fetch(
      this.getUrl('wells_inbox'),
      {
        headers: this.commonHeaders
      }
    ).then(
      response => response.json()
    ).catch(
      (error) => {
        throw error;
      }
    );
  }

  getRunWellPromise(name, well) {
    return fetch(
      this.buildUrl(join(['run', name,'well',well])),
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
    );
  }

  claimWell(name, well) {
    throw Error('Not implemented');
  }
}
