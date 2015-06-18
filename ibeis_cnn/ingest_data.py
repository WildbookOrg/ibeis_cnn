# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
from ibeis_cnn import utils
from ibeis_cnn import ingest_helpers
from ibeis_cnn import ingest_ibeis
from ibeis_cnn.dataset import DataSet
from os.path import join, basename, splitext
import utool as ut
print, rrr, profile = ut.inject2(__name__, '[ibeis_cnn.ingest]')


def testdata_trainset():
    trainset = get_ibeis_siam_trainset(max_examples=5, controlled=False)
    return trainset


def testdata_patchmatch():
    """
        >>> from ibeis_cnn.ingest_data import *  # NOQA
    """
    trainset = get_ibeis_siam_trainset(max_examples=5)
    data_fpath = trainset.data_fpath
    labels_fpath = trainset.labels_fpath
    data_cv2, labels = utils.load(data_fpath, labels_fpath)
    data = utils.convert_cv2_images_to_theano_images(data_cv2)
    return data, labels


def testdata_patchmatch2():
    """
        >>> from ibeis_cnn.ingest_data import *  # NOQA
    """
    trainset = get_ibeis_siam_trainset(max_examples=5)
    data_fpath = trainset.data_fpath
    labels_fpath = trainset.labels_fpath
    data, labels = utils.load(data_fpath, labels_fpath)
    return data, labels


def get_extern_training_dpath(alias_key):
    return DataSet.from_alias_key(alias_key).training_dpath


def view_training_directories():
    r"""
    CommandLine:
        python -m ibeis_cnn.ingest_data --test-view_training_directories

    Example:
        >>> # UTILITY_SCRIPT
        >>> from ibeis_cnn.ingest_data import *  # NOQA
        >>> result = view_training_directories()
        >>> print(result)
    """
    ut.vd(ingest_ibeis.get_juction_dpath())


def grab_siam_trainset(ds_tag):
    """
    Will build the dataset using the command line if it doesnt exist

    CommandLine:
        python -m ibeis_cnn.ingest_data --test-grab_siam_trainset --db PZ_MTEST --show
        python -m ibeis_cnn.ingest_data --test-grab_siam_trainset --db NNP_Master3 --show
        python -m ibeis_cnn.ingest_data --test-grab_siam_trainset --db PZ_Master0 --show
        python -m ibeis_cnn.ingest_data --test-grab_siam_trainset --db mnist --show
        python -m ibeis_cnn.ingest_data --test-grab_siam_trainset --db liberty --show

        python -m ibeis_cnn.ingest_data --test-grab_siam_trainset --db PZ_MTEST

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis_cnn.ingest_data import *  # NOQA
        >>> ds_tag = None
        >>> trainset = grab_siam_trainset(ds_tag=ds_tag)
        >>> ut.quit_if_noshow()
        >>> from ibeis_cnn import draw_results
        >>> #ibsplugin.rrr()
        >>> flat_metadata = {}
        >>> data, labels = trainset.load_subset('all')
        >>> ut.quit_if_noshow()
        >>> warped_patch1_list = data[::2]
        >>> warped_patch2_list = data[1::2]
        >>> draw_results.interact_patches(labels, warped_patch1_list, warped_patch2_list, flat_metadata, sortby='rand')
        >>> print(result)
        >>> ut.show_if_requested()
    """
    if ds_tag is not None:
        try:
            return DataSet.from_alias_key(ds_tag)
        except Exception as ex:
            ut.printex(ex, 'Could not resolve alias. Need to rebuild dataset', keys=['ds_tag'])
            raise

    dbname = ut.get_argval('--db')
    if dbname == 'liberty':
        pairs = 250000
        trainset = grab_liberty_siam_trainset(pairs)
    elif dbname == 'mnist':
        trainset = grab_mnist_siam_trainset()
    else:
        trainset = get_ibeis_siam_trainset()
    return trainset


def grab_mnist_category_trainset():
    import numpy as np
    training_dpath = ut.get_app_resource_dir('ibeis_cnn', 'training', 'mnist')
    ut.ensuredir(training_dpath)
    data_fpath = join(training_dpath, 'mnist_data.cPkl')
    labels_fpath = join(training_dpath, 'mnist_labels.cPkl')
    if not ut.checkpath(data_fpath):
        train_imgs_fpath = ut.grab_zipped_url(
            'http://yann.lecun.com/exdb/mnist/train-images-idx3-ubyte.gz')
        train_lbls_fpath = ut.grab_zipped_url(
            'http://yann.lecun.com/exdb/mnist/train-labels-idx1-ubyte.gz')
        test_imgs_fpath = ut.grab_zipped_url(
            'http://yann.lecun.com/exdb/mnist/t10k-images-idx3-ubyte.gz')
        test_lbls_fpath = ut.grab_zipped_url(
            'http://yann.lecun.com/exdb/mnist/t10k-labels-idx1-ubyte.gz')

        train_images, train_labels = ingest_helpers.open_mnist_files(
            train_lbls_fpath, train_imgs_fpath)
        test_images, test_labels = ingest_helpers.open_mnist_files(
            test_lbls_fpath, test_imgs_fpath)
        data = np.vstack((train_images, test_images))
        labels = np.append(train_labels, test_labels)
        utils.write_data_and_labels(data, labels, data_fpath, labels_fpath)

    alias_key = 'mnist'

    trainset = DataSet.new_training_set(
        alias_key=alias_key,
        data_fpath=data_fpath,
        labels_fpath=labels_fpath,
        training_dpath=training_dpath,
        data_per_label=1,
        data_shape=(28, 28, 1),
        output_dims=10,
    )
    return trainset


