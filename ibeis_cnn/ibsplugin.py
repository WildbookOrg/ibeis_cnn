from __future__ import absolute_import, division, print_function
import utool as ut
import numpy as np
#from ibeis_cnn import utils


def get_verified_aid_pairs(ibs):
    """
    Example:
        >>> # DISABLE_DOCTEST
        >>> from ibeis_cnn.train import *  # NOQA
        >>> import ibeis
        >>> ibs = ibeis.opendb('NNP_Master3')
        >>> verified_aid1_list, verified_aid2_list = get_verified_aid_pairs(ibs)
    """
    # Grab marked hard cases
    am_rowids = ibs._get_all_annotmatch_rowids()
    remove_photobombs = True
    if remove_photobombs:
        flags = ibs.get_annotmatch_is_photobomb(am_rowids)
        am_rowids = ut.filterfalse_items(am_rowids, flags)
    verified_aid1_list = ibs.get_annotmatch_aid1(am_rowids)
    verified_aid2_list = ibs.get_annotmatch_aid2(am_rowids)
    return verified_aid1_list, verified_aid2_list


def get_hotspotter_aid_pairs(ibs):
    aid_list = ibs.get_valid_aids()
    import utool as ut
    aid_list = ut.list_compress(aid_list, ibs.get_annot_has_groundtruth(aid_list))
    qres_list = ibs.query_chips(aid_list, aid_list)
    num_top = 3
    aid1_list = np.array(ut.flatten([[qres.qaid] * num_top for qres in qres_list]))
    aid2_list = np.array(ut.flatten([qres.get_top_aids()[0:num_top] for qres in qres_list]))
    return aid1_list, aid2_list


def filter_aid_pairs(aid1_list, aid2_list):
    """
    TODO: move to results_organizer
    """
    np.vstack((aid1_list, aid2_list)).T
    import vtool as vt
    index_list = vt.find_best_undirected_edge_indexes(np.vstack((aid1_list, aid2_list)).T)
    aid1_list = ut.list_take(aid1_list, index_list)
    aid2_list = ut.list_take(aid2_list, index_list)
    return aid1_list, aid2_list


def get_identify_training_aid_pairs(ibs):
    r"""
    Args:
        ibs (IBEISController):  ibeis controller object

    Returns:
        tuple: (aid1_list, aid2_list)

    CommandLine:
        python -m ibeis_cnn.ibsplugin --test-get_identify_training_aid_pairs

    Example:
        >>> # DISABLE_DOCTEST
        >>> from ibeis_cnn.ibsplugin import *  # NOQA
        >>> import ibeis
        >>> ibs = ibeis.opendb('NNP_Master3')
        >>> (aid1_list, aid2_list) = get_identify_training_aid_pairs(ibs)
        >>> result = str((len(aid1_list), len(aid2_list)))
        >>> assert aid1_list != aid2_list
        >>> print(result)
    """
    verified_aid1_list, verified_aid2_list = get_verified_aid_pairs(ibs)
    if len(verified_aid1_list) > 100:
        aid1_list = verified_aid1_list
        aid2_list = verified_aid2_list
    else:
        aid1_list, aid2_list = get_hotspotter_aid_pairs(ibs)
    aid1_list, aid2_list = filter_aid_pairs(aid1_list, aid2_list)
    return aid1_list, aid2_list


def compute_target_size_from_aspect(chip_list, target_height=256):
    r"""
    Args:
        chip_list (list):
        target_height (int):

    Returns:
        ?: data

    CommandLine:
        python -m ibeis_cnn.ibsplugin --test-compute_target_size_from_aspect

    Example:
        >>> # DISABLE_DOCTEST
        >>> from ibeis_cnn.ibsplugin import *  # NOQA
        >>> import ibeis
        >>> # build test data
        >>> ibs = ibeis.opendb('testdb1')
        >>> (aid1_list, aid2_list) = get_identify_training_aid_pairs(ibs)
        >>> # execute function
        >>> chip1_list = ibs.get_annot_chips(aid1_list)
        >>> chip2_list = ibs.get_annot_chips(aid2_list)
        >>> chip_list = chip1_list + chip2_list
        >>> target_height = 256
        >>> target_size = compute_target_size_from_aspect(chip_list, target_height)
        >>> # verify results
        >>> result = str(target_size)
        >>> print(result)
        (381, 256)
    """
    import vtool as vt
    sizes1 = np.array([vt.get_size(chip1) for chip1 in chip_list])
    ar1_list = sizes1.T[0] / sizes1.T[1]
    ave_ar = ar1_list.mean()
    target_size = (int(np.round(ave_ar * target_height)), target_height)
    return target_size


