import unittest
from cbv.pipeline_health import SyncHealthTracker, available_source_counts

class SourceCountsTest(unittest.TestCase):
    def test_only_available_manifest_entries_are_counted(self):
        manifest = {'sources': {'scoresheet': {'status': 'AVAILABLE'}, 'match_report': {'status': 'BLOCKED'}, 'libero_report': {'status': 'AVAILABLE'}}}
        self.assertEqual(available_source_counts(manifest), {'scoresheets': 1, 'match_reports': 0, 'libero_reports': 1, 'play_by_play': 0})

    def test_optional_source_with_zero_coverage_is_unavailable(self):
        tracker = SyncHealthTracker()
        tracker.record_source('play_by_play', attempted=613, successful=0)
        report = tracker.finalize(None, initial_match_count=613)
        self.assertEqual(report['sources']['play_by_play']['status'], 'UNAVAILABLE')
        self.assertEqual(report['status'], 'HEALTHY')

    def test_critical_source_with_zero_coverage_fails_the_sync(self):
        tracker = SyncHealthTracker()
        tracker.record_source('match_reports', attempted=613, successful=0)
        report = tracker.finalize(None, initial_match_count=613)
        self.assertEqual(report['status'], 'FAILED')

if __name__ == '__main__':
    unittest.main()
