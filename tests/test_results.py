"""Checks on the generated results JSON.

These are consistency and sanity checks on a run's output, not assertions that
the model produces a particular number. Where a bound is asserted it is wide
enough that only a structural break would trip it.
"""

import pytest

YEARS = ["2027", "2028", "2029"]


def test_every_requested_year_is_present(results):
    assert [str(year) for year in results["years"]] == YEARS
    for year in YEARS:
        assert year in results["by_year"]


def test_the_registry_is_emitted(results):
    for key in ["assumptions", "sources", "comparable_costings", "income_cliff_context"]:
        assert results[key], f"{key} missing from the results JSON"


def test_costs_are_positive_and_grow_with_the_forecast(results):
    combined = [results["by_year"][year]["legs"]["combined"]["static_cost_bn"] for year in YEARS]
    assert all(cost > 0 for cost in combined)
    assert combined == sorted(combined), "cost should rise as the population and rates uprate"


def test_the_legs_do_not_sum_to_the_combined_cost(results):
    # Free hours displace paid care, shrinking the base the subsidy applies to,
    # so the combined cost is below the sum of the legs run separately.
    for year in YEARS:
        legs = results["by_year"][year]["legs"]
        leg_sum = legs["free_hours"]["static_cost_bn"] + legs["subsidy"]["static_cost_bn"]
        assert legs["combined"]["static_cost_bn"] < leg_sum


def test_free_hours_leg_is_near_the_published_analogue(results):
    # NEF costed 15 hours free for all children 9 months to 4 at £3.0-3.4bn net
    # for England. This is UK-wide and static, so it should be the same order.
    cost = results["by_year"]["2027"]["legs"]["free_hours"]["static_cost_bn"]
    assert 1.0 < cost < 5.0


def test_the_labour_supply_response_is_small_relative_to_the_cost(results):
    for year in YEARS:
        dynamic = results["by_year"][year]["dynamic_cost"]["central"]
        assert abs(dynamic["offset_share_of_static_cost"]) < 0.25


def test_elasticity_bounds_order_the_response(results):
    # A larger elasticity must move employment further from zero in whichever
    # direction the central case points.
    for year in YEARS:
        responses = results["by_year"][year]["labour_supply"]
        low = abs(responses["low"]["net_entrants"])
        central = abs(responses["central"]["net_entrants"])
        high = abs(responses["high"]["net_entrants"])
        assert low <= central <= high


def test_the_price_elasticity_cross_check_can_only_be_positive(results):
    # It sees the price fall and nothing else, so it brackets the gain-to-work
    # model from above rather than confirming it.
    for year in YEARS:
        for bound in ["low", "central", "high"]:
            check = results["by_year"][year]["price_elasticity_cross_check"][bound]
            assert check["entrants"] >= 0
            assert check["effective_price_change"] < 0


def test_quintiles_are_complete_and_gains_are_non_negative(results):
    for year in YEARS:
        effects = results["by_year"][year]["legs"]["combined"]["household_effects"]
        for key in ["by_income_quintile", "by_income_quintile_families_with_under_5s"]:
            rows = effects[key]
            assert [row["group"] for row in rows] == ["Q1", "Q2", "Q3", "Q4", "Q5"]
            # Nobody loses: the reform only adds support.
            assert all(row["average_gain_gbp"] >= 0 for row in rows)


def test_household_gains_are_consistent_with_the_cost(results):
    # Total household gain should track the static cost. It is not identical:
    # gov_spending includes support the household measure nets differently, and
    # the free-hours value reaches households as an in-kind benefit.
    for year in YEARS:
        result = results["by_year"][year]
        total_gain = result["legs"]["combined"]["household_effects"]["all_households"][
            "total_gain_bn"
        ]
        cost = result["legs"]["combined"]["static_cost_bn"]
        assert 0.5 * cost < total_gain < 1.5 * cost


def test_uc_childcare_element_is_never_counted_as_spending(results):
    # It is the childcare element of the UC maximum amount, before the taper,
    # so it is an entitlement component and not government spending.
    for year in YEARS:
        spending = results["by_year"][year]["baseline_spending"]
        assert "uc_childcare_element" not in spending
        assert spending["total_childcare_support_bn"] == pytest.approx(
            spending["universal_childcare_entitlement"]
            + spending["extended_childcare_entitlement"]
            + spending["targeted_childcare_entitlement"]
            + spending["tax_free_childcare"],
            abs=1e-3,
        )


