// Reusable text-mangling for the interface

export { combineLabelWithPlate, listStudiesForTooltip }

function combineLabelWithPlate(well, plate) {
  if (!plate) {
    return well
  } else {
    return `${plate}-${well}`
  }
}

function listStudiesForTooltip(study_names) {
  let names = study_names.length == 0 ? ['No study info'] : study_names
  return names.join('<br />')
}
