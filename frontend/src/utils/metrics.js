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
    PolymeraseStats: (['polymerase_read_bases', 'polymerase_read_length_mean', 'p0_num', 'p1_num', 'p2_num'])
});

// Collection of functions to convert metrics to prettier label and value, keyed off LangQC metric key
const Reformatting = {
    binding_kit: (v) => {return ['Binding Kit', v]},
    control_num_reads: (v) => {return ['Number of Control Reads', v.toLocaleString()]},
    control_read_length_mean: (v) => {return ['Control Read Length (bp)', v.toLocaleString()]},
    hifi_read_bases: (v) => {return ['CCS Yield (Gb)', (v / 1000000000).toPrecision(4)]},
    hifi_read_length_mean: (v) => {return ['CCS Mean Length (bp)', v.toLocaleString()]},
    local_base_rate: (v) => {return ['Local Base Rate', v]},
    p0_num: (n, d) => {return ['P0 %', (n / d).toPrecision(3)]},
    p1_num: (n, d) => {return ['P1 %', (n / d).toPrecision(3)]},
    p2_num: (n, d) => {return ['P2 %', (n / d).toPrecision(3)]},
    polymerase_read_bases: (v) => {return ['Total Cell Yield (Gb)', (v / 1000000000).toPrecision(4)]},
    polymerase_read_length_mean: (v) => {return ['Mean Polymerase Read Length (bp)', v.toLocaleString()]},
    movie_minutes: (v) => {return ['Run Time (hr)', (v / 60).toPrecision(2)]}
};

export default function groupMetrics(metrics) {
    /*
    Cluster metrics together into approved groupings
    Accepts a LangQC metric object
    Returns an object -> category -> list of [label, value]
    */
    let groupedMetrics = {};
    for (const [cat, members] of Object.entries(StatCategories)) {
        let cssClass = CssMapping[cat];
        for (const label of members) {
            if (! (cssClass in groupedMetrics)) { groupedMetrics[cssClass] = {} };
            if (['p0_num', 'p1_num', 'p2_num'].includes(label)) {
                groupedMetrics[cssClass][label] = Reformatting[label](metrics[label], metrics['productive_zmws_num']);
            } else {
                groupedMetrics[cssClass][label] = Reformatting[label](metrics[label]);
            }
        }
    }
    console.log(groupedMetrics);
    return groupedMetrics;
}