def test_benchmarks_carry_a_source_and_a_verdict(results):
    benchmarks = results["by_year"]["2027"]["benchmarks"]
    assert len(benchmarks) >= 5
    for benchmark in benchmarks:
        assert benchmark["url"].startswith("https://")
        assert benchmark["kind"]
        assert benchmark["model_bn"] >= 0


def test_the_known_gaps_are_flagged_rather_than_hidden(results):
    kinds = {
        benchmark["measure"]: benchmark["kind"]
        for benchmark in results["by_year"]["2027"]["benchmarks"]
    }
    assert kinds["Tax-Free Childcare"] == "Award gap"
    # It became comparable once measured as a counterfactual rather than by
    # summing a maximum-amount component; what remains is a caseload gap.
    assert kinds["Universal Credit childcare element"] == "Caseload gap"
    assert kinds["Parent-paid childcare fees, England, under-5s"] == "Fee base check"
    assert kinds["Childcare spending, all children, UK"] == "Unbenchmarked"


def test_the_fee_base_is_compared_like_for_like(results):
    # The CMA benchmark covers England and the under-5s, so it must be compared
    # against that slice of the model, not the UK all-ages aggregate. Comparing
    # the two would roughly double the apparent gap.
    rows = {row["measure"]: row for row in results["by_year"]["2027"]["benchmarks"]}
    comparable = rows["Parent-paid childcare fees, England, under-5s"]
    full_base = rows["Childcare spending, all children, UK"]
    assert comparable["model_bn"] < full_base["model_bn"]
    assert comparable["ratio_model_to_official"] < 2.5
    # The unbenchmarked row must not claim a ratio it cannot have.
    assert full_base["ratio_model_to_official"] is None


def test_the_fee_base_benchmark_is_gross_of_the_support_derived_from_it(results):
    """The benchmark must not net off TFC or the UC childcare element.

    `childcare_expenses` is the total fee, and `tax_free_childcare` and
    `uc_childcare_element` are both computed from it. Subtracting them from the
    CMA residual and then comparing against the variable they derive from
    double-counts the support: it is what produced an apparent 1.70x gap where
    the like-for-like figure is 1.25x. The comparator is the CMA residual
    itself — England early years sector income less funded entitlements,
    about £14bn - £8.9bn.
    """
    rows = {row["measure"]: row for row in results["by_year"]["2027"]["benchmarks"]}
    benchmark = rows["Parent-paid childcare fees, England, under-5s"]["official_bn"]
    assert benchmark == pytest.approx(5.10), (
        "the fee-base benchmark must be the gross CMA residual, not a figure "
        "net of the support computed from childcare_expenses"
    )
    for year in YEARS:
        sensitivity = results["by_year"][year]["fee_base_sensitivity"]
        assert sensitivity["benchmark_england_under_5_bn"] == pytest.approx(5.10)


def test_the_fee_base_sensitivity_lowers_the_subsidy_leg(results):
    for year in YEARS:
        result = results["by_year"][year]
        sensitivity = result["fee_base_sensitivity"]
        assert sensitivity["ratio"] < 1
        assert sensitivity["combined_cost_bn"] < result["legs"]["combined"]["static_cost_bn"]
        # The free-hours leg is untouched by the fee base, so it is a floor.
        assert sensitivity["combined_cost_bn"] > result["legs"]["free_hours"]["static_cost_bn"]


def test_entering_work_pays_a_realistic_amount(results):
    """The extensive margin must not be suppressed by an imputation bug.

    With the upstream wage imputation a non-worker was credited with about £194
    a year for entering part-time work, so entrants rounded to nothing and the
    exchequer recovered nothing from them. Average earnings per entrant should
    look like a real part-time job.
    """
    for year in YEARS:
        response = results["by_year"][year]["labour_supply"]["central"]
        assert response["entrants"] > 100, "entrants collapsed — check the wage imputation"
        per_entrant = response["earnings_gained_gbp"] / response["entrants"]
        assert 8_000 < per_entrant < 40_000, f"{per_entrant:,.0f} is not a part-time wage"


def test_the_exchequer_recovers_something_from_entrants(results):
    for year in YEARS:
        response = results["by_year"][year]["labour_supply"]["central"]
        assert response["revenue_from_entrants_gbp"] > 0
        # Tax plus benefit withdrawal on a part-time wage: a positive share, well under all of it.
        share = response["revenue_from_entrants_gbp"] / response["earnings_gained_gbp"]
        assert 0.02 < share < 0.9


