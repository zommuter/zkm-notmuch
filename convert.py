"""zkm-notmuch — filesystem-discovery shim; delegates to the zkm_notmuch package.

Loaded by core when the plugin is filesystem-discovered (dev-symlink workflow).
Core's _inject_plugin_venv (SB2) adds plugins/zkm-notmuch/src/ to sys.path before
loading this file, making zkm_notmuch importable here.
"""

from zkm_notmuch.convert import convert  # noqa: F401