def grab_mnist_siam_trainset():
    r"""

    CommandLine:
        python -m ibeis_cnn.ingest_data --test-grab_mnist_siam_trainset --show

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis_cnn.ingest_data import *  # NOQA
        >>> trainset = grab_mnist_siam_trainset()
        >>> ut.quit_if_noshow()
        >>> from ibeis_cnn import draw_results
        >>> #ibsplugin.rrr()
        >>> flat_metadata = {}
        >>> data, labels = trainset.load_subset('all')
        >>> ut.quit_if_noshow()
        >>> warped_patch1_list = data[::2]
        >>> warped_patch2_list = data[1::2]
        >>> draw_results.interact_patches(labels, warped_patch1_list, warped_patch2_list, flat_metadata, sortby='rand')
        >>> print(result)
        >>> ut.show_if_requested()
    """
    import numpy as np
    alias_key = 'mnist_pairs'

    training_dpath = ut.get_app_resource_dir('ibeis_cnn', 'training', alias_key)
    ut.ensuredir(training_dpath)

    data_fpath = join(training_dpath, alias_key + '_data.cPkl')
    labels_fpath = join(training_dpath, alias_key + '_labels.cPkl')
    if not ut.checkpath(data_fpath):
        train_imgs_fpath = ut.grab_zipped_url(
            'http://yann.lecun.com/exdb/mnist/train-images-idx3-ubyte.gz')
        train_lbls_fpath = ut.grab_zipped_url(
            'http://yann.lecun.com/exdb/mnist/train-labels-idx1-ubyte.gz')
        test_imgs_fpath = ut.grab_zipped_url(
            'http://yann.lecun.com/exdb/mnist/t10k-images-idx3-ubyte.gz')
        test_lbls_fpath = ut.grab_zipped_url(
            'http://yann.lecun.com/exdb/mnist/t10k-labels-idx1-ubyte.gz')

        train_images, train_labels = ingest_helpers.open_mnist_files(
            train_lbls_fpath, train_imgs_fpath)
        test_images, test_labels = ingest_helpers.open_mnist_files(
            test_lbls_fpath, test_imgs_fpath)

        category_data = np.vstack((train_images, test_images))
        category_labels = np.append(train_labels, test_labels)
        data, labels = ingest_helpers.convert_category_to_siam_data(category_data, category_labels)
        #metadata = {
        #    'flat_index_list': flat_index_list,
        #    'category_labels': category_labels.take(flat_index_list)
        #}
        utils.write_data_and_labels(data, labels, data_fpath, labels_fpath)
        #metadata = {}

    trainset = DataSet.new_training_set(
        alias_key=alias_key,
        data_fpath=data_fpath,
        labels_fpath=labels_fpath,
        training_dpath=training_dpath,
        data_per_label=2,
        data_shape=(28, 28, 1),
        output_dims=1,
    )
    return trainset


