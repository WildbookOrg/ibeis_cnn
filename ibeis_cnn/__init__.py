### __init__.py ###
# flake8: noqa
from __future__ import absolute_import, division, print_function
from ibeis_cnn import models
from ibeis_cnn import process
from ibeis_cnn import train
from ibeis_cnn import utils
from ibeis_cnn import theano_ext
#from ibeis_cnn import _plugin
import utool
print, print_, printDBG, rrr, profile = utool.inject(
    __name__, '[ibeis_cnn]')

__version__ = '1.0.0.dev1'


def reassign_submodule_attributes(verbose=True):
    """
    why reloading all the modules doesnt do this I don't know
    """
    import sys
    if verbose and '--quiet' not in sys.argv:
        print('dev reimport')
    # Self import
    import ibeis_cnn
    # Implicit reassignment.
    seen_ = set([])
    for tup in IMPORT_TUPLES:
        if len(tup) > 2 and tup[2]:
            continue  # dont import package names
        submodname, fromimports = tup[0:2]
        submod = getattr(ibeis_cnn, submodname)
        for attr in dir(submod):
            if attr.startswith('_'):
                continue
            if attr in seen_:
                # This just holds off bad behavior
                # but it does mimic normal util_import behavior
                # which is good
                continue
            seen_.add(attr)
            setattr(ibeis_cnn, attr, getattr(submod, attr))


def reload_subs(verbose=True):
    """ Reloads ibeis_cnn and submodules """
    rrr(verbose=verbose)
    def fbrrr(*args, **kwargs):
        """ fallback reload """
        pass
    getattr(models, 'rrr', fbrrr)(verbose=verbose)
    getattr(process, 'rrr', fbrrr)(verbose=verbose)
    getattr(train, 'rrr', fbrrr)(verbose=verbose)
    getattr(utils, 'rrr', fbrrr)(verbose=verbose)
    rrr(verbose=verbose)
    try:
        # hackish way of propogating up the new reloaded submodule attributes
        reassign_submodule_attributes(verbose=verbose)
    except Exception as ex:
        print(ex)
rrrr = reload_subs

IMPORT_TUPLES = [
    ('ibsplugin', None),
    ('models', None),
    ('process', None),
    ('train', None),
    ('utils', None),
]
"""
Regen Command:
    cd /home/joncrall/code/ibeis_cnn/ibeis_cnn
    makeinit.py -x _grave old_test old_models old_train sandbox
"""
# autogenerated __init__.py for: '/home/joncrall/code/ibeis_cnn/ibeis_cnn'
