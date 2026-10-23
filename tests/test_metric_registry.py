from pathlib import Path
from cbv.metrics.registry import REGISTRY,MetricClass,legacy_bindings
from cbv.metrics.methodology import render


def test_registry_complete_and_notebook_generated():
    assert len(REGISTRY)>=70
    assert len(REGISTRY)==len(set(REGISTRY))
    for metric in REGISTRY.values():
        assert metric.metric_class in {m.value for m in MetricClass}
        assert metric.formula and metric.limitations and metric.validation_method
    assert all(k in REGISTRY for k,*_ in legacy_bindings())
    assert Path('docs/CADERNO_METODOLOGICO.md').read_text()==render()


def test_legacy_so_distinct_from_scoreboard_so():
    assert REGISTRY['so'].formula!=REGISTRY['rally_so'].formula
    assert REGISTRY['prematch'].model_version=='logistic-l2-v1'
    assert REGISTRY['setter_distribution'].metric_class=='EXPERIMENTAL'
