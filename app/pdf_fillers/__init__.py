"""PDF filler subpackage.

Currently exposes fill_161d_form which fills the 161d tax form.
The implementation delegates to the original function that lives in
app.pdf_filler to avoid code duplication while we gradually migrate
all PDF related utilities into this sub-package.
"""

from .form161d import fill_161d

# Export only the minimal simple filler for now
__all__ = ["fill_161d"]