def test_the_baseline_is_compared_at_the_published_figures_own_year(results):
    """Each programme's ratio must be taken at the year its source covers.

    Dividing a 2027 model figure by a January 2025 census measures the gap
    between the two dates as much as the model: on the working-parent
    entitlement that reads 1.61x, almost all of it the September 2025
    expansion to 30 hours for under-threes, which the census predates.
    """
    rows = {row["programme"]: row for row in results["by_year"]["2027"]["baseline_programmes"]}
    assert set(rows) == {"universal", "extended", "targeted", "tfc"}
    # Every programme now carries an official spending figure. The two
    # entitlements come from DfE's early years national funding formula
    # technical note, which does publish the universal/additional split — an
    # earlier version of this analysis wrongly concluded it did not.
    for programme in rows:
        assert rows[programme]["official_spending_bn"] > 0, programme
    # The working-parent figure is a lower bound: DfE's two-year-old line mixes
    # the working-parent and disadvantaged offers and is not split.
    assert rows["extended"]["official_spending_bn"] == pytest.approx(3.4)
    assert "lower bound" in rows["extended"]["official_spending_label"]
    for programme, row in rows.items():
        assert row["comparison_year"] < row["costed_year"], programme
        # The costed-year figures are reported for context and must never be
        # the numerator of a ratio against an older published figure.
        assert row["costed_year_spending_bn"] >= row["model_spending_bn"], programme
        if row["official_caseload"]:
            expected = round(row["model_caseload"] / row["official_caseload"], 3)
            assert row["caseload_ratio"] == pytest.approx(expected), programme
        if row["official_spending_bn"]:
            expected = round(row["model_spending_bn"] / row["official_spending_bn"], 3)
            assert row["spending_ratio"] == pytest.approx(expected), programme


def test_the_baseline_agrees_with_the_data_builds_own_release_check(results):
    """The four ratios must match what policyengine-uk-data checks its release on.

    Same published figures, same model years. If these drift apart, one of the
    two is comparing against something the other is not, which is the failure
    this whole analysis has hit twice.
    """
    rows = {row["programme"]: row for row in results["by_year"]["2027"]["baseline_programmes"]}
    # Release 1.57.2, from the push.yaml calibration log. The entitlements
    # total row has no caseload: a child can hold more than one entitlement.
    expected_caseload = {"universal": 0.93, "extended": 1.16, "targeted": 0.78, "tfc": 1.01}
    for programme, ratio in expected_caseload.items():
        assert rows[programme]["caseload_ratio"] == pytest.approx(ratio, abs=0.02), programme
    assert rows["tfc"]["spending_ratio"] == pytest.approx(0.99, abs=0.02)


def test_the_uc_childcare_element_is_measured_by_abolishing_it(results):
    """Summing the variable gives an entitlement component, not spending.

    `uc_childcare_element` is part of the UC maximum amount, before the
    earnings taper. Its sum is £8.69bn against DWP's £611m outturn — a 14x
    gap that is an artefact of the comparison. The comparable figure is what
    abolishing it costs.
    """
    for year in YEARS:
        measured = results["by_year"][year]["uc_childcare_fiscal_cost"]
        assert measured["fiscal_cost_bn"] < measured["maximum_amount_component_bn"] / 3, (
            "most of the maximum-amount component is withdrawn by the taper and "
            "never reaches a household"
        )
        assert measured["benefit_units_receiving"] > 0

    row = next(
        row
        for row in results["by_year"]["2027"]["benchmarks"]
        if row["measure"] == "Universal Credit childcare element"
    )
    fiscal = results["by_year"]["2027"]["uc_childcare_fiscal_cost"]["fiscal_cost_bn"]
    assert row["model_bn"] == pytest.approx(fiscal, abs=0.01), (
        "the benchmark row must show the counterfactual, not the variable's sum"
    )


def test_household_effects_respond_to_the_labour_supply_assumption(results):
    """The distribution must move with the assumption, not just the cost.

    The participation response is an expected value per person — a probability
    of entering or leaving work times the gain to work — so it allocates to
    households and can be read by quintile. An earlier version of this
    dashboard claimed it could not, and showed static figures under every
    assumption.
    """
    for leg in ("free_hours", "subsidy"):
        by_bound = results["by_year"]["2027"]["legs"][leg]["household_effects_by_bound"]
        assert set(by_bound) == {"low", "central", "high"}
        gains = {
            bound: [
                row["average_gain_gbp"]
                for row in effects["by_income_quintile_families_with_under_5s"]
            ]
            for bound, effects in by_bound.items()
        }
        assert gains["low"] != gains["central"] != gains["high"], leg
        static = [
            row["average_gain_gbp"]
            for row in results["by_year"]["2027"]["legs"][leg]["household_effects"][
                "by_income_quintile_families_with_under_5s"
            ]
        ]
        assert gains["central"] != static, leg
