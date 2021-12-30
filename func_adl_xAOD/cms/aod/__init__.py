from .cms_functions import isNonnull  # NOQA
try:
    import python_on_whales  # NOQA
    from .local_dataset import CMSRun1AODDataset  # NOQA
except ImportError:  # pragma: no cover
    pass
