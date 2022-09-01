// Define constants mapping logical groups to CSS classes
const CssMapping = {
    MachineInfo: 'MetricBlue',
    CCS: 'MetricYellow',
    ControlRead: 'MetricGreen',
    PolymeraseStats: 'MetricOrange'
}

// Logical grouping of metrics to display next to each other
const StatCategories = ({
    MachineInfo: (['binding_kit', 'movie_minutes']),
    CCS: (['hifi_read_bases', 'hifi_read_length_mean']),
    ControlRead: (['control_num_reads', 'control_read_length_mean']),
    PolymeraseStats: (['polymerase_read_bases', 'polymerase_read_length_mean', 'p0_num', 'p1_num', 'p2_num', 'local_base_rate'])
});

export default function groupMetrics(metrics) {
    /*
    Cluster metrics together into approved groupings
    Accepts a LangQC metric object
    Returns an object -> category -> metric_name -> list of [label, value]
    */
    let groupedMetrics = {};
    for (const [cat, members] of Object.entries(StatCategories)) {
        let cssClass = CssMapping[cat];
        for (const label of members) {
            if (! (cssClass in groupedMetrics)) { groupedMetrics[cssClass] = {} };

            if (Number.isInteger(metrics[label].value)) {
                // Format integers into 1,000 where appropriate
                groupedMetrics[cssClass][label] = [metrics[label].label, metrics[label].value.toLocaleString()];
            } else {
                groupedMetrics[cssClass][label] = [metrics[label].label, metrics[label].value];
            }
        }
    }
    console.log(groupedMetrics);
    return groupedMetrics;
}
