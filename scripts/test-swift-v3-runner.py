#!/usr/bin/env python3
import unittest
from collections import Counter
from swift_v3_runner import configuration,lane,observe
from swift_v3_reports import ROOT

class Runner(unittest.TestCase):
    def test_complete_lane_partition(self):
        _,_,cases,_=configuration(ROOT)
        self.assertEqual(Counter(lane(c) for c in cases.values()),{'kernel':68,'calibration':4,'modeling':20,'opaque':4,'native':12})
    def test_unexpected_negative_flow_preserved(self):
        case={'polarity':'negative','source_anchors':[{'file':'main.swift','line_hint':2}],'sink_anchors':[{'file':'main.swift','line_hint':5}]}
        outcome,reasons=observe(case,[['main.swift',2,1,'source'],['main.swift',5,1,'sink']],[['main.swift',2,'main.swift',5,1]],'kernel')
        self.assertEqual(outcome,'reached');self.assertEqual(reasons,[])
    def test_same_line_wrong_file_not_endpoint(self):
        case={'source_anchors':[{'file':'Source.swift','line_hint':2}],'sink_anchors':[{'file':'Sink.swift','line_hint':5}]}
        self.assertEqual(observe(case,[['Other.swift',2,1,'source'],['Sink.swift',5,1,'sink']],[],'modeling')[0],'runner-error')
    def test_native_and_opaque_lane_identity(self):
        case={'source_anchors':[{'file':'main.swift','line_hint':2}],'sink_anchors':[{'file':'main.swift','line_hint':5}]}
        for selected,profile in [('native','adapter-composed-v1'),('opaque','adapter-controlled-model-on')]:
            role='environment' if selected=='native' else 'source'
            self.assertEqual(observe(case,[[2,1,profile,role],[5,1,profile,'sink']],[[2,5,1,profile]],selected)[0],'reached')
            with self.assertRaisesRegex(ValueError,'lane endpoint'):observe(case,[[2,1,'foreign',role],[5,1,'foreign','sink']],[],selected)
    def test_malformed_alternate_lane_rejected_before_filtering(self):
        case={'source_anchors':[],'sink_anchors':[]}
        for rows in [[[1,2]],[[1,2,'adapter-controlled-model-off','invalid']]]:
            with self.assertRaisesRegex(ValueError,'lane endpoint'):observe(case,rows,[],'opaque')

    def test_malformed_generic_rows_rejected(self):
        with self.assertRaisesRegex(ValueError,'endpoint'):observe({'source_anchors':[],'sink_anchors':[]},[[1,2]],[],'kernel')

if __name__=='__main__':unittest.main(verbosity=2)
