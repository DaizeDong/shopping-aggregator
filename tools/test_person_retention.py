"""Per-person roots retain the lifecycle of each artifact kind."""
import importlib.util
from pathlib import Path
import sys

import pytest

from make_fixtures import person_retention_cases

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('shopping_storage_contract', ROOT / 'guards/tools/storage_contract.py')
storage = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = storage
spec.loader.exec_module(storage)


@pytest.mark.parametrize('relative,identifier,retention', person_retention_cases())
def test_person_artifact_retains_its_kind(relative, identifier, retention):
    contract = storage.validate_contract(ROOT)
    root_owner = storage.owners(contract, relative)
    person_owner = storage.owners(contract, 'people/synthetic-buyer/' + relative)
    assert len(root_owner) == len(person_owner) == 1
    assert person_owner[0]['artifact_id'] == 'person-' + identifier
    assert person_owner[0]['retention_rule']['class'] == retention
    assert person_owner[0]['retention_rule'] == root_owner[0]['retention_rule']


def test_unrecognized_person_outputs_have_no_owner():
    contract = storage.validate_contract(ROOT)
    assert storage.owners(contract, 'people/synthetic-buyer/unknown/output.bin') == []
