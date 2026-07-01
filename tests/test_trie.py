from cyberbullying_api.normalizer import AbusiveTrie


def test_abusive_trie_search():
    trie = AbusiveTrie()
    trie.insert("anjing")
    trie.insert("goblok")
    trie.insert("bego")

    # Exact match should return None because search_edit_distance_one checks for exactly edit distance 1
    assert trie.search_edit_distance_one("anjing") is None

    # Edit distance 1 typos
    assert trie.search_edit_distance_one("anjingg") == "anjing"
    assert trie.search_edit_distance_one("anjin") == "anjing"
    assert trie.search_edit_distance_one("goblokk") == "goblok"

    # Edit distance > 1 typos should not match
    assert trie.search_edit_distance_one("anjinggg") is None
    assert trie.search_edit_distance_one("anj") is None
