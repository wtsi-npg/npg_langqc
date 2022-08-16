import { join, reject } from "lodash";

export default class LangQc {
  constructor(host) {
    if (typeof host == 'undefined') {
      throw Error('LangQc client must know where the web service is');
    }
    this.host = host;

    this.urls = {
      inbox: this.buildUrl('pacbio/inbox', ['weeks=1']),
      run: this.buildUrl('pacbio/run'),
      wells_inbox: this.buildUrl('pacbio/wells', ['qc_status=inbox'])
    };
    this.commonHeaders = {
      'Accept': 'application/json'
    };
  }

  buildUrl(path, args) {
    let data_service = new URL(this.host);
    data_service.pathname = path;
    if (Array.isArray(args)) {
      data_service.search = '?' + join(args, "&");
    }
    return data_service;
  }

  getUrl(alias) {
    return this.urls[alias].href;
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
      this.buildUrl(join(['pacbio','run', name,'well',well], '/')),
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
