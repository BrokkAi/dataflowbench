"""Explicit environment selection for the versioned release executor."""
import os
from pathlib import Path


def semgrep_environment(launcher, inherited=None):
    """Keep Semgrep's Python fallback in the same pinned environment as its core.

    Semgrep's entrypoint appends its own scripts directory to PATH. An older
    system pysemgrep can consequently win unless the caller prepends it.
    Preserve later PATH entries because other pinned adapter dependencies may
    need them; the reviewed command still names each primary executable exactly.
    """
    launcher = Path(launcher)
    if not launcher.is_absolute() or not launcher.is_file():
        raise ValueError('Semgrep launcher must be an existing absolute file')
    scripts = launcher.parent
    fallback = scripts / 'pysemgrep'
    if not fallback.is_file():
        raise ValueError('pinned Semgrep environment lacks pysemgrep fallback')
    env = dict(os.environ if inherited is None else inherited)
    inherited_path = env.get('PATH', os.defpath)
    remaining = [p for p in inherited_path.split(os.pathsep) if p and p != str(scripts)]
    env['PATH'] = os.pathsep.join([str(scripts), *remaining])
    env['SEMGREP_ENABLE_VERSION_CHECK'] = '0'
    return env
