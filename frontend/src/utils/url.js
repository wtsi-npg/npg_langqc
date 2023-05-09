export function generateUrl(existingSettings, newSettings, path) {
  /* To be used in conjunction with Vue Router
    It overwrites existing query parts but keeps any previous settings not
    touched by the newSettings
    To remove an option from the query segment, set it as null

    existingSettings - an object clone of Router.query()
    newSettings - an object containing kv pairs intended to appear in the
      the URL as /url?k=v
    path - the /path we intend to stay on or navigate to

    Returns an object suitable for router.push(), i.e. {
      path: '/path',
      query: {
        k: v,
      }
    }

    This function exists in this way to be testable without invoking the
    Vue Router directly. It does not take kindly to out-of-component tests
  */
  let changed = false
  for (let k in newSettings) {
    if (!existingSettings[k] || existingSettings[k] != newSettings[k]) {
      if (newSettings[k] === null) {
        delete existingSettings[k]
      } else {
        existingSettings[k] = newSettings[k]
      }
      changed = true
    }
  }
  if (changed) {
    return { path: path, query: { ...existingSettings } }
  }
  return
}
