from collections.abc import Sequence
from dataclasses import dataclass
from math import prod

from shop_benchmark.domain.endpoint_result import EndpointResult
from shop_benchmark.domain.load_profile import LoadProfile
from shop_benchmark.domain.run_report import RunReport


@dataclass(frozen=True, slots=True)
class Standing:
    framework: str
    result: EndpointResult
    ratio: float


@dataclass(frozen=True, slots=True)
class Matchup:
    endpoint: str
    label: str
    profile: LoadProfile
    standings: tuple[Standing, ...]

    @property
    def winner(self) -> str:
        return self.standings[0].framework

    def standing(self, framework: str) -> Standing | None:
        return next((item for item in self.standings if item.framework == framework), None)


@dataclass(frozen=True, slots=True)
class Score:
    framework: str
    profile: str
    score: float
    wins: int


@dataclass(frozen=True, slots=True)
class Comparison:
    reports: tuple[RunReport, ...]
    profiles: tuple[LoadProfile, ...]
    matchups: tuple[Matchup, ...]

    @classmethod
    def of(cls, reports: Sequence[RunReport]) -> Comparison:
        profiles = _shared_profiles(reports)
        endpoints = _endpoints(reports)
        matchups = tuple(
            _matchup(reports, endpoint, profile) for profile in profiles for endpoint in endpoints
        )
        return cls(tuple(reports), profiles, tuple(matchup for matchup in matchups if matchup))

    @property
    def frameworks(self) -> list[str]:
        return [report.framework for report in self.reports]

    def matchups_for(self, profile: str) -> list[Matchup]:
        return [matchup for matchup in self.matchups if matchup.profile.name == profile]

    def scores(self, profile: str) -> list[Score]:
        matchups = self.matchups_for(profile)
        scores = []
        for framework in self.frameworks:
            ratios = [
                standing.ratio
                for matchup in matchups
                if (standing := matchup.standing(framework)) is not None
            ]
            wins = sum(1 for matchup in matchups if matchup.winner == framework)
            mean = prod(ratios) ** (1 / len(ratios)) if ratios else 0.0
            scores.append(Score(framework, profile, round(100 * mean, 1), wins))
        return sorted(scores, key=lambda score: -score.score)

    def mismatched_answers(self) -> list[str]:
        fingerprints: dict[str, set[str]] = {}
        for report in self.reports:
            for answer in report.answers:
                fingerprints.setdefault(answer.endpoint, set()).add(answer.fingerprint)
        return sorted(endpoint for endpoint, seen in fingerprints.items() if len(seen) > 1)


def _shared_profiles(reports: Sequence[RunReport]) -> tuple[LoadProfile, ...]:
    if not reports:
        return ()
    names = set.intersection(*({profile.name for profile in report.profiles} for report in reports))
    return tuple(profile for profile in reports[0].profiles if profile.name in names)


def _endpoints(reports: Sequence[RunReport]) -> list[str]:
    ordered = [result.endpoint for result in reports[0].results] if reports else []
    return list(dict.fromkeys(ordered))


def _matchup(reports: Sequence[RunReport], endpoint: str, profile: LoadProfile) -> Matchup | None:
    results = [
        (report.framework, result)
        for report in reports
        if (result := report.result(endpoint, profile.name)) is not None
    ]
    if not results:
        return None
    if profile.is_fixed_rate:
        best = min(result.measurement.latency.p99_ms for _, result in results)
        ranked = sorted(results, key=lambda item: item[1].measurement.latency.p99_ms)
        standings = tuple(
            Standing(
                framework,
                result,
                best / result.measurement.latency.p99_ms
                if result.measurement.latency.p99_ms
                else 0.0,
            )
            for framework, result in ranked
        )
    else:
        best = max(result.measurement.requests_per_second for _, result in results)
        ranked = sorted(results, key=lambda item: -item[1].measurement.requests_per_second)
        standings = tuple(
            Standing(
                framework, result, result.measurement.requests_per_second / best if best else 0.0
            )
            for framework, result in ranked
        )
    return Matchup(endpoint, results[0][1].label, profile, standings)
