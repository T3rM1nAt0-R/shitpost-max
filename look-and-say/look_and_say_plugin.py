"""Generates consecutive terms of the look-and-say sequence, capped at 15 terms then reset."""

from harness.shitpost_base import Shitpost

MAX_TERMS = 15


def _next_term(s):
    result = []
    i = 0
    while i < len(s):
        j = i
        while j < len(s) and s[j] == s[i]:
            j += 1
        result.append(str(j - i))
        result.append(s[i])
        i = j
    return "".join(result)


class LookAndSayPlugin(Shitpost):
    """Emit one look-and-say term per tick, resetting to term 0 after MAX_TERMS."""

    name = "look-and-say"
    internal = False
    commit_template = "look-and-say term {term_index}: {term_length} chars"

    def produce(self):
        state = self._load_persisted_state({"term_index": 0, "current_term": "1"})
        term_index = state["term_index"]
        current_term = state["current_term"]

        result = {
            "term_index": term_index,
            "term": current_term,
            "term_length": len(current_term),
        }

        if term_index == MAX_TERMS - 1:
            self._save_persisted_state({"term_index": 0, "current_term": "1"})
        else:
            next_term = _next_term(current_term)
            self._save_persisted_state({"term_index": term_index + 1, "current_term": next_term})

        return result