def extract_chip_from_gpath_into_square_worker(args):
    import vtool as vt
    gfpath, bbox, theta, target_size = args
    imgBGR = vt.imread(gfpath)  # Read parent image
    return vt.extract_chip_into_square(imgBGR, bbox, theta, target_size)


def extract_square_chips_from_images(ibs, aid_list, target_size):
    """
    Simple function for computing a set of chips without going through the whole ibeis stuff

    Args:
        ibs (IBEISController):  ibeis controller object
        aid_list (int):  list of annotation ids

    CommandLine:
        python -m ibeis_cnn.ibsplugin --test-extract_square_chips_from_images --show

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis_cnn.ibsplugin import *  # NOQA
        >>> import ibeis
        >>> # build test data
        >>> ibs = ibeis.opendb('PZ_MTEST')
        >>> aid_list = ibs.get_valid_aids()[0:40]
        >>> target_size = (220, 220)
        >>> # execute function
        >>> chipBGR_square_list = extract_square_chips_from_images(ibs, aid_list, target_size)
        >>> ut.quit_if_noshow()
        >>> import plottool as pt
        >>> for chipBGR in ut.InteractiveIter(chipBGR_square_list, display_item=False):
        ...     pt.imshow(chipBGR)
        ...     pt.update()
        >>> # verify results
        >>> print(result)
    """
    gfpath_list = ibs.get_annot_image_paths(aid_list)
    bbox_list   = ibs.get_annot_bboxes(aid_list)
    theta_list  = ibs.get_annot_thetas(aid_list)
    target_size_list = [target_size] * len(aid_list)
    args_iter = zip(gfpath_list, bbox_list, theta_list, target_size_list)
    chipBGR_square_gen = ut.generate(extract_chip_from_gpath_into_square_worker, args_iter)
    chipBGR_square_list = list(chipBGR_square_gen)
    return chipBGR_square_list
    #gfpath = gfpath_list[0]
    #bbox = bbox_list[0]
    #theta = theta_list[0]
    #imgBGR = vt.imread(gfpath)
    #chipBGR_square = vt.extract_chip_into_square(imgBGR, bbox, theta, target_size)
    pass


