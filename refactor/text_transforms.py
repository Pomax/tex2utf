"""
Text transformation functions for tex2utf.

This module provides functions to convert plain ASCII text into
Unicode mathematical styled characters. These are used for:
- \\mathcal{}: Script/calligraphic style (𝒜, 𝓑, 𝒞, ...)
- \\mathbf{}: Bold style (𝐀, 𝐁, 𝐂, ...)
- \\mathit{}: Italic style (𝐴, 𝐵, 𝐶, ...)

Unicode Mathematical Alphanumeric Symbols:
------------------------------------------
Unicode provides styled variants of Latin letters in the
Mathematical Alphanumeric Symbols block (U+1D400–U+1D7FF).
These allow rendering styled math without actual font changes.

Note: Not all characters have script variants (e.g., some lowercase
letters may use italic forms as fallbacks).
"""


def make_text_fancy(input_text: str) -> str:
    """
    Convert text to fancy/script style (\\mathcal).

    Uses Unicode Mathematical Script characters where available.

    Args:
        input_text: Plain ASCII text

    Returns:
        Text with script-style Unicode characters

    Example:
        make_text_fancy("ABC") -> "𝒜𝓑𝒞"
    """
    result = []
    for char in input_text:
        if "A" <= char <= "Z":
            script_map = {
                "A": "𝒜", "B": "𝓑", "C": "𝒞", "D": "𝓓", "E": "𝓔",
                "F": "𝓕", "G": "𝓖", "H": "𝓗", "I": "𝓘", "J": "𝓙",
                "K": "𝓚", "L": "𝓛", "M": "𝓜", "N": "𝓝", "O": "𝓞",
                "P": "𝓟", "Q": "𝓠", "R": "𝓡", "S": "𝓢", "T": "𝓣",
                "U": "𝓤", "V": "𝓥", "W": "𝓦", "X": "𝓧", "Y": "𝓨",
                "Z": "𝓩",
            }
            result.append(script_map.get(char, char))
        elif "a" <= char <= "z":
            script_map = {
                "a": "𝒶", "b": "𝒷", "c": "𝒸", "d": "𝒹", "e": "𝑒",
                "f": "𝒻", "g": "𝑔", "h": "𝒽", "i": "𝒾", "j": "𝒿",
                "k": "𝓀", "l": "𝓁", "m": "𝓂", "n": "𝓃", "o": "𝑜",
                "p": "𝓅", "q": "𝓆", "r": "𝓇", "s": "𝓈", "t": "𝓉",
                "u": "𝓊", "v": "𝓋", "w": "𝓌", "x": "𝓍", "y": "𝓎",
                "z": "𝓏",
            }
            result.append(script_map.get(char, char))
        else:
            result.append(char)
    return "".join(result)


def make_text_bold(text_input: str) -> str:
    """
    Convert text to bold style (\\mathbf).

    Uses Unicode Mathematical Bold characters.

    Args:
        text_input: Plain ASCII text

    Returns:
        Text with bold-style Unicode characters

    Example:
        make_text_bold("ABC") -> "𝐀𝐁𝐂"
    """
    result = []
    for char in text_input:
        if "A" <= char <= "Z":
            script_map = {
                "A": "𝐀", "B": "𝐁", "C": "𝐂", "D": "𝐃", "E": "𝐄",
                "F": "𝐅", "G": "𝐆", "H": "𝐇", "I": "𝐈", "J": "𝐉",
                "K": "𝐊", "L": "𝐋", "M": "𝐌", "N": "𝐍", "O": "𝐎",
                "P": "𝐏", "Q": "𝐐", "R": "𝐑", "S": "𝐒", "T": "𝐓",
                "U": "𝐔", "V": "𝐕", "W": "𝐖", "X": "𝐗", "Y": "𝐘",
                "Z": "𝐙",
            }
            result.append(script_map.get(char, char))
        elif "a" <= char <= "z":
            script_map = {
                "a": "𝐚", "b": "𝐛", "c": "𝐜", "d": "𝐝", "e": "𝐞",
                "f": "𝐟", "g": "𝐠", "h": "𝐡", "i": "𝐢", "j": "𝐣",
                "k": "𝐤", "l": "𝐥", "m": "𝐦", "n": "𝐧", "o": "𝐨",
                "p": "𝐩", "q": "𝐪", "r": "𝐫", "s": "𝐬", "t": "𝐭",
                "u": "𝐮", "v": "𝐯", "w": "𝐰", "x": "𝐱", "y": "𝐲",
                "z": "𝐳",
            }
            result.append(script_map.get(char, char))
        elif "0" <= char <= "9":
            script_map = {
                "0": "𝟎", "1": "𝟏", "2": "𝟐", "3": "𝟑", "4": "𝟒",
                "5": "𝟓", "6": "𝟔", "7": "𝟕", "8": "𝟖", "9": "𝟗",
            }
            result.append(script_map.get(char, char))
        else:
            result.append(char)
    return "".join(result)


def make_text_italic(text_input: str) -> str:
    """
    Convert text to italic style (\\mathit).

    Uses Unicode Mathematical Italic characters.

    Args:
        text_input: Plain ASCII text

    Returns:
        Text with italic-style Unicode characters

    Example:
        make_text_italic("ABC") -> "𝐴𝐵𝐶"
    """
    result = []
    for char in text_input:
        if "A" <= char <= "Z":
            script_map = {
                "A": "𝐴", "B": "𝐵", "C": "𝐶", "D": "𝐷", "E": "𝐸",
                "F": "𝐹", "G": "𝐺", "H": "𝐻", "I": "𝐼", "J": "𝐽",
                "K": "𝐾", "L": "𝐿", "M": "𝑀", "N": "𝑁", "O": "𝑂",
                "P": "𝑃", "Q": "𝑄", "R": "𝑅", "S": "𝑆", "T": "𝑇",
                "U": "𝑈", "V": "𝑉", "W": "𝑊", "X": "𝑋", "Y": "𝑌",
                "Z": "𝑍",
            }
            result.append(script_map.get(char, char))
        elif "a" <= char <= "z":
            script_map = {
                "a": "𝑎", "b": "𝑏", "c": "𝑐", "d": "𝑑", "e": "𝑒",
                "f": "𝑓", "g": "𝑔", "h": "ℎ", "i": "𝑖", "j": "𝑗",
                "k": "𝑘", "l": "𝑙", "m": "𝑚", "n": "𝑛", "o": "𝑜",
                "p": "𝑝", "q": "𝑞", "r": "𝑟", "s": "𝑠", "t": "𝑡",
                "u": "𝑢", "v": "𝑣", "w": "𝑤", "x": "𝑥", "y": "𝑦",
                "z": "𝑧",
            }
            result.append(script_map.get(char, char))
        else:
            result.append(char)
    return "".join(result)