def grab_liberty_siam_trainset(pairs=250000):
    """
    References:
        http://www.cs.ubc.ca/~mbrown/patchdata/patchdata.html
        https://github.com/osdf/datasets/blob/master/patchdata/dataset.py

    Notes:
        "info.txt" contains the match information Each row of info.txt
        corresponds corresponds to a separate patch, with the patches ordered
        from left to right and top to bottom in each bitmap image.

        3 types of metadata files

        info.txt - contains patch ids that correspond with the order of patches
          in the bmp images
          In the format:
              pointid, unused

        interest.txt -
            interest points corresponding to patches with patchids
            has same number of rows as info.txt
            In the format:
                reference image id, x, y, orientation, scale (in log2 units)

        m50_<d>_<d>_0.txt -
             matches files
             patchID1  3DpointID1  unused1  patchID2  3DpointID2  unused2

    CommandLine:
        python -m ibeis_cnn.ingest_data --test-grab_liberty_siam_trainset --show

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis_cnn.ingest_data import *  # NOQA
        >>> pairs = 500
        >>> trainset = grab_liberty_siam_trainset(pairs)
        >>> ut.quit_if_noshow()
        >>> from ibeis_cnn import draw_results
        >>> #ibsplugin.rrr()
        >>> flat_metadata = {}
        >>> data, labels = trainset.load_subset('all')
        >>> ut.quit_if_noshow()
        >>> warped_patch1_list = data[::2]
        >>> warped_patch2_list = data[1::2]
        >>> draw_results.interact_patches(labels, warped_patch1_list, warped_patch2_list, flat_metadata, sortby='rand')
        >>> print(result)
        >>> ut.show_if_requested()
    """
    datakw = {
        'detector': 'dog',
        'pairs': pairs,
    }

    assert datakw['detector'] in ['dog', 'harris']
    assert pairs in [500, 50000, 100000, 250000]

    liberty_urls = {
        'dog': 'http://www.cs.ubc.ca/~mbrown/patchdata/liberty.zip',
        'harris': 'http://www.cs.ubc.ca/~mbrown/patchdata/liberty_harris.zip',
    }
    url = liberty_urls[datakw['detector']]
    ds_path = ut.grab_zipped_url(url)

    ds_name = splitext(basename(ds_path))[0]
    alias_key = 'liberty;' + ut.dict_str(datakw, nl=False, explicit=True)
    cfgstr = ','.join([str(val) for key, val in ut.iteritems_sorted(datakw)])

    training_dpath = ut.ensure_app_resource_dir('ibeis_cnn', 'training', ds_name)
    if ut.get_argflag('--vtd'):
        ut.vd(training_dpath)
    ut.ensuredir(training_dpath)

    data_fpath = join(training_dpath, 'liberty_data_' + cfgstr + '.cPkl')
    labels_fpath = join(training_dpath, 'liberty_labels_' + cfgstr  + '.cPkl')

    if not ut.checkpath(data_fpath, verbose=True):
        data, labels = ingest_helpers.extract_liberty_style_patches(ds_path, pairs)
        utils.write_data_and_labels(data, labels, data_fpath, labels_fpath)

    trainset = DataSet.new_training_set(
        alias_key=alias_key,
        data_fpath=data_fpath,
        labels_fpath=labels_fpath,
        training_dpath=training_dpath,
        data_shape=(64, 64, 1),
        data_per_label=2,
        output_dims=1,
    )
    return trainset


def get_ibeis_siam_trainset(**kwargs):
    """
    CommandLine:
        python -m ibeis_cnn.ingest_data --test-get_ibeis_siam_trainset --show
        python -m ibeis_cnn.ingest_data --test-get_ibeis_siam_trainset --show --db PZ_Master0

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis_cnn.ingest_data import *  # NOQA
        >>> from ibeis_cnn import draw_results
        >>> import ibeis
        >>> kwargs = {}  # ut.argparse_dict({'max_examples': None, 'num_top': 3})
        >>> trainset = get_ibeis_siam_trainset(**kwargs)
        >>> data_fpath = trainset.data_fpath
        >>> labels_fpath = trainset.labels_fpath
        >>> ut.quit_if_noshow()
        >>> draw_results.interact_siamese_data_fpath_patches(data_fpath, labels_fpath, {})
        >>> ut.show_if_requested()
    """
    datakw = ut.argparse_dict(
        {
            #'db': 'PZ_MTEST',
            'max_examples': None,
            'num_top': 3,
            'controlled': True,
        }, verbose=True)
    with ut.Indenter('[LOAD IBEIS DB]'):
        import ibeis
        dbname = ut.get_argval('--db', default='PZ_MTEST')
        ibs = ibeis.opendb(dbname=dbname)

    # Nets dir is the root dir for all training on this data
    training_dpath = ibs.get_neuralnet_dir()
    ut.ensuredir(training_dpath)
    datakw.update(kwargs)
    print('\n\n[get_ibeis_siam_trainset] START')
    #log_dir = join(training_dpath, 'logs')
    #ut.start_logging(log_dir=log_dir)

    alias_key = ibs.get_dbname() + ';' + ut.dict_str(datakw, nl=False, explicit=True)
    try:
        # Try and short circut cached loading
        trainset = DataSet.from_alias_key(alias_key)
        return trainset
    except Exception as ex:
        ut.printex(ex, 'alias definitions have changed. alias_key=%r' % (alias_key,), iswarning=True)

    with ut.Indenter('[CHECKDATA]'):
        # Get training data pairs
        patchmatch_tup = ingest_ibeis.get_aidpairs_and_matches(ibs, **datakw)
        aid1_list, aid2_list, kpts1_m_list, kpts2_m_list, fm_list, metadata_lists = patchmatch_tup
        # Extract and cache the data
        # TODO: metadata
        data_fpath, labels_fpath, training_dpath, data_shape = ingest_ibeis.cached_patchmetric_training_data_fpaths(
            ibs, aid1_list, aid2_list, kpts1_m_list, kpts2_m_list, fm_list, metadata_lists)
        print('\n[get_ibeis_siam_trainset] FINISH\n\n')

    trainset = DataSet.new_training_set(
        alias_key=alias_key,
        data_fpath=data_fpath,
        labels_fpath=labels_fpath,
        training_dpath=training_dpath,
        data_shape=data_shape,
        data_per_label=2,
        output_dims=1,
    )
    return trainset


if __name__ == '__main__':
    """
    CommandLine:
        python -m ibeis_cnn.ingest_data
        python -m ibeis_cnn.ingest_data --allexamples
        python -m ibeis_cnn.ingest_data --allexamples --noface --nosrc
    """
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    import utool as ut  # NOQA
    ut.doctest_funcs()
