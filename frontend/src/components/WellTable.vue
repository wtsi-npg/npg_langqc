<script setup>
/*
* Renders a table for a list of wells and generates buttons for selecting wells
*/
import { combineLabelWithPlate, listStudiesForTooltip } from "../utils/text.js"
import { ElTooltip, ElButton } from "element-plus"
import { Top } from "@element-plus/icons-vue"

const tooltipDelay = 500
const studyNameHighlight = 'BIOSCAN UK for flying insects'

defineProps({
  wellCollection: Object,
  allowNav: Boolean,
})

defineEmits(['wellSelected', 'runSelected'])
</script>

<template>
  <table id="run_wells">
    <tr>
      <th>Run name</th>
      <th>Well label</th>
      <th>Instrument</th>
      <th>QC state</th>
      <th>QC date</th>
      <th>Assessor</th>
      <th>Well status</th>
      <th>Run status</th>
      <th>Well time start</th>
      <th>Well time complete</th>
    </tr>
    <tr :key="wellObj.id_product" v-for="wellObj in wellCollection">
      <td :id="wellObj.run_name">{{ wellObj.run_name }}<el-icon v-if="allowNav" :size="10" v-on:click="$emit('runSelected', wellObj.run_name)"><Top /></el-icon></td>
      <td class="well_selector">
        <el-tooltip placement="top" effect="light" :show-after="tooltipDelay"
          :content="'<span>'.concat(listStudiesForTooltip(wellObj.study_names)).concat('</span>')"
          raw-content
        >
          <el-button plain
            :type="wellObj.study_names.includes(studyNameHighlight) ? 'warning' : 'info'"
            v-on:click="$emit('wellSelected', { idProduct: wellObj.id_product })"
          >
            {{ combineLabelWithPlate(wellObj.label, wellObj.plate_number) }}
          </el-button>
        </el-tooltip>
      </td>
      <td>{{ wellObj.instrument_type }} {{ wellObj.instrument_name }}</td>
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
