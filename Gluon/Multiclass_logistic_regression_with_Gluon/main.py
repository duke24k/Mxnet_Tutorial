import model
import mxnet as mx
#implementation

#dataset = MNIST or FashionMNIST or CIFAR10
result=model.muitlclass_logistic_regression(epoch=0, batch_size=256 , save_period=50 , load_period=100 , optimizer="adam", learning_rate=0.001, dataset="FashionMNIST", ctx=mx.gpu(0))
print("///"+result+"///")