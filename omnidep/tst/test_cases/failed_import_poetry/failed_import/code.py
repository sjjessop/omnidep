
# Import something not installed locally: will provoke error as long as this
# file is actually checked
import no_such_module  # type: ignore[import-not-found]  # noqa: F401
