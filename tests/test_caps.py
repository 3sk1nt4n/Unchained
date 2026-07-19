"""Hard-cap tests; no test waits on real time or performs network I/O."""

from __future__ import annotations

import pytest

from conftest import ManualClock
from unchained.caps import CapConfig, CapExceeded, CapKind, RunBudget, estimate_usage_cost
from unchained.models import ModelUsage


def config(**overrides: int | float) -> CapConfig:
    """Return a permissive baseline with just the named test value changed."""

    values: dict[str, int | float] = {
        "max_tool_calls": 100,
        "max_total_tokens": 1_000_000,
        "max_wall_seconds": 3_600.0,
        "max_cost_usd": 1_000.0,
        "input_usd_per_million": 1.0,
        "cached_input_usd_per_million": 0.1,
        "output_usd_per_million": 1.0,
    }
    values.update(overrides)
    return CapConfig(**values)


def assert_sticky_cap(budget: RunBudget, expected: CapKind) -> None:
    """A fired cap must terminate all later work, not merely one operation."""

    assert budget.fired is expected
    with pytest.raises(CapExceeded) as repeated:
        budget.check()
    assert repeated.value.kind is expected
    assert repeated.value.snapshot.fired == expected.value


def test_tool_call_cap_terminates_before_extra_tool_starts() -> None:
    budget = RunBudget(config(max_tool_calls=1))
    budget.reserve_tool_calls()

    with pytest.raises(CapExceeded) as raised:
        budget.reserve_tool_calls()

    assert raised.value.kind is CapKind.TOOL_CALLS
    assert raised.value.snapshot.tool_calls == 1
    assert_sticky_cap(budget, CapKind.TOOL_CALLS)


def test_total_token_cap_terminates_after_observed_response() -> None:
    budget = RunBudget(config(max_total_tokens=10))

    with pytest.raises(CapExceeded) as raised:
        budget.record_model_usage(ModelUsage(input_tokens=6, output_tokens=5))

    assert raised.value.kind is CapKind.TOTAL_TOKENS
    assert raised.value.snapshot.total_tokens == 11
    assert_sticky_cap(budget, CapKind.TOTAL_TOKENS)


def test_provider_total_mismatch_is_rejected_instead_of_underpricing_cost() -> None:
    """Unexplained provider tokens cannot bypass the dollar cap."""

    budget = RunBudget(config(max_total_tokens=10))

    with pytest.raises(ValueError, match="provider_total_tokens must equal"):
        budget.record_model_usage(
            ModelUsage(input_tokens=3, output_tokens=3, provider_total_tokens=11)
        )


def test_wall_clock_cap_terminates_without_real_sleep() -> None:
    clock = ManualClock()
    budget = RunBudget(config(max_wall_seconds=2.0), clock=clock)
    clock.advance(2.0)

    with pytest.raises(CapExceeded) as raised:
        budget.check()

    assert raised.value.kind is CapKind.WALL_SECONDS
    assert raised.value.snapshot.elapsed_seconds == pytest.approx(2.0)
    assert_sticky_cap(budget, CapKind.WALL_SECONDS)


def test_cost_cap_terminates_after_observed_response() -> None:
    budget = RunBudget(
        config(
            max_cost_usd=0.50,
            input_usd_per_million=1_000_000.0,
            output_usd_per_million=1_000_000.0,
        )
    )

    with pytest.raises(CapExceeded) as raised:
        budget.record_model_usage(ModelUsage(input_tokens=1))

    assert raised.value.kind is CapKind.COST_USD
    assert raised.value.snapshot.estimated_cost_usd == pytest.approx(1.0)
    assert_sticky_cap(budget, CapKind.COST_USD)


@pytest.mark.parametrize("raw", ["nan", "inf", "-inf"])
def test_non_finite_cap_environment_values_are_rejected(
    raw: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MAX_WALL_SECONDS", raw)

    with pytest.raises(ValueError, match="MAX_WALL_SECONDS"):
        CapConfig.from_env()


def test_environment_cannot_zero_the_code_owned_price_table(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for variable in (
        "INPUT_USD_PER_MILLION",
        "CACHED_INPUT_USD_PER_MILLION",
        "CACHE_WRITE_USD_PER_MILLION",
        "OUTPUT_USD_PER_MILLION",
    ):
        monkeypatch.setenv(variable, "0")
        monkeypatch.setenv(f"UNCHAINED_{variable}", "0")

    configured = CapConfig.from_env()

    assert configured.input_usd_per_million == 5.0
    assert configured.cached_input_usd_per_million == 0.50
    assert configured.cache_write_usd_per_million == 6.25
    assert configured.output_usd_per_million == 30.0


def test_gpt56_cache_write_and_long_context_cost_math() -> None:
    prices = CapConfig()
    cache_write_only = ModelUsage(input_tokens=100_000, cache_write_tokens=100_000)
    long_context = ModelUsage(
        input_tokens=300_000,
        cached_input_tokens=60_000,
        cache_write_tokens=40_000,
        output_tokens=100_000,
    )

    assert estimate_usage_cost(prices, cache_write_only, "gpt-5.6") == pytest.approx(0.625)
    assert estimate_usage_cost(prices, long_context, "gpt-5.6") == pytest.approx(7.06)


@pytest.mark.parametrize(
    "usage",
    [
        ModelUsage(input_tokens=-1),
        ModelUsage(output_tokens=-1),
        ModelUsage(cached_input_tokens=-1),
        ModelUsage(cache_write_tokens=-1),
        ModelUsage(provider_total_tokens=-1),
    ],
)
def test_negative_usage_is_rejected_instead_of_reducing_cost(usage: ModelUsage) -> None:
    with pytest.raises(ValueError, match="nonnegative integer"):
        estimate_usage_cost(CapConfig(), usage)


def test_cache_accounting_larger_than_input_is_rejected() -> None:
    usage = ModelUsage(
        input_tokens=10,
        output_tokens=1,
        cached_input_tokens=8,
        cache_write_tokens=3,
        provider_total_tokens=11,
    )

    with pytest.raises(ValueError, match="cache read/write tokens"):
        estimate_usage_cost(CapConfig(), usage)


def test_request_preflight_fires_token_cap_before_starving_phase_minimum() -> None:
    budget = RunBudget(config(max_total_tokens=5_000))

    with pytest.raises(CapExceeded) as raised:
        budget.prepare_model_request(
            1_500,
            4_096,
            "gpt-5.6",
            minimum_output_tokens=4_096,
        )

    assert raised.value.kind is CapKind.TOTAL_TOKENS
    assert "phase minimum of 4096" in raised.value.detail
    assert_sticky_cap(budget, CapKind.TOTAL_TOKENS)


def test_request_preflight_fires_cost_cap_before_starving_phase_minimum() -> None:
    budget = RunBudget(config(max_cost_usd=0.001))

    with pytest.raises(CapExceeded) as raised:
        budget.prepare_model_request(
            100,
            4_096,
            "gpt-5.6",
            minimum_output_tokens=4_096,
        )

    assert raised.value.kind is CapKind.COST_USD
    assert "phase minimum of 4096" in raised.value.detail
    assert_sticky_cap(budget, CapKind.COST_USD)


@pytest.mark.parametrize("minimum", [0, True, 1.5, 4_097])
def test_request_preflight_rejects_invalid_phase_minimum(minimum: object) -> None:
    budget = RunBudget(config())

    with pytest.raises(ValueError, match="minimum_output_tokens"):
        budget.prepare_model_request(
            100,
            4_096,
            "gpt-5.6",
            minimum_output_tokens=minimum,  # type: ignore[arg-type]
        )