def get_aidpair_identify_images(ibs, aid1_list, aid2_list, base_size=64, stacked=False):
    r"""
    Args:
        ibs (IBEISController):  ibeis controller object
        aid1_list (list):
        aid2_list (list):

    Returns:
        tuple: (data, labels)

    CommandLine:
        python -m ibeis_cnn.ibsplugin --test-get_aidpair_identify_images --show
        python -m ibeis_cnn.ibsplugin --test-get_aidpair_identify_images --show --db NNP_Master3
        python -m ibeis_cnn.ibsplugin --test-get_aidpair_identify_images

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis_cnn.ibsplugin import *  # NOQA
        >>> import ibeis
        >>> # build test data
        >>> ibs = ibeis.opendb(defaultdb='testdb1')
        >>> (aid1_list, aid2_list) = get_identify_training_aid_pairs(ibs)
        >>> aid1_list = aid1_list[0:min(100, len(aid1_list))]
        >>> aid2_list = aid2_list[0:min(100, len(aid2_list))]
        >>> # execute function
        >>> thumb1_list, thumb2_list = get_aidpair_identify_images(ibs, aid1_list, aid2_list)
        >>> ut.quit_if_noshow()
        >>> import plottool as pt
        >>> for aid1, aid2, thumb1, thumb2 in ut.InteractiveIter(zip(aid1_list, aid2_list, thumb1_list, thumb2_list), display_item=False):
        ...     print('aid1=%r, aid2=%r' % (aid1, aid2))
        ...     pt.imshow(thumb1, pnum=(1, 2, 1))
        ...     pt.imshow(thumb2, pnum=(1, 2, 2))
        ...     pt.update()
        >>> ut.show_if_requested()
    """
    # TODO: Cache this with visual uuids

    import vtool as vt
    print('[ibeget_aidpair_identify_images len(aid1_list)=%r' % (len(aid1_list)))
    print('base_size = %r' % (base_size,))
    assert len(aid1_list) == len(aid2_list)

    # TODO: Generalize these functions
    def inverable_unique_two_lists(item1_list, item2_list):
        """
        item1_list = aid1_list
        item2_list = aid2_list
        """
        import utool as ut
        unique_list1, inverse1 = np.unique(item1_list, return_inverse=True)
        unique_list2, inverse2 = np.unique(item2_list, return_inverse=True)
        flat_stacked, cumsum = ut.invertible_flatten2((unique_list1, unique_list2))
        flat_unique, inverse3 = np.unique(flat_stacked, return_inverse=True)
        reconstruct_tup = (inverse3, cumsum, inverse2, inverse1)
        return flat_unique, reconstruct_tup

    def uninvert_unique_two_lists(flat_list, reconstruct_tup):
        """
        flat_list = thumb_list
        """
        import utool as ut
        (inverse3, cumsum, inverse2, inverse1) = reconstruct_tup
        flat_stacked_ = ut.list_take(flat_list, inverse3)
        unique_list1_, unique_list2_ = ut.unflatten2(flat_stacked_, cumsum)
        res_list1_ = ut.list_take(unique_list1_, inverse1)
        res_list2_ = ut.list_take(unique_list2_, inverse2)
        return res_list1_, res_list2_

    # Flatten to only apply chip operations once
    flat_unique, reconstruct_tup = inverable_unique_two_lists(aid1_list, aid2_list)

    print('get_chips')
    chip_list = ibs.get_annot_chips(flat_unique)
    print('resize chips: base_size = %r' % (base_size,))
    target_height = base_size
    AUTO_SIZE = False
    if AUTO_SIZE:
        target_size = compute_target_size_from_aspect(chip_list, target_height)
    else:
        if stacked:
            target_size = (2 * base_size, base_size)
        else:
            target_size = (base_size, base_size)

    thumb_list = [vt.padded_resize(chip, target_size) for chip in ut.ProgressIter(chip_list)]

    thumb1_list, thumb2_list = uninvert_unique_two_lists(thumb_list, reconstruct_tup)

    return thumb1_list, thumb2_list


def get_aidpair_training_data(ibs, aid1_list, aid2_list, base_size=64, stacked=False, data_format='cv2'):
    thumb1_list, thumb2_list = get_aidpair_identify_images(ibs, aid1_list, aid2_list, base_size=base_size, stacked=stacked)
    assert data_format == 'cv2'
    # Stacking these might not be the exact correct thing to do.
    if stacked:
        img_list = [
            np.vstack((thumb1, thumb2)) for thumb1, thumb2, in
            zip(thumb1_list, thumb2_list)
        ]
    else:
        # Strided data comes in in pairs of two
        img_list = ut.flatten(list(zip(thumb1_list, thumb2_list)))
    data = np.array(img_list)
    #data = [img[None, :] for img in im
    #data = utils.convert_imagelist_to_data(img_list)
    return data


def view_training_data(ibs, **kwargs):
    """
    CommandLine:
        python -m ibeis_cnn.ibsplugin --test-view_training_data --db NNP_Master3

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis_cnn.ibsplugin import *  # NOQA
        >>> import ibeis
        >>> # build test data
        >>> ibs = ibeis.opendb(defaultdb='testdb1')
        >>> view_training_data(ibs)
    """
    data_fpath, labels_fpath, training_dpath = get_identify_training_fpaths(ibs, **kwargs)
    data = np.load(data_fpath, mmap_mode='r')
    #width = height = base_size * 2  # HACK FIXME
    #channels = 3
    #img_list = utils.convert_data_to_imglist(data, width, height, channels)
    import plottool as pt
    for img in ut.InteractiveIter(data, display_item=False):
        pt.imshow(img)
        pt.update()


