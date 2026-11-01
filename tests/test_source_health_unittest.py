import unittest
from cbv.pipeline_health import available_source_counts

class SourceCountsTest(unittest.TestCase):
    def test_only_available_manifest_entries_are_counted(self):
        manifest = {'sources': {'scoresheet': {'status': 'AVAILABLE'}, 'match_report': {'status': 'BLOCKED'}, 'libero_report': {'status': 'AVAILABLE'}}}
        self.assertEqual(available_source_counts(manifest), {'scoresheets': 1, 'match_reports': 0, 'libero_reports': 1, 'play_by_play': 0})

if __name__ == '__main__':
    unittest.main()
