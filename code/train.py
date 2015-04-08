#!/usr/bin/env python

# train.py
# constructs the Theano optimization and trains a learning model,
# optionally by initializing the network with pre-trained weights.

# our own imports
import utils
import model

# module imports
import time
import theano
import itertools
import numpy as np
import cPickle as pickle

from lasagne import layers

from os.path import join, abspath
import random


def augmentation(Xb, yb):
    # label_map = {
    #     0:  4,
    #     1:  5,
    #     2:  6,
    #     3:  7,
    #     8:  12,
    #     9:  13,
    #     10: 14,
    #     11: 15,
    # }
    label_map = { x: x + 4 for x in range(0, 4) + range(8, 12) }
    # Apply inverse
    for key in label_map.keys():
        label = label_map[key]
        label_map[label] = key
    # Map
    points, channels, height, width = Xb.shape
    for index in range(points):
        if random.uniform(0.0, 1.0) <= 0.5:
            Xb[index] = Xb[index, :, ::-1]
            yb[index] = label_map[yb[index]]
    return Xb, yb


def learning_rate_update(x):
    return 0.1 * x


def train(data_file, labels_file, trained_weights_file=None,
          pretrained_weights_file=None):
    current_time = utils.get_current_time()
    if trained_weights_file is None:
        trained_weights_file = '%s.pickle' % (current_time)

    learning_rate = theano.shared(utils.float32(0.03))
    patience   = 10
    max_epochs = 150
    momentum   = 0.9
    batch_size = 128
    whiten     = True
    normalizer = 255.0
    output_dim = 16    # the number of outputs from the softmax layer (# classes)

    print('loading data...')
    data, labels = utils.load(data_file, labels_file)
    # print('adding channels...')
    # data = utils.add_channels(data)
    print('  X.shape = %r' % (data.shape,))
    print('  X.dtype = %r' % (data.dtype,))
    print('  y.shape = %r' % (labels.shape,))
    print('  y.dtype = %r' % (labels.dtype,))

    # utils.show_image_from_data(data)

    print('building model...')
    input_cases, input_channels, input_height, input_width = data.shape
    output_layer = model.build_model(batch_size, input_width, input_height,
                                     input_channels, output_dim)
    utils.print_layer_info(layers.get_all_layers(output_layer)[::-1])
    print('this model has %d learnable parameters' % (layers.count_params(output_layer)))

    if pretrained_weights_file is not None:
        print('loading pretrained weights from %s' % (pretrained_weights_file))
        with open(pretrained_weights_file, 'rb') as pfile:
            pretrained_weights = pickle.load(pfile)
            layers.set_all_param_values(output_layer, pretrained_weights)

    all_iters = utils.create_iter_funcs(learning_rate, momentum, output_layer)
    train_iter, valid_iter, predict_iter = all_iters

    print('creating train, validation datasaets...')
    dataset = utils.train_test_split(data, labels, eval_size=0.2)
    X_train, y_train, X_valid, y_valid = dataset

    print('calculating whitening...')
    if whiten:
        whiten_mean = np.mean(X_train, axis=0)
        # whiten_std  = np.std(X_train, axis=0)
        whiten_std  = 1.0
    else:
        whiten_mean = None  # 0.0
        whiten_std  = None  # 1.0

    best_weights = None
    best_train_loss, best_valid_loss, best_valid_accuracy = np.inf, np.inf, 0.0
    print('starting training at %s...' % (current_time))
    utils.print_header_columns()

    best_weights, best_epoch, best_train_loss, best_valid_loss = None, 0, np.inf, np.inf
    try:
        for epoch in itertools.count(1):
            train_losses, valid_losses, valid_accuracies = [], [], []

            t0 = time.time()
            # compute the loss over all training batches
            for Xb, yb in utils.batch_iterator(X_train, y_train, batch_size,
                                               normalizer, whiten_mean, whiten_std,
                                               rand=True, augment=augmentation):
                batch_train_loss = train_iter(Xb, yb)
                train_losses.append(batch_train_loss)

            # compute the loss over all validation batches
            for Xb, yb in utils.batch_iterator(X_valid, y_valid, batch_size,
                                               normalizer, whiten_mean, whiten_std):
                batch_valid_loss, batch_accuracy = valid_iter(Xb, yb)
                valid_losses.append(batch_valid_loss)
                valid_accuracies.append(batch_accuracy)

            # estimate the loss over all batches
            avg_train_loss = np.mean(train_losses)
            avg_valid_loss = np.mean(valid_losses)
            avg_valid_accuracy = np.mean(valid_accuracies)

            if np.isnan(avg_train_loss):
                print('training diverged')
                break

            if avg_train_loss < best_train_loss:
                best_train_loss = avg_train_loss
            if avg_valid_loss < best_valid_loss:
                best_epoch = epoch
                best_valid_loss = avg_valid_loss
                best_weights = layers.get_all_param_values(output_layer)
            if avg_valid_accuracy > best_valid_accuracy:
                best_valid_accuracy = avg_valid_accuracy

            utils.print_epoch_info(avg_valid_loss, best_valid_loss, avg_valid_accuracy,
                                   best_valid_accuracy, avg_train_loss, best_train_loss,
                                   epoch, time.time() - t0)

            if epoch >= best_epoch + patience:
                best_epoch = epoch
                new_learning_rate = learning_rate_update(learning_rate.get_value())
                learning_rate.set_value(utils.float32(new_learning_rate))
                print('\nsetting learning rate to %.6f\n' % (new_learning_rate))

            if epoch > max_epochs:
                print('\nmaximum number of epochs exceeded')
                print('saving best weights to %s' % (weights_file))
                with open(weights_file, 'wb') as pfile:
                    pickle.dump(best_weights, pfile, protocol=pickle.HIGHEST_PROTOCOL)
                break
    except KeyboardInterrupt:
        print('saving best weights to %s' % (weights_file))
        with open(weights_file, 'wb') as pfile:
            pickle.dump(best_weights, pfile, protocol=pickle.HIGHEST_PROTOCOL)


if __name__ == '__main__':
    project_name = 'viewpoint'
    root = abspath(join('..', 'data'))
    train_data_file = join(root, 'numpy', project_name, 'X.npy')
    train_labels_file = join(root, 'numpy', project_name, 'y.npy')
    weights_file = join(root, 'nets', 'ibeis_cnn_weights.pickle')
    pretrained_weights_file = join(root, 'nets', 'pretrained_weights.pickle')
    train(train_data_file, train_labels_file, weights_file)
    #train(train_data_file, train_labels_file, weights_file, pretrained_weights_file)
