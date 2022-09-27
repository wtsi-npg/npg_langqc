import { describe, expect, test } from 'vitest';
import groupMetrics from "../metrics.js";

describe('Grouping of metrics into useful elements', () => {
    test('Grouping a zero length list', () => {
        expect(groupMetrics([])).toEqual({
            'MetricBlue': {},
            'MetricGreen': {},
            'MetricOrange': {},
            'MetricYellow': {}
        });
    });
});
