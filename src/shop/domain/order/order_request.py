import hashlib
from dataclasses import dataclass

from shop.domain.order.order_line import OrderLine


@dataclass(frozen=True, slots=True)
class OrderRequest:
    customer: str
    lines: tuple[OrderLine, ...]

    @property
    def skus(self) -> tuple[str, ...]:
        return tuple(sorted({line.sku for line in self.lines}))

    @property
    def reference(self) -> str:
        canonical = (
            self.customer + "|" + ";".join(f"{line.sku}x{line.quantity}" for line in self.lines)
        )
        return "ORD-" + hashlib.sha256(canonical.encode()).hexdigest()[:16].upper()
