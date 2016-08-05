import sys
sys.path.append('./..')
import os
import scipy.io as sio
from time import clock
from optimization import SurvivalAnalysis
from optimization import Bayesian_Optimization
import cPickle
import numpy as np
from .train import train
import theano
import shutil

def pickSubType(subtypesVec, subtype):
  inds = [i for i in range(len(subtypesVec)) if (subtypesVec[i] == subtype)]
  return inds
def Run():      
#where c-index and cost function values are saved 
  resultPath = os.path.join(os.getcwd(), '../results/Final/LUSC_Integ/')
  if os.path.exists(resultPath):
      shutil.rmtree(resultPath)
      os.makedirs(resultPath)
  else:
      os.makedirs(resultPath)
  #where the data (possibly multiple cross validation sets) are stored
  #we use 10 permutations of the data and consequently 10 different training 
  #and testing splits to produce the results in the paper
  p = os.path.join(os.getcwd(), '../data/LUSC_Integ.mat')
  D = sio.loadmat(p)
  T = np.asarray([t[0] for t in D['Survival']])
  O = 1 - np.asarray([c[0] for c in D['Censored']])
  X = D['Integ_X']
  # Use Bayesian Optimization for model selection, 
  #if false ,manually set parameters will be used
  BayesOpt = True
  opt = 'GDLS'    
  #pretrain_config = {'pt_lr':0.01, 'pt_epochs':1000, 'pt_batchsize':None,'corruption_level':.3}
  pretrain_config = None         #No pre-training 
  numberOfShuffles = 20
  ft = np.multiply(np.ones((numberOfShuffles, 1)), 40)
  shuffleResults =[]
  avg_cost = 0
  i = 0 
  while i < numberOfShuffles: 
    if BayesOpt == True:
      print '***Model Selection with BayesOpt for shuffle', str(i), '***'
      maxval, bo_params, err = Bayesian_Optimization.tune(i)
      n_layers = bo_params[0]
      n_hidden = bo_params[1]
      do_rate = bo_params[2]
      nonlin = theano.tensor.nnet.relu if bo_params[3]>.5 else np.tanh
    else:
      n_layers = 1
      n_hidden = 67
      do_rate = .35
      #nonlin = theano.tensor.nnet.relu
      nonlin = np.tanh 

    expID = 'nl' + str(n_layers) + '-' + 'hs' + str(n_hidden) + '-' + \
            'dor'+ str(do_rate) + '-id' + str(i)       
    #file names: shuffle0.mat, etc.
    prng = np.random.RandomState(i)
    order = prng.permutation(np.arange(len(X)))
    X = X[order]
    #C is censoring status. 0 means alive patient. We change it to O 
    #for comatibility with lifelines package        
    O = O[order]
    T = T[order]

    #Use the entire dataset for pretraining
    pretrain_set = X

    #foldsize denotes th amount of data used for testing. The same amount 
    #of data is used for model selection. The rest is used for training.
    fold_size = int(20 * len(X) / 100)

    train_set = {}
    test_set = {}

    #caclulate the risk group for every patient i: patients who die after i
    sa = SurvivalAnalysis()    
    finetune_config = {'ft_lr':0.01, 'ft_epochs':ft[i]}
    train_set['X'], train_set['T'], train_set['O'], train_set['A'] = sa.calc_at_risk(X[fold_size:], T[fold_size:], O[fold_size:]);
    #train_set['X'], train_set['T'], train_set['O'], train_set['A'] = sa.calc_at_risk(X, T, O);
    test_set['X'], test_set['T'], test_set['O'], test_set['A'] = sa.calc_at_risk(X[:fold_size], T[:fold_size], O[:fold_size]);
    print '***Model Assesment***'
    train_cost_list, cindex_train, test_cost_list, cindex_test, model, _ = train(pretrain_set, train_set, test_set,
    pretrain_config, finetune_config, n_layers, n_hidden, coxphfit=False,
    dropout_rate=do_rate, non_lin = nonlin, optim = opt, disp = True, earlystp = False )
    i = i + 1
    shuffleResults.append(cindex_test[-1])
    avg_cost += cindex_test[-1]
    print expID , ' ',   cindex_test[-1],  'average = ',avg_cost/i
  ## write output to file
  #outputFileName = os.path.join(resultPath, expID  + 'ci_tst')
  #f = file(outputFileName, 'wb')
  #cPickle.dump(cindex_test, f, protocol=cPickle.HIGHEST_PROTOCOL)
  #f.close()

  #outputFileName = os.path.join(resultPath, expID  + 'ci_trn')
  #f = file(outputFileName, 'wb')
  #cPickle.dump(cindex_train, f, protocol=cPickle.HIGHEST_PROTOCOL)
  #f.close()

  #outputFileName = os.path.join(resultPath , expID  + 'lpl_trn')
  #f = file(outputFileName, 'wb')
  #cPickle.dump(train_cost_list, f, protocol=cPickle.HIGHEST_PROTOCOL)
  #f.close()

  #outputFileName = os.path.join(resultPath, expID  + 'lpl_tst')
  #f = file(outputFileName, 'wb')
  #cPickle.dump(test_cost_list, f, protocol=cPickle.HIGHEST_PROTOCOL)
  #f.close()

  #outputFileName = os.path.join(resultPath, expID  + 'final_model')
  #f = file(outputFileName, 'wb')
  #cPickle.dump(model, f, protocol=cPickle.HIGHEST_PROTOCOL)
  #f.close()
  outputFileName = resultPath  + 'shuffle_cis'
  sio.savemat(outputFileName, {'cis':shuffleResults})#, f, protocol=cPickle.HIGHEST_PROTOCOL)
  print np.mean(shuffleResults), np.std(shuffleResults)
if __name__ == '__main__':
  Run()
