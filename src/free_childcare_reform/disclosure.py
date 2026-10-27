"""UK Data Service disclosure control for the published household figures.

Microcosm UK is built from Family Resources Survey households, and the UK
Data Service End User Licence binds every published figure to the disclosure
control rules of its Research data handling and security guide (CD171,
section 5.2.1). Household effects are published by group — income decile,
family type, country — and some groups rest on few survey households, or can
be recovered as the difference of two published groups that do.

So those figures carry keyed noise. Each survey household's change is scaled
by one fixed factor 8-12% from 1, which policyengine.disclosure derives from
its id and the key in POLICYENGINE_DISCLOSURE_NOISE_KEY. The household moves
the same way in every table and every rerun, so subtraction between tables
cannot strip the noise. Noise goes on the change only: household counts and
incomes are exact. A figure resting on one or two survey households is
withheld (null). Microcosm's records are copies of survey households, so
households are counted by their source id, once each.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from policyengine.disclosure import noise_factors, resolve_noise_key

# CD171's absolute floor: below it a figure is withheld, noised or not.
MIN_SOURCES = 3
NOISE_DISTANCE = (0.08, 0.12)
# A change this small, in pounds a year, counts as no change and is left out
# of every sum, as in policyengine.disclosure, so floating-point residue does
# not count as a contributing household.
CHANGE_TOLERANCE = 1.0


@dataclass(frozen=True)
class Noise:
    """Each household's survey household and noise factor, and the same per person."""

    household_source: np.ndarray
    household_factor: np.ndarray
    person_source: np.ndarray
    person_factor: np.ndarray


def noise_for(sim, dataset: str, year: int, key: str | bytes | None = None) -> Noise:
    """The noise for ``sim``'s households, read from the dataset's source ids.

    Without ``key``, the key comes from POLICYENGINE_DISCLOSURE_NOISE_KEY, and
    a missing key fails here, before any figure is computed.
    """
    resolved = resolve_noise_key(key)
    table = pd.read_hdf(dataset, "household")
    households = np.asarray(sim.calculate("household_id", year).values)
    source = table.set_index("household_id")["source_household_id"].reindex(households)
    if source.isna().any():
        raise ValueError(f"{dataset}: some households have no source household id")
    household_source = source.to_numpy()
    household_factor = noise_factors(household_source, resolved, distance=NOISE_DISTANCE)
    person_household = np.asarray(sim.calculate("household_id", year, map_to="person").values)
    position = pd.Index(households).get_indexer(person_household)
    return Noise(
        household_source=household_source,
        household_factor=household_factor,
        person_source=household_source[position],
        person_factor=household_factor[position],
    )


def too_few(sources) -> bool:
    """Whether a figure resting on these records rests on one or two survey households."""
    return 0 < pd.unique(np.asarray(sources, dtype=object)).size < MIN_SOURCES


def withhold_rows(rows: dict, sources: dict, fields: tuple[str, ...]) -> None:
    """Withhold ``fields`` in rows resting on one or two survey households, in place.

    ``rows`` and ``sources`` share their keys; ``sources`` holds the survey
    households each row's ``fields`` rest on. The rows partition a published
    total, so a single withheld row would come back by subtraction: the row
    with the fewest households among the rest is withheld beside it, until the
    withheld rows together rest on at least MIN_SOURCES survey households.
    """
    withheld = [name for name in rows if too_few(sources[name])]
    if not withheld:
        return

    def households(names) -> int:
        return pd.unique(np.concatenate([np.asarray(sources[n], dtype=object) for n in names])).size

    rest = sorted(
        (name for name in rows if name not in withheld and len(sources[name])),
        key=lambda name: households([name]),
    )
    while (len(withheld) < 2 or households(withheld) < MIN_SOURCES) and rest:
        withheld.append(rest.pop(0))
    for name in withheld:
        for field in fields:
            rows[name][field] = None
