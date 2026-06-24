import re
import logging
from typing import List, Optional, Set, Tuple

from jamdict import Jamdict

logger = logging.getLogger(__name__)

_STRIP = re.compile(r"[.\u30fb\-\uff0d\u30fc()\uff08\uff09　 ]")


class ValidationResult:
    def __init__(
        self,
        is_valid: bool,
        issues: List[str],
        suggested_on: Optional[str] = None,
        suggested_kun: Optional[str] = None,
    ):
        self.is_valid = is_valid
        self.issues = issues
        self.suggested_on = suggested_on
        self.suggested_kun = suggested_kun


class KanjiValidator:
    def __init__(self):
        try:
            self._jam = Jamdict()

            self._jam.lookup("水")
            self.available = True
            logger.info("KanjiValidator initialized (KanjiDic2 via jamdict)")
        except Exception as e:
            logger.warning("Failed to initialize jamdict/KanjiDic2: %s", e)
            self._jam = None
            self.available = False


    def validate_entry(self, kanji: str, proposed_readings: List[str]) -> ValidationResult:
        if not self.available:
            return ValidationResult(True, ["KanjiDic2 unavailable"])

        on_proposed = proposed_readings[0] if len(proposed_readings) > 0 else ""
        kun_proposed = proposed_readings[1] if len(proposed_readings) > 1 else ""

        on_set, kun_set = self._readings(kanji)
        if on_set is None:
            return ValidationResult(True, [f"{kanji} not in KanjiDic2; trusting model"])

        issues: List[str] = []
        suggested_on: Optional[str] = None
        suggested_kun: Optional[str] = None

        if on_proposed.strip():
            if self._norm(on_proposed) not in on_set:
                issues.append(f"on-yomi '{on_proposed}' not a known reading of {kanji}")
                suggested_on = self._pick(on_set)

        if kun_proposed.strip():
            if self._norm(kun_proposed) not in kun_set:
                issues.append(f"kun-yomi '{kun_proposed}' not a known reading of {kanji}")
                suggested_kun = self._pick(kun_set)

        return ValidationResult(
            is_valid=(len(issues) == 0),
            issues=issues,
            suggested_on=suggested_on,
            suggested_kun=suggested_kun,
        )

    # internals

    def _readings(self, kanji: str) -> Tuple[Optional[Set[str]], Optional[Set[str]]]:
        """Return (on_set, kun_set) of normalized readings, or (None, None) if unknown."""
        try:
            res = self._jam.lookup(kanji)
        except Exception as e:
            logger.debug("KanjiDic2 lookup failed for %s: %s", kanji, e)
            return None, None

        if not res.chars:
            return None, None

        char = res.chars[0]
        on: Set[str] = set()
        kun: Set[str] = set()
        for group in char.rm_groups:
            for r in group.readings:
                if r.r_type == "ja_on":
                    on.add(self._norm(r.value))
                elif r.r_type == "ja_kun":
                    kun.add(self._norm(r.value))
        return on, kun

    @staticmethod
    def _norm(reading: str) -> str:
        return _STRIP.sub("", reading).strip()

    @staticmethod
    def _pick(readings: Set[str]) -> Optional[str]:
        if not readings:
            return None
        return sorted(readings, key=len)[0]