<script setup>
import { ref } from "vue";
import { ElTooltip, ElCollapse, ElCollapseItem } from "element-plus";

const props = defineProps({
  pool: Object,
})

const active = ref([])
</script>

<template>
  <el-collapse v-model="active" accordion>
    <el-collapse-item name="1">
      <template #title><slot>Pool composition</slot></template>
      <el-tooltip content="Caution, this value is of low signficance when the pool size is small">
        <p>Coefficient of Variance: {{ props.pool.pool_coeff_of_variance }}</p>
      </el-tooltip>
      <table>
        <tr>
          <th>Tag 1</th>
          <th>Tag 2</th>
          <th>Deplexing barcode ID</th>
          <th>HiFi bases (Gb)</th>
          <th>HiFi reads</th>
          <th>HiFi mean read length</th>
          <th>Percentage of HiFi bases</th>
          <th>Percentage of total reads</th>
        </tr>
        <tr :key="library.id_product" v-for="library in props.pool.products">
          <td>{{ library.tag1_name }}</td>
          <td>{{ library.tag2_name }}</td>
          <td>{{ library.deplexing_barcode }}</td>
          <td>{{ library.hifi_read_bases }}</td>
          <td>{{ library.hifi_num_reads }}</td>
          <td>{{ library.hifi_read_length_mean }}</td>
          <td>{{ library.hifi_bases_percent }}</td>
          <td>{{ library.percentage_total_reads }}</td>
        </tr>
      </table>
    </el-collapse-item>
  </el-collapse>
</template>
