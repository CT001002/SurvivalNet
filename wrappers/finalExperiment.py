"""
Created on Tue Oct 20 12:53:54 2015
@author: syouse3
"""


import sys
import os
sys.path.insert(0, '../')
from train import test_SdA
import bayesopt_wrapper
import numpy as np
import scipy.io as sio
from nonLinearities import ReLU, LeakyReLU, Sigmoid
import cPickle

def calc_at_risk(X, T, O):
    tmp = list(T)
    T = np.asarray(tmp).astype('float64')
    order = np.argsort(T)
    sorted_T = T[order]
    at_risk = np.asarray([list(sorted_T).index(x)+1 for x in sorted_T]).astype('int32')
    T = np.asarray(sorted_T)
    O = O[order]
    X = X[order]
    return X, T, O, at_risk - 1
    
def wrapper(maxShuffIter, path2data, path2output, validation = True):
    for i in range(maxShuffIter):
        p = path2data + 'shuffle' + str(i) + '.mat'    
        print '*** shuffle #%d *** \n' % i                       
        mat = sio.loadmat(p)
        X = mat['X']
        X = X.astype('float64')       
        O = mat['C']
        T = mat['T']
        T = np.asarray([t[0] for t in T.transpose()])
        O = 1 - np.asarray([o[0] for o in O.transpose()])
        fold_size = int(15 * len(X) / 100)       
        
        X_test = X[:fold_size]
        T_test = T[:fold_size]
        O_test = O[:fold_size]
        
        X_train = X[fold_size * 2:]       
        T_train = T[fold_size * 2:]
        O_train = O[fold_size * 2:]
        
        if validation == True:
            maxval, params, err = bayesopt_wrapper.bayesopt_tuning(i)
            cost_func(O_train, X_train, T_train, O_test, X_test, T_test, i, resultPath = path2output, params = params)
            
        else: cost_func(O_train, X_train, T_train, O_test, X_test, T_test, i, resultPath = path2output, params = None)
    
    return

def cost_func(O_train, X_train, T_train, O_test, X_test, T_test, shuffle_id, resultPath, params = None):
        
    print '*** Model assesment using selected params ***'    
    if not os.path.exists(resultPath):
        os.makedirs(resultPath)
    if params == None:
        ## PARSET
        n_layer = 0
        hSize = 250
        do_rate = 0
        ftlr = .1
        ptlr = 0.01
    else:
        n_layer = params[0]
        hSize = params[1]
        ptlr = params[2] 
        ftlr = params[3]
        do_rate = params[4]
    ## PARSET    
    ptepochs=100
    tepochs=100
    bs = 1
    dropout = True
    pretrain = True
    
    x_train, t_train, o_train, at_risk_train = calc_at_risk(X_train, T_train, O_train);
    x_test, t_test, o_test, at_risk_test = calc_at_risk(X_test, T_test, O_test);
    
   
    cost_list, tst_cost_list, c = test_SdA(train_observed = o_train, train_X = x_train, train_y = t_train, at_risk_train = at_risk_train, \
     at_risk_test=at_risk_test, test_observed = o_test, test_X = x_test, test_y = t_test,\
     finetune_lr=ftlr, pretrain=pretrain, pretraining_epochs = ptepochs, n_layers=n_layer, n_hidden = hSize,\
     pretrain_lr=ptlr, training_epochs = tepochs , batch_size=bs, drop_out = dropout, dropout_rate= do_rate, \
     non_lin=Sigmoid, alpha=5.5)
    
    expID = 'pt' + str(pretrain) + 'ftlr' + str(ftlr) + '-' + 'pt' + str(ptepochs) + '-' + \
    'nl' + str(n_layer) + '-' + 'hs' + str(hSize) + '-' + \
    'ptlr' + str(ptlr) + '-' + 'ft' + str(tepochs) + '-' + 'bs' + str(bs) + '-' +  \
    'dor'+ str(do_rate) + '-' + 'do'+ str(dropout) + '-id' + str(shuffle_id)       

    print expID
     
    ## write output to file
    outputFileName = os.path.join(resultPath, expID  + 'ci')
    f = file(outputFileName, 'wb')
    cPickle.dump(c, f, protocol=cPickle.HIGHEST_PROTOCOL)
    f.close()
    
    outputFileName = os.path.join(resultPath , expID  + 'lpl')
    f = file(outputFileName, 'wb')
    cPickle.dump(cost_list, f, protocol=cPickle.HIGHEST_PROTOCOL)
    f.close()

    outputFileName = os.path.join(resultPath, expID  + 'lpl_tst')
    f = file(outputFileName, 'wb')
    cPickle.dump(tst_cost_list, f, protocol=cPickle.HIGHEST_PROTOCOL)
    f.close()


    return 
if __name__ == '__main__':
        ## PARSET
    pout = '/Users/Ayine/pySurv/Brain_P_results/sigmoid/Dec/'
    pin = '../data/Brain_P/'
    wrapper(maxShuffIter = 10, path2data = pin, path2output = pout)



                        