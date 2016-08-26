# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from ibeis_cnn.models import abstract_models
import utool as ut
print, rrr, profile = ut.inject2(__name__, '[ibeis_cnn.models.dummy]')


class MNISTModel(abstract_models.AbstractCategoricalModel):
    """
    Toy model for testing and playing with mnist

    CommandLine:
        python -m ibeis_cnn.models.mnist MNISTModel:0
        python -m ibeis_cnn.models.mnist MNISTModel:1

        python -m ibeis_cnn _ModelFitting.fit:0 --vd --monitor
        python -m ibeis_cnn _ModelFitting.fit:1 --vd

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis_cnn.models.mnist import *  # NOQA
        >>> from ibeis_cnn import ingest_data
        >>> dataset = ingest_data.grab_mnist_category_dataset_float()
        >>> model = MNISTModel(batch_size=128, data_shape=dataset.data_shape,
        >>>                    output_dims=dataset.output_dims,
        >>>                    training_dpath=dataset.training_dpath)
        >>> output_layer = model.init_arch()
        >>> model.print_model_info_str()
        >>> model.mode = 'FAST_COMPILE'
        >>> model.build_backprop_func()

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis_cnn.models.mnist import *  # NOQA
        >>> from ibeis_cnn.models import mnist
        >>> model, dataset = mnist.testdata_mnist(name='bnorm')
        >>> model.init_arch()
        >>> model.print_layer_info()
        >>> model.print_model_info_str()
        >>> #model.reinit_weights()
        >>> X_train, y_train = dataset.subset('train')
        >>> model.fit(X_train, y_train)
        >>> output_layer = model.init_arch()
        >>> model.print_layer_info()
        >>> # parse training arguments
        >>> model.monitor_config.update(**ut.argparse_dict(dict(
        >>>     era_size=100,
        >>>     max_epochs=5,
        >>>     rate_decay=.8,
        >>> )))
        >>> X_train, y_train = dataset.subset('train')
        >>> model.fit(X_train, y_train)

    """
    def __init__(model, **kwargs):
        model.batch_norm = kwargs.pop('batch_norm', True)
        model.dropout = kwargs.pop('dropout', .5)
        super(MNISTModel, model).__init__(**kwargs)

    def augment(model, Xb, yb=None):
        """
        X_valid, y_valid = dataset.subset('valid')
        num = 10
        Xb = X_valid[:num]
        Xb = Xb / 255.0 if ut.is_int(Xb) else Xb
        Xb = Xb.astype(np.float32, copy=True)
        yb = None if yb is None else yb.astype(np.int32, copy=True)
        # Rescale the batch data to the range 0 to 1
        Xb_, yb_ = model.augment(Xb)
        yb_ = None
        >>> ut.quit_if_noshow()
        >>> import plottool as pt
        >>> pt.qt4ensure()
        >>> from ibeis_cnn import augment
        >>> augment.show_augmented_patches(Xb, Xb_, yb, yb_, data_per_label=1)
        >>> ut.show_if_requested()
        """
        from ibeis_cnn import augment
        rng = model._rng
        affperterb_ranges = dict(
            zoom_range=(1.3, 1.2),
            max_tx=2,
            max_ty=2,
            max_shear=ut.TAU / 32,
            max_theta=ut.TAU,
            enable_stretch=True,
            enable_flip=True,
        )
        Xb_, yb_ = augment.augment_affine(
            Xb, yb, rng=rng, inplace=True, data_per_label=1,
            affperterb_ranges=affperterb_ranges,
            aug_prop=.5,
        )
        return Xb_, yb_

    def init_arch(model):
        """

        CommandLine:
            python -m ibeis_cnn  MNISTModel.init_arch --verbcnn
            python -m ibeis_cnn  MNISTModel.init_arch --verbcnn --show

            python -m ibeis_cnn  MNISTModel.init_arch --verbcnn --name=bnorm --show
            python -m ibeis_cnn  MNISTModel.init_arch --verbcnn --name=incep --show

        Example:
            >>> # ENABLE_DOCTEST
            >>> from ibeis_cnn.models.mnist import *  # NOQA
            >>> verbose = True
            >>> name = ut.get_argval('--name', default='bnorm')
            >>> model = MNISTModel(batch_size=128, data_shape=(28, 28, 1),
            >>>                    output_dims=10, name=name)
            >>> model.init_arch()
            >>> model.print_model_info_str()
            >>> print(model)
            >>> ut.quit_if_noshow()
            >>> model.show_arch()
            >>> ut.show_if_requested()
        """
        print('[model] init_arch')
        if True:
            print('[model] Initialize MNIST model architecture')
            print('[model]   * batch_size     = %r' % (model.batch_size,))
            print('[model]   * input_width    = %r' % (model.input_width,))
            print('[model]   * input_height   = %r' % (model.input_height,))
            print('[model]   * input_channels = %r' % (model.input_channels,))
            print('[model]   * output_dims    = %r' % (model.output_dims,))
        if model.name.startswith('incep'):
            network_layers_def = model.get_inception_def()
        else:
            network_layers_def = model.get_mnist_model_def1()
        network_layers = abstract_models.evaluate_layer_list(network_layers_def)
        model.output_layer = network_layers[-1]
        return model.output_layer

    def get_mnist_model_def1(model):
        """
        Follows https://github.com/Lasagne/Lasagne/blob/master/examples/mnist.py
        """
        import ibeis_cnn.__LASAGNE__ as lasange
        from ibeis_cnn import custom_layers
        batch_norm = model.batch_norm
        dropout = model.dropout

        bundles = custom_layers.make_bundles(
            nonlinearity=lasange.nonlinearities.rectify,
            batch_norm=batch_norm,
        )
        b = ut.DynStruct(copy_dict=bundles)

        N = 128

        network_layers_def = [
            b.InputBundle(shape=model.input_shape, noise=False),
            b.ConvBundle(num_filters=N, filter_size=(3, 3), pool=False),
            b.ConvBundle(num_filters=N, filter_size=(3, 3), pool=False),
            b.ConvBundle(num_filters=N, filter_size=(3, 3), pool=True),
            b.ConvBundle(num_filters=N, filter_size=(3, 3), pool=False),
            b.ConvBundle(num_filters=N, filter_size=(3, 3), pool=True),
            b.ConvBundle(num_filters=N, filter_size=(3, 3), pool=False),
            # A fully-connected layer of 256 units and 50% dropout of its inputs
            b.DenseBundle(num_units=N * 4, dropout=dropout),
            # A fully-connected layer of 256 units and 50% dropout of its inputs
            b.DenseBundle(num_units=N * 4, dropout=dropout),
            # And, finally, the 10-unit output layer with 50% dropout on its inputs
            b.SoftmaxBundle(num_units=model.output_dims, dropout=dropout),
        ]
        return network_layers_def

    def get_inception_def(model):
        import ibeis_cnn.__LASAGNE__ as lasange
        from ibeis_cnn import custom_layers
        batch_norm = model.batch_norm
        if model.dropout is None:
            dropout = 0 if batch_norm else .5
        else:
            dropout = model.dropout

        bundles = custom_layers.make_bundles(
            nonlinearity=lasange.nonlinearities.rectify,
            batch_norm=batch_norm,
        )
        b = ut.DynStruct(copy_dict=bundles)

        N = 64

        network_layers_def = [
            b.InputBundle(shape=model.input_shape, noise=False),
            b.ConvBundle(num_filters=N, filter_size=(3, 3), pool=False),
            b.ConvBundle(num_filters=N, filter_size=(3, 3), pool=True),
            b.InceptionBundle(
                branches=[dict(t='c', s=(1, 1), r=00, n=N),
                          dict(t='c', s=(3, 3), r=N // 2, n=N),
                          dict(t='c', s=(3, 3), r=N // 4, n=N // 2, d=2),
                          dict(t='p', s=(3, 3), n=N // 2)],
            ),
            b.InceptionBundle(
                branches=[dict(t='c', s=(1, 1), r=00, n=N),
                          dict(t='c', s=(3, 3), r=N // 2, n=N),
                          dict(t='c', s=(3, 3), r=N // 4, n=N // 2, d=2),
                          dict(t='p', s=(3, 3), n=N // 2)],
                dropout=dropout,
                pool=True
            ),
            # ---
            b.DenseBundle(num_units=N, dropout=dropout),
            b.DenseBundle(num_units=N, dropout=dropout),
            # And, finally, the 10-unit output layer with 50% dropout on its inputs
            b.SoftmaxBundle(num_units=model.output_dims, dropout=dropout),
            #b.GlobalPool
            #b.NonlinearitySoftmax(),
        ]
        return network_layers_def


def testdata_mnist(name='bnorm', batch_size=128, dropout=None):
    from ibeis_cnn import ingest_data
    from ibeis_cnn.models import mnist
    dataset = ingest_data.grab_mnist_category_dataset()
    if name == 'bnorm':
        batch_norm = True
        dropout = dropout
    elif name == 'dropout':
        batch_norm = False
        dropout = .5
    else:
        batch_norm = True
        dropout = dropout
    output_dims = len(dataset.unique_labels)
    model = mnist.MNISTModel(
        batch_size=batch_size,
        data_shape=dataset.data_shape,
        name=name,
        output_dims=output_dims,
        batch_norm=batch_norm,
        dropout=dropout,
        dataset_dpath=dataset.dataset_dpath
    )
    model.monitor_config['monitor'] = True
    model.monitor_config['showprog'] = False
    model.monitor_config['slowdump_freq'] = 10

    model.learn_state['learning_rate'] = .1
    model.hyperparams['weight_decay'] = .001
    if name == 'bnorm':
        model.hyperparams['era_size'] = 4
        model.hyperparams['rate_schedule'] = [.9]
    else:
        model.hyperparams['era_size'] = 20
        model.hyperparams['rate_schedule'] = [.9]
    return model, dataset


if __name__ == '__main__':
    """
    CommandLine:
        python -m ibeis_cnn.models.mnist
        python -m ibeis_cnn.models.mnist --allexamples
        python -m ibeis_cnn.models.mnist --allexamples --noface --nosrc
    """
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    import utool as ut  # NOQA
    ut.doctest_funcs()
