<script setup>
defineProps({
  wellCollection: Object
})

defineEmits(['wellSelected'])
</script>

<template>
  <table id="run_wells">
    <tr>
      <th>Run name</th>
      <th>Well label</th>
      <th>QC state</th>
      <th>QC date</th>
      <th>Assessor</th>
      <th>Well status</th>
      <th>Run status</th>
      <th>Well time start</th>
      <th>Well time complete</th>
    </tr>
    <tr :key="wellObj.run_name + ':' + wellObj.label" v-for="wellObj in wellCollection">
      <td>{{ wellObj.run_name }}</td>
      <td class="well_selector">
        <button v-on:click="$emit('wellSelected', { qcRun: wellObj.run_name, qcLabel: wellObj.label })">{{ wellObj.label
        }}</button>
      </td>
      <td>{{ wellObj.qc_state ? wellObj.qc_state.qc_state : '&nbsp;' }}</td>
      <td>{{ wellObj.qc_state ? wellObj.qc_state.date_updated : '&nbsp;' }}</td>
      <td>{{ wellObj.qc_state ? wellObj.qc_state.user : '&nbsp;' }}</td>
      <td>{{ wellObj.well_status ? wellObj.well_status : '&nbsp;' }}</td>
      <td>{{ wellObj.run_status ? wellObj.run_status : '&nbsp;' }}</td>
      <td>{{ wellObj.well_start_time ? wellObj.well_start_time : '&nbsp;' }}</td>
      <td>{{ wellObj.well_complete_time ? wellObj.well_complete_time : '&nbsp;' }}</td>
    </tr>
  </table>
</template>

<style>
#run_wells {
  width: 100%;
}
</style>