def get_aidpair_training_labels(ibs, aid1_list, aid2_list):
    """
    Example:
        >>> # DISABLE_DOCTEST
        >>> from ibeis_cnn.ibsplugin import *  # NOQA
        >>> import ibeis
        >>> # build test data
        >>> ibs = ibeis.opendb(defaultdb='NNP_Master3')
        >>> (aid1_list, aid2_list) = get_identify_training_aid_pairs(ibs)
        >>> aid1_list = aid1_list[0:min(100, len(aid1_list))]
        >>> aid2_list = aid2_list[0:min(100, len(aid2_list))]
        >>> # execute function
        >>> img_list = get_aidpair_training_labels(ibs, aid1_list, aid2_list)
    """
    import vtool as vt
    truth_list = ibs.get_aidpair_truths(aid1_list, aid2_list)
    labels = truth_list
    # Mark different viewpoints as unknown for training
    yaw1_list = np.array(ut.replace_nones(ibs.get_annot_yaws(aid2_list), np.nan))
    yaw2_list = np.array(ut.replace_nones(ibs.get_annot_yaws(aid1_list), np.nan))
    yawdist_list = vt.ori_distance(yaw1_list, yaw2_list)
    TAU = np.pi * 2
    invalid_list = yawdist_list > TAU / 8
    from ibeis import const
    labels[invalid_list] = const.TRUTH_UNKNOWN
    return labels


def get_identify_training_dname(ibs, aid1_list, aid2_list):
    """
    Args:
        ibs (IBEISController):  ibeis controller object
        aid1_list (list):
        aid2_list (list):

    Returns:
        tuple: (data_fpath, labels_fpath)

    CommandLine:
        python -m ibeis_cnn.ibsplugin --test-get_identify_training_dname

    Example:
        >>> # DISABLE_DOCTEST
        >>> from ibeis_cnn.ibsplugin import *  # NOQA
        >>> import ibeis
        >>> # build test data
        >>> ibs = ibeis.opendb('testdb1')
        >>> aid1_list = ibs.get_valid_aids()
        >>> aid2_list = ibs.get_valid_aids()
        >>> training_dpath = get_identify_training_dname(ibs, aid1_list, aid2_list)
        >>> # verify results
        >>> result = str(training_dpath)
        >>> print(result)
        training((13)e%dn&kgqfibw7dbu)
    """
    semantic_uuids1 = ibs.get_annot_semantic_uuids(aid1_list)
    semantic_uuids2 = ibs.get_annot_semantic_uuids(aid2_list)
    aidpair_hashstr_list = map(ut.hashstr, zip(semantic_uuids1, semantic_uuids2))
    training_dname = ut.hashstr_arr(aidpair_hashstr_list, hashlen=16, lbl='training')
    return training_dname


def cached_identify_training_data_fpaths(ibs, aid1_list, aid2_list, base_size=64):
    """
    todo use size in cfgstrings
    """
    from os.path import join
    training_dname = get_identify_training_dname(ibs, aid1_list, aid2_list)
    nets_dir = ut.unixjoin(ibs.get_cachedir(), 'nets')
    training_dpath = join(nets_dir, training_dname)
    ut.ensuredir(nets_dir)
    ut.ensuredir(training_dpath)
    view_train_dir = ut.get_argflag('--vtd')
    if view_train_dir:
        ut.view_directory(training_dpath)

    class IdentifyDataConfig(object):
        def __init__(idcfg):
            idcfg.stacked = False
            idcfg.data_format = 'cv2'
            idcfg.base_size = 64

        def update(idcfg, **kwargs):
            idcfg.__dict__.update(**kwargs)

        def kw(idcfg):
            return ut.KwargsWrapper(idcfg)

        def get_cfgstr(idcfg):
            cfgstr_list = [
                'stacked' if idcfg.stacked else 'strided',
                idcfg.data_format,
                'sz=%d' % (idcfg.base_size,),
            ]
            return ','.join(cfgstr_list)

    idcfg = IdentifyDataConfig()
    idcfg.base_size = base_size

    data_fpath = join(training_dpath, 'data_' + idcfg.get_cfgstr())
    labels_fpath = join(training_dpath, 'labels.pkl')
    NOCACHE_TRAIN = ut.get_argflag('--nocache-train')

    if NOCACHE_TRAIN or not (
            ut.checkpath(data_fpath, verbose=True)
            and ut.checkpath(labels_fpath, verbose=True)
    ):
        data = get_aidpair_training_data(ibs, aid1_list, aid2_list, **idcfg.kw())
        labels = get_aidpair_training_labels(ibs, aid1_list, aid2_list)

        # Remove unknown labels
        from ibeis import const
        label_isinvalid = (labels != const.TRUTH_UNKNOWN)
        data_isinvalid = np.vstack((label_isinvalid, label_isinvalid)).T.flatten()
        data = data.compress(data_isinvalid, axis=0)
        labels = labels.compress(label_isinvalid, axis=0)

        print('np.shape(data) = %r' % (np.shape(data),))
        print('np.shape(labels) = %r' % (np.shape(labels),))

        # to resize the images back to their 2D-structure:
        # X = images_array.reshape(-1, 3, 48, 48)

        print('writing training data to %s...' % (data_fpath))
        with open(data_fpath, 'wb') as ofile:
            np.save(ofile, data)

        print('writing training labels to %s...' % (labels_fpath))
        with open(labels_fpath, 'wb') as ofile:
            np.save(ofile, labels)
    else:
        print('data and labels cache hit')
    return data_fpath, labels_fpath, training_dpath


