from collections.abc import Sequence

MEGABYTE: float = 1024 * 1024


def rate(value: float) -> str:
    return f"{value:,.0f}".replace(",", " ")


def ms(value: float) -> str:
    return f"{value:.2f}"


def megabytes_per_second(value: float) -> str:
    return f"{value / MEGABYTE:.1f}"


def percent(value: float) -> str:
    return f"{value:.0f}"


def fewer(ratio: float) -> str:
    return "" if ratio >= 0.9995 else f" ({(ratio - 1) * 100:+.0f} %)"


def slower(ratio: float) -> str:
    return "" if ratio >= 0.9995 or ratio <= 0 else f" ({(1 / ratio - 1) * 100:+.0f} %)"


def table(header: Sequence[str], align: Sequence[str], rows: Sequence[Sequence[str]]) -> list[str]:
    return [
        "| " + " | ".join(header) + " |",
        "|" + "|".join("---:" if side == "right" else "---" for side in align) + "|",
        *("| " + " | ".join(row) + " |" for row in rows),
    ]
