"""Disclosure control on synthetic data: noise, the floor and the partner rows."""

import numpy as np
import pytest

from free_childcare_reform import disclosure


def test_one_or_two_survey_households_are_too_few_and_copies_count_once():
    assert not disclosure.too_few([])
    assert disclosure.too_few(["a"])
    assert disclosure.too_few(["a", "a", "a", "b"])
    assert not disclosure.too_few(["a", "b", "c"])


def test_a_lone_small_row_takes_the_smallest_other_row_with_it():
    rows = {name: {"value": 1.0} for name in ("big", "small", "medium", "empty")}
    sources = {
        "big": list("abcdefghij"),
        "small": ["k", "k"],
        "medium": ["l", "m", "n"],
        "empty": [],
    }
    disclosure.withhold_rows(rows, sources, ("value",))
    # Alone, the small row would come back as the total less the others.
    assert rows["small"]["value"] is None
    assert rows["medium"]["value"] is None
    assert rows["big"]["value"] == 1.0
    # A row resting on no household gives nothing away and protects nothing.
    assert rows["empty"]["value"] == 1.0


def test_partners_are_added_until_the_withheld_rows_rest_on_three_households():
    rows = {name: {"value": 1.0} for name in ("one", "two", "many", "more")}
    sources = {
        "one": ["a"],
        "two": ["a", "b"],
        "many": list("cdefghij"),
        "more": list("klmnopqrstuv"),
    }
    disclosure.withhold_rows(rows, sources, ("value",))
    assert [name for name, row in rows.items() if row["value"] is None] == ["one", "two", "many"]


def test_rows_on_three_or_more_households_are_left_alone():
    rows = {"x": {"value": 1.0}, "y": {"value": 2.0}}
    disclosure.withhold_rows(rows, {"x": ["a", "b", "c"], "y": ["d", "e", "f"]}, ("value",))
    assert rows == {"x": {"value": 1.0}, "y": {"value": 2.0}}


def test_a_quintile_with_a_withheld_decile_is_withheld_in_that_field():
    from free_childcare_reform.pipeline import fold_deciles_to_quintiles

    published = {
        "households_m": 1.0,
        "total_gain_bn": 0.1,
        "average_gain_gbp": 100.0,
        "average_gain_gbp_among_gainers": 200.0,
        "share_gaining": 0.5,
        "average_gain_pct_of_income": 0.5,
        "households": 1e6,
        "total_gain_gbp": 1e8,
        "gainers_households": 5e5,
        "gainers_total_gain_gbp": 1e8,
        "baseline_income_gbp": 2e10,
    }
    withheld = dict(published, gainers_households=None, gainers_total_gain_gbp=None)
    withheld.update(average_gain_gbp_among_gainers=None, share_gaining=None)
    (q1,) = fold_deciles_to_quintiles([{"group": "D1", **published}, {"group": "D2", **withheld}])
    # Otherwise the published D1 beside it would give D2 back.
    assert q1["share_gaining"] is None
    assert q1["average_gain_gbp_among_gainers"] is None
    assert q1["average_gain_gbp"] == 100.0
    assert q1["households"] == 2e6


def _prepared(country, source, factor, *, working, change):
    from free_childcare_reform.disclosure import Noise

    n = len(country)
    return {
        "gtw_pct_change": np.asarray(change, float),
        "elasticity_wrt_gain_to_work": np.full(n, 0.5),
        "eligible": np.ones(n, bool),
        "currently_working": np.asarray(working, bool),
        "currently_not_working": ~np.asarray(working, bool),
        "employment_income": np.where(working, 20_000.0, 0.0),
        "imputed_wages": np.full(n, 15_000.0),
        "reform_gain": np.full(n, 1_000.0),
        "weekly_hours_worked": np.where(working, 30.0, 0.0),
        "country": np.asarray(country),
        "weights": np.full(n, 100.0),
        "noise": Noise(
            household_source=np.asarray(source, object),
            household_factor=np.asarray(factor, float),
            person_source=np.asarray(source, object),
            person_factor=np.asarray(factor, float),
        ),
    }


def test_the_country_split_is_noised_and_small_cells_are_withheld():
    from free_childcare_reform.labour_supply import participation_response

    # Every country has ten entrants from ten households. Wales's only leaver
    # comes from one survey household; Scotland's leavers from five.
    country, source, working, change = [], [], [], []
    for name, leavers in (("ENGLAND", 20), ("SCOTLAND", 5), ("WALES", 1), ("NI", 0)):
        for i in range(10):
            country.append(name)
            source.append(f"{name}-entrant-{i}")
            working.append(False)
            change.append(0.2)
        for i in range(leavers):
            country.append(name)
            source.append(f"{name}-leaver-{i}")
            working.append(True)
            change.append(-0.2)
    factor = np.where(np.arange(len(country)) % 2, 1.1, 0.9)
    prepared = _prepared(country, source, factor, working=working, change=change)
    result = participation_response(prepared)
    by_country = result["by_country"]

    # Noise is on the country split only: the totals stay exact.
    assert result["entrants"] == pytest.approx(40 * 100 * 0.1)
    entering = (np.asarray(country) == "ENGLAND") & ~np.asarray(working)
    assert by_country["england"]["entrants"] == pytest.approx(
        float((100 * 0.1 * factor[entering]).sum()), abs=1e-3
    )
    # Wales's leaver is withheld, with net entrants, which would give it back;
    # Scotland, the next smallest, is withheld beside it so the UK total
    # cannot. Entrants rest on ten households everywhere and stay.
    for name in ("wales", "scotland"):
        assert by_country[name]["leavers"] is None
        assert by_country[name]["net_entrants"] is None
        assert by_country[name]["entrants"] is not None
    assert by_country["england"]["leavers"] is not None
    assert by_country["ni"]["leavers"] == 0.0
