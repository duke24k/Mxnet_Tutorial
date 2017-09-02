# -*- coding: utf-8 -*-
import mxnet as mx
import numpy as np
import data_download as dd
import logging
logging.basicConfig(level=logging.INFO)
import matplotlib.pyplot as plt
import os

'''unsupervised learning -  Autoencoder'''

def to2d(img):
    return img.reshape(img.shape[0],784).astype(np.float32)/255.0

def NeuralNet(epoch,batch_size,save_period,load_weights):
    '''
    load_data

    1. SoftmaxOutput must be

    train_iter = mx.io.NDArrayIter(data={'data' : to4d(train_img)},label={'label' : train_lbl}, batch_size=batch_size, shuffle=True) #training data
    test_iter   = mx.io.NDArrayIter(data={'data' : to4d(test_img)}, label={'label' : test_lbl}, batch_size=batch_size) #test data

    2. LogisticRegressionOutput , LinearRegressionOutput , MakeLoss and so on.. must be

    train_iter = mx.io.NDArrayIter(data={'data' : to4d(train_img)},label={'label' : train_lbl_one_hot}, batch_size=batch_size, shuffle=True) #training data
    test_iter   = mx.io.NDArrayIter(data={'data' : to4d(test_img)}, label={'label' : test_lbl_one_hot}, batch_size=batch_size) #test data
    '''

    '''In this Autoencoder tutorial, we don't need the label data.'''
    (_, _, train_img) = dd.read_data_from_file('train-labels-idx1-ubyte.gz','train-images-idx3-ubyte.gz')
    (_, _, test_img) = dd.read_data_from_file('t10k-labels-idx1-ubyte.gz', 't10k-images-idx3-ubyte.gz')

    '''data loading referenced by Data Loading API '''
    train_iter  = mx.io.NDArrayIter(data={'input' : to2d(train_img)},label={'input_' : to2d(train_img)}, batch_size=batch_size, shuffle=True) #training data
    test_iter   = mx.io.NDArrayIter(data={'input' : to2d(test_img)},label={'input_' : to2d(test_img)}) #test data

    '''Autoencoder network

    <structure>
    input - encode - middle - decode -> output
    '''
    input = mx.sym.Variable('input')
    output= mx.sym.Variable('input_')

    # encode
    affine1 = mx.sym.FullyConnected(data=input,name='encode1',num_hidden=100)
    encode1 = mx.sym.Activation(data=affine1, name='sigmoid1', act_type="sigmoid")

    # encode
    affine2 = mx.sym.FullyConnected(data=encode1, name='encode2', num_hidden=50)
    encode2 = mx.sym.Activation(data=affine2, name='sigmoid2', act_type="sigmoid")

    # decode
    affine3 = mx.sym.FullyConnected(data=encode2, name='decode1', num_hidden=50)
    decode1 = mx.sym.Activation(data=affine3, name='sigmoid3', act_type="sigmoid")

    # decode
    affine4 = mx.sym.FullyConnected(data=decode1,name='decode2',num_hidden=100)
    decode2 = mx.sym.Activation(data=affine4, name='sigmoid4', act_type="sigmoid")

    # output
    result = mx.sym.FullyConnected(data=decode2, name='result', num_hidden=784)
    result = mx.sym.Activation(data=result, name='sigmoid5', act_type="sigmoid")

    #LogisticRegressionOutput contains a sigmoid function internally. and It should be executed with xxxx_lbl_one_hot data.
    result=mx.sym.LinearRegressionOutput(data=result ,label=output)

    # We visualize the network structure with output size (the batch_size is ignored.)
    shape = {"input": (batch_size,784)}
    graph=mx.viz.plot_network(symbol=result,shape=shape)#The diagram can be found on the Jupiter notebook.
    if epoch==1:
        graph.view()
    print(result.list_arguments())

    # Fisrt optimization method
    # weights save
    if not os.path.exists("weights"):
        os.makedirs("weights")

    model_name = 'weights/Autoencoder'
    checkpoint = mx.callback.do_checkpoint(model_name, period=save_period)

    #training mod
    mod = mx.mod.Module(symbol=result, data_names=['input'],label_names=['input_'], context=mx.gpu(0))

    #test mod
    test = mx.mod.Module(symbol=result, data_names=['input'],label_names=['input_'], context=mx.gpu(0))

    # Network information print
    print(mod.data_names)
    print(mod.label_names)
    print(train_iter.provide_data)
    print(train_iter.provide_label)

    '''if the below code already is declared by mod.fit function, thus we don't have to write it.
    but, when you load the saved weights, you must write the below code.'''
    mod.bind(data_shapes=train_iter.provide_data,label_shapes=train_iter.provide_label)

    #weights load
    # When you want to load the saved weights, uncomment the code below.
    weights_path= model_name+"-0{}.params".format(load_weights)
    if os.path.exists(weights_path):
        print("Load weights")
        symbol, arg_params, aux_params = mx.model.load_checkpoint(model_name, load_weights)
        #the below code needs mod.bind, but If arg_params and aux_params is set in mod.fit, you do not need the code below, nor do you need mod.bind.
        mod.set_params(arg_params, aux_params)

    '''if you want to modify the learning process, go into the mod.fit function()'''

    mod.fit(train_iter, initializer=mx.initializer.Xavier(rnd_type='gaussian', factor_type="avg", magnitude=1),
            optimizer='adam', #optimizer
            optimizer_params={'learning_rate': 0.001 }, #learning rate
            eval_metric=mx.metric.MSE(),
            # Once the loaded parameters are declared here,You do not need to declare mod.set_params,mod.bind
            arg_params=None,
            aux_params=None,
            num_epoch=epoch,
            epoch_end_callback=checkpoint)

    # Network information print
    #print(mod.data_shapes)
    #print(mod.label_shapes)
    #print(mod.output_shapes)
    #print(mod.get_params())
    #print(mod.get_outputs())

    print("training_data : {}".format(mod.score(train_iter, ['mse'])))

    print("Optimization complete.")

    #################################TEST####################################
    '''load method1 - load the saved parameter'''
    #symbol, arg_params, aux_params = mx.model.load_checkpoint(model_name, 100)

    '''load method2 - load the training mod.get_params() directly'''
    #arg_params, aux_params = mod.get_params()

    '''load method3 - using the shared_module'''
    """
    Parameters
    shared_module : Module
        Default is `None`. This is used in bucketing. When not `None`, the shared module
        essentially corresponds to a different bucket -- a module with different symbol
        but with the same sets of parameters (e.g. unrolled RNNs with different lengths).
    """
    test.bind(data_shapes=test_iter.provide_data, label_shapes=test_iter.provide_label,shared_module=mod,for_training=False)

    '''Annotate only when running test data. and Uncomment only if it is 'load method1' or 'load method2' '''
    #test.set_params(arg_params, aux_params)

    '''test'''
    column_size=10 ; row_size=10 #     column_size x row_size <= 10000

    result = test.predict(test_iter,num_batch=column_size*row_size).asnumpy()
    '''range adjustment 0 ~ 1 -> 0 ~ 255 '''
    result = result*255.0

    '''generator image visualization'''
    fig_g ,  ax_g = plt.subplots(row_size, column_size, figsize=(column_size, row_size))
    fig_g.suptitle('generator')
    for j in range(row_size):
        for i in range(column_size):
            ax_g[j][i].set_axis_off()
            ax_g[j][i].imshow(np.reshape(result[i+j*column_size],(28,28)),cmap='gray')

    fig_g.savefig("generator.png")
    '''real image visualization'''
    fig_r ,  ax_r = plt.subplots(row_size, column_size, figsize=(column_size, row_size))
    fig_r.suptitle('real')
    for j in range(row_size):
        for i in range(column_size):
            ax_r[j][i].set_axis_off()
            ax_r[j][i].imshow(test_img[i+j*column_size], cmap='gray')
    fig_r.savefig("real.png")

    plt.show()

if __name__ == "__main__":
    print("NeuralNet_starting in main")
    NeuralNet(epoch=100,batch_size=100,save_period=100,load_weights=100)
else:
    print("NeuralNet_imported")
