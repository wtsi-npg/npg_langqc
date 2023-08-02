// Reusable text-mangling for the interface

export default function combineLabelWithPlate(well, plate) {
  if (!plate) {
    return well
  } else {
    return `${plate}-${well}`
  }
}
