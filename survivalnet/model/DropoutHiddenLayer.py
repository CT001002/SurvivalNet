__docformat__ = 'restructedtext en'

import theano
import theano.tensor as T
from .HiddenLayer import HiddenLayer
from theano.ifelse import ifelse
import numpy as np

class DropoutHiddenLayer(HiddenLayer):
    def __init__(self, rng, input, n_in, n_out, is_train,
                 activation, dropout_rate, mask=None, W=None, b=None):
        super(DropoutHiddenLayer, self).__init__(
                rng=rng, input=input, n_in=n_in, n_out=n_out, W=W, b=b,
                activation=activation)

        # Set variables
        self.dropout_rate = dropout_rate
        self.srng = T.shared_randomstreams.RandomStreams(rng.randint(999999))
        self.mask = mask

        # Compute outputs for train and test phase applying dropout when necessary
        train_output = layer * T.cast(self.mask, theano.config.floatX)
        test_output = self.output * (1 - dropout_rate)
        self.output = ifelse(T.eq(is_train, 1), train_output, test_output)
        return