def get_identify_training_fpaths(ibs, **kwargs):
    """

    Notes:
        Blog post:
        http://benanne.github.io/2015/03/17/plankton.html

        Code:
        https://github.com/benanne/kaggle-ndsb

        You need to do something like this to pass two images through the network:
        https://github.com/benanne/kaggle-ndsb/blob/master/dihedral.py#L89

        And then something like this to combine them again:
        https://github.com/benanne/kaggle-ndsb/blob/master/dihedral.py#L224

    CommandLine:
        python -m ibeis_cnn.ibsplugin --test-get_identify_training_fpaths

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis_cnn.ibsplugin import *  # NOQA
        >>> import ibeis
        >>> # build test data
        >>> ibs = ibeis.opendb('testdb1')
        >>> # execute function
        >>> (data_fpath, labels_fpath) = get_identify_training_fpaths(ibs)
        >>> # verify results
        >>> result = str((data_fpath, labels_fpath))
        >>> print(result)
    """
    print('get_identify_training_fpaths')
    aid1_list, aid2_list = get_identify_training_aid_pairs(ibs)
    max_examples = kwargs.pop('max_examples', None)
    if max_examples is not None:
        print('max_examples = %r' % (max_examples,))
        aid1_list = aid1_list[0:min(max_examples, len(aid1_list))]
        aid2_list = aid2_list[0:min(max_examples, len(aid2_list))]
    data_fpath, labels_fpath, training_dpath = cached_identify_training_data_fpaths(
        ibs, aid1_list, aid2_list, **kwargs)
    return data_fpath, labels_fpath, training_dpath


#def get_patchmetric_training_fpaths(ibs, **kwargs):
#    """
#    CommandLine:
#        python -m ibeis_cnn.ibsplugin --test-get_patchmetric_training_fpaths

#    Example:
#        >>> # ENABLE_DOCTEST
#        >>> from ibeis_cnn.ibsplugin import *  # NOQA
#        >>> import ibeis
#        >>> # build test data
#        >>> ibs = ibeis.opendb('testdb1')
#        >>> # execute function
#        >>> (data_fpath, labels_fpath) = get_patchmetric_training_fpaths(ibs)
#        >>> # verify results
#        >>> result = str((data_fpath, labels_fpath))
#        >>> print(result)
#    """
#    def get_aidpairs_and_matches():
#        aid_list = ibs.get_valid_aids()
#        import utool as ut
#        aid_list = ut.list_compress(aid_list, ibs.get_annot_has_groundtruth(aid_list))
#        qres_list = ibs.query_chips(aid_list, aid_list)
#        num_top = 3
#        aid1_list = np.array(ut.flatten([[qres.qaid] * num_top for qres in qres_list]))
#        aid2_list = np.array(ut.flatten([qres.get_top_aids()[0:num_top] for qres in qres_list]))
#        print('get_patchmetric_training_fpaths')
#        aid1_list, aid2_list = get_identify_training_aid_pairs(ibs)
#    max_examples = kwargs.pop('max_examples', None)
#    if max_examples is not None:
#        print('max_examples = %r' % (max_examples,))
#        aid1_list = aid1_list[0:min(max_examples, len(aid1_list))]
#        aid2_list = aid2_list[0:min(max_examples, len(aid2_list))]
#    data_fpath, labels_fpath, training_dpath = cached_identify_training_data_fpaths(
#        ibs, aid1_list, aid2_list, **kwargs)
#    return data_fpath, labels_fpath, training_dpath


if __name__ == '__main__':
    """
    CommandLine:
        python -m ibeis_cnn.ibsplugin
        python -m ibeis_cnn.ibsplugin --allexamples
        python -m ibeis_cnn.ibsplugin --allexamples --noface --nosrc
    """
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    import utool as ut  # NOQA
    ut.doctest_funcs()
