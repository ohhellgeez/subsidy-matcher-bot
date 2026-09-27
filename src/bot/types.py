from dataclasses import dataclass, field


@dataclass
class Reply:
    text: str
    # список кнопок: (подпись, callback_data)
    buttons: list[tuple[str, str]] = field(default_factory=list)