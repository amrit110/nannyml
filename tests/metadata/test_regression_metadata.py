#  Author:   Niels Nuyttens  <niels@nannyml.com>
#
#  License: Apache Software License 2.0

"""Tests concerning :class:`nannyml.metadata.regression.RegressionMetadata`."""

from typing import Tuple

import pandas as pd
import pytest

from nannyml.datasets import load_synthetic_binary_classification_dataset
from nannyml.metadata import ModelType, RegressionMetadata, extract_metadata
from nannyml.metadata.base import (
    NML_METADATA_PERIOD_COLUMN_NAME,
    NML_METADATA_TARGET_COLUMN_NAME,
    NML_METADATA_TIMESTAMP_COLUMN_NAME,
)
from nannyml.metadata.regression import NML_METADATA_PREDICTION_COLUMN_NAME, _guess_predictions


@pytest.fixture
def data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:  # noqa: D103
    ref_df, ana_df, tgt_df = load_synthetic_binary_classification_dataset()  # TODO create new regression sample data

    return ref_df, ana_df, tgt_df


@pytest.fixture
def metadata(data) -> RegressionMetadata:  # noqa: D103
    md = extract_metadata(data[0], model_type='regression')
    md.target_column_name = 'work_home_actual'
    return md


def test_model_metadata_creation_with_defaults_has_correct_properties():  # noqa: D103
    sut = RegressionMetadata()

    assert sut.name is None
    assert sut.model_type == ModelType.REGRESSION
    assert sut.features is not None
    assert len(sut.features) == 0
    assert sut.prediction_column_name is None
    assert sut.target_column_name is None
    assert sut.period_column_name is None
    assert sut.timestamp_column_name is None


def test_model_metadata_creation_sets_correct_values_for_special_attributes():  # noqa: D103
    sut = RegressionMetadata(prediction_column_name='pred')
    assert sut.prediction_column_name == 'pred'


def test_to_dict_contains_all_properties(metadata):  # noqa: D103
    sut = metadata.to_dict()
    assert sut['prediction_column_name'] == 'y_pred'


def test_to_pd_contains_all_properties(metadata):  # noqa: D103
    sut = metadata.to_df()
    assert sut.loc[sut['label'] == 'prediction_column_name', 'column_name'].iloc[0] == 'y_pred'


@pytest.mark.parametrize(
    'col,expected',
    [
        ('p', True),
        ('y_pred', True),
        ('pred', True),
        ('prediction', True),
        ('out', True),
        ('output', True),
        ('nope', False),
    ],
)
def test_guess_predictions_yields_correct_results(col, expected):  # noqa: D103
    sut = _guess_predictions(data=pd.DataFrame(columns=[col]))
    assert col == sut[0] if expected else len(sut) == 0


def test_setting_prediction_column_name_after_extracting_metadata_updates_the_features_list(  # noqa: D103
    data: pd.DataFrame,
):
    data[0].rename(columns={'y_pred': 'foo'}, inplace=True)
    md = extract_metadata(data[0], model_type='regression')
    md.prediction_column_name = 'foo'
    assert md.prediction_column_name == 'foo'
    assert md.feature(column='foo') is None


def test_enrich_copies_each_metadata_column_to_new_fixed_column():  # noqa: D103
    data = pd.DataFrame(columns=['identity', 'prediction', 'actual', 'period', 'ts', 'feat1', 'feat2'])
    md = extract_metadata(data, model_name='model', model_type='regression')
    sut = md.enrich(data).columns

    assert NML_METADATA_TIMESTAMP_COLUMN_NAME in sut
    assert NML_METADATA_PREDICTION_COLUMN_NAME in sut
    assert NML_METADATA_TARGET_COLUMN_NAME in sut
    assert NML_METADATA_PERIOD_COLUMN_NAME in sut


def test_enrich_works_on_copy_of_data_by_default():  # noqa: D103
    data = pd.DataFrame(columns=['identity', 'prediction', 'actual', 'period', 'ts', 'feat1', 'feat2'])
    old_column_count = len(data.columns)
    md = extract_metadata(data, model_name='model', model_type='regression')
    sut = md.enrich(data).columns

    assert len(sut) == len(data.columns) + 4
    assert len(data.columns) == old_column_count

    assert NML_METADATA_TIMESTAMP_COLUMN_NAME in sut
    assert NML_METADATA_PREDICTION_COLUMN_NAME in sut
    assert NML_METADATA_TARGET_COLUMN_NAME in sut
    assert NML_METADATA_PERIOD_COLUMN_NAME in sut
    assert 'prediction' in sut
    assert 'actual' in sut
    assert 'period' in sut
    assert 'feat1' in sut
    assert 'feat2' in sut


def test_enrich_adds_nan_prediction_column_if_no_prediction_column_in_original_data(data, metadata):  # noqa: D103
    analysis_data = data[1].drop(columns=[metadata.prediction_column_name])
    sut = metadata.enrich(analysis_data)
    assert NML_METADATA_PREDICTION_COLUMN_NAME in sut.columns
    assert sut[NML_METADATA_PREDICTION_COLUMN_NAME].isna().all()


def test_enrich_adds_nan_ground_truth_column_if_no_ground_truth_in_original_data(data, metadata):  # noqa: D103
    sut = metadata.enrich(data[1])
    assert NML_METADATA_TARGET_COLUMN_NAME in sut.columns
    assert sut[NML_METADATA_TARGET_COLUMN_NAME].isna().all()


def test_extract_metadata_should_set_regression_properties(data):  # noqa: D103
    sut = extract_metadata(data[0], model_type='regression')
    assert sut is not None

    # check regression properties
    assert sut.prediction_column_name == 'y_pred'

    # check base properties
    assert sut.target_column_name is None
    assert sut.period_column_name == 'period'
    assert sut.timestamp_column_name == 'timestamp'
