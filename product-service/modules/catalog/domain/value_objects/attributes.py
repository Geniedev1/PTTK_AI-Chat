from dataclasses import dataclass, field


@dataclass(frozen=True)
class Attributes:
    values: dict[str, object] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        return dict(self.values)
