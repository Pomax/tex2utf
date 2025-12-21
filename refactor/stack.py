"""
Stack operations for tex2utf.

This module manages the grouping/scoping mechanism that tracks nested
LaTeX structures. LaTeX has many nested constructs:
- Brace groups: {content}
- Math modes: $...$ and $$...$$
- Environments: \\begin{env}...\\end{env}
- Delimiters: \\left(...\\right)

The stack system tracks:
- level: What nesting depth we're at
- chunks: Where each group's output starts
- wait: What token/event will close each group
- action: What function to call when the group closes

When a group closes, its contents can be processed (e.g., building
a fraction from numerator and denominator groups).

Key Functions:
--------------
- start(): Begin a new group
- finish(): End the current group
- commit(): Add a record to the output
- collapse(): Merge multiple records into one
- trim(): Remove whitespace from record edges
- finishBuffer(): Flush all pending output
"""

from .config import debug_log
from .records import empty, string2record, get_length
from . import state


def commit(rec: str):
    """
    Commit a record to the output buffer.
    
    This is the primary way content gets added to the output.
    If we're at the top level, handles line-length checking.
    If we're in a group that's waiting for a certain number of
    items, may trigger the group's action callback.
    
    Args:
        rec: A record string to add to output
    """
    from . import config
    from .output import prepare_cut
    
    debug_log(f"commit: rec={rec[:50]}...")
    
    # At top level, check line length
    if len(state.level) == 1:
        l = get_length(rec)
        if state.curlength + l > config.linelength:
            rec = prepare_cut(rec)
            l = get_length(rec)
        state.curlength += l
    
    # Add to output buffer
    state.out.append(rec)
    
    # Track chunk boundary
    if len(state.out) - 1 != state.chunks[-1]:
        state.chunks.append(len(state.out) - 1)
    
    # Check if current group is waiting for a specific number of items
    if len(state.level) > 1 and state.wait[len(state.level) - 1] == len(state.chunks) - state.level[len(state.level) - 1]:
        sub = state.action[len(state.level) - 1]
        debug_log(f"commit: triggering action '{sub}'")
        if sub == "":
            finish(state.wait[len(state.level) - 1])
        else:
            callsub(sub)


def uncommit() -> str:
    """
    Remove and return the last committed record.
    
    Used when we need to modify the last output item.
    
    Returns:
        The removed record
    """
    if not state.out:
        return empty()
    if len(state.level) == 1:
        state.curlength -= get_length(state.out[-1])
    rec = state.out[-1]
    state.out[-1] = empty()
    return rec


def finish(event, force_one_group: bool = False):
    """
    Finish (close) the current group.
    
    Called when we encounter a closing delimiter or when a group
    has collected all its expected items.
    
    Args:
        event: The event/token that triggered the close
        force_one_group: If True, keep output as single group
    """
    debug_log(f"finish: event={event}, force={force_one_group}")
    
    if len(state.level) <= 1:
        return
    
    # Ensure we have content for this group
    if len(state.out) < state.chunks[state.level[-1]]:
        state.out.append(empty())
    
    state.chunks[:] = state.chunks[: state.level[-1] + 1]
    
    # Save output if at level 2
    t = []
    if len(state.level) == 2 and not force_one_group:
        t = state.out[state.chunks[-1] :]
        state.out = state.out[: state.chunks[-1]]
    
    # Pop the level
    state.level.pop()
    state.action.pop()
    state.tokenByToken.pop()
    state.wait.pop()
    
    # Re-commit saved output
    if len(state.level) == 1 and not force_one_group:
        for rec in t:
            commit(rec)
    
    # Check if parent group is now complete
    if len(state.level) > 1 and state.wait[-1] == len(state.chunks) - state.level[-1]:
        sub = state.action[-1]
        if sub == "":
            finish(state.wait[-1])
        else:
            callsub(sub)


def finish_ignore(event):
    """
    Finish the current group and discard its output.
    
    Used for commands like \\hphantom that consume arguments
    but produce no output.
    
    Args:
        event: The event/token that triggered the close
    """
    if len(state.level) <= 1:
        return
    state.out[:] = state.out[: state.chunks[state.level[-1]]]
    state.level.pop()
    state.tokenByToken.pop()
    state.action.pop()
    state.wait.pop()


def start(event, act: str = ""):
    """
    Start a new group/scope.
    
    Called when we encounter an opening delimiter or begin
    collecting arguments for a command.
    
    Args:
        event: The closing event to wait for (e.g., "}", "$")
               or a number indicating how many items to collect
        act: Name of function to call when group completes
    """
    debug_log(f"start: event={event}, action={act}")
    
    if state.chunks[state.level[-1]] <= len(state.out) - 1 and state.chunks[-1] <= len(state.out) - 1:
        state.chunks.append(len(state.out))
    
    state.level.append(len(state.chunks) - 1)
    state.tokenByToken.append(0)
    state.wait.append(event)
    state.action.append(act)


