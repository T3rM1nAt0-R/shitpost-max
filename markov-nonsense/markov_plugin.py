import json
import os
import random
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost

CORPUS = "the cat sat on the mat. the dog ran in the park. the cat chased the dog around the park."

def build_bigram_table(corpus: str) -> dict:
    words = corpus.split()
    table = {}
    for i in range(len(words) - 2):
        key = (words[i], words[i + 1])
        next_word = words[i + 2]
        table.setdefault(key, {})
        table[key][next_word] = table[key].get(next_word, 0) + 1
    return table

def generate_sentence(table: dict, rng: random.Random) -> str:
    keys = list(table.keys())
    start_key = rng.choice(keys)
    word_list = list(start_key)
    while True:
        current_key = tuple(word_list[-2:])
        if current_key not in table:
            break
        next_word = rng.choices(list(table[current_key].keys()), weights=list(table[current_key].values()), k=1)[0]
        word_list.append(next_word)
        if word_list[-1][-1] in '.!?':
            break
        if len(word_list) >= 50:
            break
    return " ".join(word_list)

def _walk(table, rng, start_key):
    word_list = list(start_key)
    while True:
        current_key = tuple(word_list[-2:])
        if current_key not in table:
            break
        next_word = rng.choices(list(table[current_key].keys()), weights=list(table[current_key].values()), k=1)[0]
        word_list.append(next_word)
        if word_list[-1][-1] in ".!?":
            break
        if len(word_list) >= 50:
            break
    return " ".join(word_list)


class MarkovNonsensePlugin(Shitpost):
    """Generate a random sentence using a bigram markov chain."""

    name = "markov-nonsense"
    internal = False
    commit_template = "markov: {sentence}"

    def produce(self) -> dict:
        table = build_bigram_table(CORPUS)
        rng = random.Random()
        keys = list(table.keys())
        start_key = rng.choice(keys)
        seed_bigram = " ".join(start_key)
        sentence = _walk(table, rng, start_key)
        word_count = len(sentence.split())
        tick = self._load_state().get('tick', 0) + 1
        self._save_state({'tick': tick})
        return {
            "tick": tick,
            "sentence": sentence,
            "word_count": word_count,
            "seed_bigram": seed_bigram
        }

    def _load_state(self) -> dict:
        path = os.path.join(self._plugin_dir(), 'markov_state.json')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_state(self, state: dict) -> None:
        path = os.path.join(self._plugin_dir(), 'markov_state.json')
        tmp_path = path + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, separators=(',', ':'), sort_keys=True)
            f.write('\n')
        os.replace(tmp_path, path)