def assertHave(n: int) -> bool:
    """
    Check if we have at least n chunks in the current group.
    
    Used before operations that require a certain number of
    collected items (e.g., fraction needs 2 items).
    
    Args:
        n: Required number of chunks
        
    Returns:
        True if we have enough chunks
    """
    have = len(state.chunks) - state.level[-1]
    debug_log(f"assertHave: need={n}, have={have}")
    return have >= n


def collapse(n: int):
    """
    Collapse the last n chunks into joined records.
    
    Merges multiple consecutive records within each chunk.
    
    Args:
        n: Number of chunks to collapse
    """
    have = len(state.chunks) - state.level[-1]
    debug_log(f"collapse: n={n}, have={have}")
    if have < n:
        n = have
    if n > 0:
        for i in range(n):
            collapseOne(len(state.chunks) - 1 - i)
        for i in range(1, n):
            state.chunks[len(state.chunks) - i] = state.chunks[len(state.chunks) - n] + n - i


def collapseAll():
    """Collapse all chunks at the current level."""
    collapse(len(state.chunks) - state.level[-1])


def collapseOne(n: int):
    """
    Collapse a single chunk by joining all its records.
    
    Args:
        n: Index of chunk to collapse
    """
    from .join import join_records
    
    if n >= len(state.chunks):
        return
    
    if n == len(state.chunks) - 1:
        last = len(state.out) - 1
    else:
        last = state.chunks[n + 1] - 1
    
    start_idx = state.chunks[n]
    debug_log(f"collapseOne: n={n}, start={start_idx}, last={last}")
    
    if last <= start_idx:
        return
    
    # Join all records in this chunk
    result = state.out[start_idx]
    for i in range(start_idx + 1, last + 1):
        result = join_records(result, state.out[i])
    state.out[start_idx : last + 1] = [result]


def trim_end(idx: int):
    """
    Trim trailing whitespace from a record.
    
    Args:
        idx: Index into output buffer
    """
    if not state.out or idx < 0 or idx >= len(state.out):
        return
    parts = state.out[idx].split(",", 4)
    h = int(parts[0])
    s = parts[4] if len(parts) > 4 else ""
    if not h:  # Only for single-line records
        s = s.rstrip()
        state.out[idx] = string2record(s)


def trim_beg(idx: int):
    """
    Trim leading whitespace from a record.
    
    Args:
        idx: Index into output buffer
    """
    if not state.out or idx < 0 or idx >= len(state.out):
        return
    parts = state.out[idx].split(",", 4)
    h = int(parts[0])
    s = parts[4] if len(parts) > 4 else ""
    if not h:
        s = s.lstrip()
        state.out[idx] = string2record(s)


def trim_one(n: int):
    """
    Trim whitespace from both ends of a chunk.
    
    Args:
        n: Chunk index
    """
    trim_beg(state.chunks[n])
    if n == len(state.chunks) - 1:
        trim_end(len(state.out) - 1)
    else:
        trim_end(state.chunks[n + 1] - 1)


def trim(n: int):
    """
    Trim whitespace from the last n chunks.
    
    Args:
        n: Number of chunks to trim
    """
    debug_log(f"trim: n={n}")
    for i in range(len(state.chunks) - n, len(state.chunks)):
        trim_one(i)


def finishBuffer():
    """
    Finish all pending groups and print remaining output.
    
    Called at end of input or paragraph to flush everything.
    """
    from .output import do_print
    
    while len(state.level) > 1:
        finish("")
    do_print(True)


def puts(s: str, no_expand: bool = False):
    """
    Convenience function to commit a string as a record.
    
    Args:
        s: String to output
        no_expand: If True, spaces won't be expanded for justification
    """
    commit(string2record(s, no_expand))


def callsub(sub: str):
    """
    Call a handler function by name.
    
    Used to invoke callbacks when groups complete.
    Supports both simple names ("f_fraction") and names
    with arguments ("f_putover_string;^").
    
    Args:
        sub: Function name, optionally with ";arg" suffix
    """
    from . import commands
    from . import math_ops
    
    if ";" in sub:
        parts = sub.split(";", 1)
        name, arg = parts[0], parts[1]
        # Try to find the function in various modules
        func = None
        for module in [commands, math_ops]:
            if hasattr(module, name):
                func = getattr(module, name)
                break
        if func:
            func(arg)
    else:
        func = None
        for module in [commands, math_ops]:
            if hasattr(module, sub):
                func = getattr(module, sub)
                break
        if func:
            func()
