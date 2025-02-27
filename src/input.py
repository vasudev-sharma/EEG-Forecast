import numpy as np
import scipy as sio
import os
import matplotlib as plt
import numpy as np
import scipy.io as sio
rng = np.random
from sklearn.preprocessing import StandardScaler


from scipy import stats
from utils import rolling_window, preprocess_data

forecasting_self = os.environ["forecasting_self"]
MIMO_output = os.environ["MIMO_output"]
model_name = os.environ["model_name"]


def get_data():

  # data import from matlab
  subject = sio.loadmat('../input/1filtered.mat')      #recovering matlab data in the form of a python dictionar
  format_1 = subject['data']          #in the dictionary, only the data key interests us
  print (format_1.shape)

  # shuffle trials
  (_, trial, _)= format_1.shape

  trials = np.arange(trial)
  np.random.shuffle(trials)

  #Z score
  format_1=stats.zscore(format_1, axis=2)

  assert (format_1.shape == (65, 192, 840))
  '''
  trials_train = np.array([172, 125, 136,  99,  82,  31, 133,  44, 183, 184, 142, 121,  18,
          89, 141,  27, 107,  49,  68, 186,  70,  92, 109,   6, 147, 124,
        117, 161, 137,  39, 157, 159,   4,  23,  25, 145, 179, 118, 163,
        106,  69, 187,  76, 108, 188,  32, 178,  19,  26,  72, 168, 158,
          55,   8, 167,  11,  30,  59,  80,  95,  60, 148, 153,  45,  20,
        152,  73,  48,  36, 100, 185, 131, 138,   3,  13,  97, 126, 171,
        130,  54,   2,  50,  75,  83,  33, 174, 140,  79, 113, 146,  81,
          64,  63,  46, 170,  16, 173, 156,  90, 103, 144,  29,  58,  47,
        105, 189,  56,  34,  12, 165, 122, 119,  94,  42,  24,  37,  14,
          65,  93,  87, 154,  77, 166, 114, 112, 160, 164,  51, 139,  84,
        169,  85, 162,  88,  66, 155,  78,  28,   9,   1,  98, 132, 175,
        177, 115,  96, 111,  52,  21, 180,  61, 191, 143,  10])

  trials_valid = np.array([ 67,  15,  38,  22,   0,  74, 182, 151,  91,  43,  53, 123, 127,
        128, 149, 190, 134, 102, 181])

  trials_test = np.array([116,  57, 110,   7,  40, 176, 150,  41, 120, 135, 101,  71,  62,
            86, 129,  35, 104,   5,  17])
  train_data = format_1[:, trials_train, :]
  valid_data = format_1[:, trials_valid, :]
  test_data = format_1[:, trials_test, :]

  format_1 = np.concatenate((train_data, valid_data, test_data), axis = 1)
  print(format_1)


  scaler = StandardScaler()
  train_data = scaler.fit_transform(train_data.reshape(-1, train_data.shape[-1])).reshape(train_data.shape)
  valid_data = scaler.transform(valid_data.reshape(-1, valid_data.shape[-1])).reshape(valid_data.shape)
  test_data = scaler.transform(test_data.reshape(-1, test_data.shape[-1])).reshape(test_data.shape)


  
  #inverse transform
  train_data = scaler.inverse_transform(train_data)
  valid_data = scaler.inverse_transform(valid_data)
  test_data = scaler.inverse_transform(test_data)
  
  format_1 = np.concatenate((train_data, valid_data, test_data), axis = 1)
  print("Inverted data is ", format_1)
  print(format_1.shape)
  '''
  #format_1, scaler = preprocess_data(format_1)
  #format_1 = format_1[:, :, 160:]
  return format_1, trials




def extract_Y (data, window, source, batch_trials, horizon = 1, multivariate = False):             
    #creation of a function to recover y - simplification of reading

    '''
      param: data - (3D np.array of Shape [Channels, Trials, Timepoints]), the EEG data is of the shape [64, 192, 840] 
      param: window - (int), window size 
      param: source - (List of int),  Electrodes /Channels
      param: batch_trials - (List of int), Trails of the data
      param: horizon - (int), Number of future time steps to be predicted
      param: split- (Boolean), If modelling using LR set split to False, else set slit to True so that shape would be [Batch_Size, Window, Features]

      return: (np array), shape: [Batch_size, horizon]

    '''

    y = []
    for i in source:                                                                      #reading the source list

      y_tmp = []
      for j in batch_trials:
        tmp = rolling_window(data[i, j,window :], horizon)                                 #Compute the windowed numpy array for each electrode for each trail
        y_tmp.append(tmp)
      y.append(np.vstack(y_tmp))

    if multivariate:
      y= np.moveaxis(np.array(y), 0, -1)                                                  
    else: 
      y = np.hstack(y) 
    return(y) 






def extract_X (data,  window, source, batch_trials, horizon = 1, split = True):                     
    #creation of a function to recover x - simplification of reading
    '''
      param: data - (3D np.array of Shape [Channels, Trials, Timepoints]), the EEG data is of the shape [64, 192, 840] 
      param: window - (int), window size 
      param: source - (List of int),  Electrodes/ Channels
      param: trials - (List of int), Trails of the data
      param: horizon - (int), Number of future time steps to be predicted
      param: multivarite - (Boolean), to indicate whether to perform multivariate prediction or not

      return: np array, shape: [Batch_size, window,channels]

    '''
   
    time_points = data.shape[-1] 
    x = np.zeros((len(source),  len(batch_trials) * (time_points - window  - horizon + 1), window)) 

    for idx, i in enumerate(source):                                      #reading the source list
      x_tmp = []
      for j in batch_trials:
        tmp = rolling_window(data[i, j, : -horizon], window)              #Compute the windowed numpy array for each electrode for each trail
        x_tmp.append(tmp)                                                       
      x[idx] = np.vstack(x_tmp)

    x = np.hstack(x)
   
    if split:                                                             #Split the np array into number of features such that intial array [Batch_size, window * Channels] becomes new array of shape [Batch_size, window, channels]
        x = np.array(np.split(x, len(source), axis = -1))
        x = np.moveaxis(x, 0, -1)
    
    return x



def split_data(data, window, trials, source_Y, source_X, horizon, split, multivariate):

    #Split the trials
    #trials_train, trials_valid, trials_test = split_trials(trials)
    '''Hard coding of the results to produce consistent result'''
    trials_train = np.array([172, 125, 136,  99,  82,  31, 133,  44, 183, 184, 142, 121,  18,
        89, 141,  27, 107,  49,  68, 186,  70,  92, 109,   6, 147, 124,
       117, 161, 137,  39, 157, 159,   4,  23,  25, 145, 179, 118, 163,
       106,  69, 187,  76, 108, 188,  32, 178,  19,  26,  72, 168, 158,
        55,   8, 167,  11,  30,  59,  80,  95,  60, 148, 153,  45,  20,
       152,  73,  48,  36, 100, 185, 131, 138,   3,  13,  97, 126, 171,
       130,  54,   2,  50,  75,  83,  33, 174, 140,  79, 113, 146,  81,
        64,  63,  46, 170,  16, 173, 156,  90, 103, 144,  29,  58,  47,
       105, 189,  56,  34,  12, 165, 122, 119,  94,  42,  24,  37,  14,
        65,  93,  87, 154,  77, 166, 114, 112, 160, 164,  51, 139,  84,
       169,  85, 162,  88,  66, 155,  78,  28,   9,   1,  98, 132, 175,
       177, 115,  96, 111,  52,  21, 180,  61, 191, 143,  10])

    trials_valid = np.array([ 67,  15,  38,  22,   0,  74, 182, 151,  91,  43,  53, 123, 127,
        128, 149, 190, 134, 102, 181])

    trials_test = np.array([116,  57, 110,   7,  40, 176, 150,  41, 120, 135, 101,  71,  62,
            86, 129,  35, 104,   5,  17])


    if MIMO_output:

      #Extract Y
      y_train = extract_Y (data, window,  source_Y, trials_train, horizon = horizon, multivariate = multivariate)
      print ("y_train.shape = ", y_train.shape)

      y_valid = extract_Y (data, window, source_Y, trials_valid, horizon  = horizon, multivariate= multivariate)
      print ("y_valid.shape = ", y_valid.shape)

      y_test = extract_Y (data, window, source_Y, trials_test, horizon = horizon, multivariate= multivariate)
      print ("y_test.shape = ", y_test.shape)

      #Extract X
      x_train = extract_X (data, window, source_X, trials_train,  horizon  = horizon,   split = split)
      print ("x_train.shape = ", x_train.shape)

      x_valid = extract_X (data, window, source_X, trials_valid, horizon = horizon , split = split)
      print ("x_valid.shape = ", x_valid.shape)

      x_test = extract_X (data, window, source_X, trials_test, horizon = horizon, split = split)
      print ("x_test.shape = ", x_test.shape)
    
    else: 
      #Extract Y
      y_train = extract_Y (data, window,  source_Y, trials_train, horizon = 1, multivariate = False)
      print ("y_train.shape = ", y_train.shape)

      y_valid = extract_Y (data, window, source_Y, trials_valid, horizon  = 1, multivariate= False)
      print ("y_valid.shape = ", y_valid.shape)

      y_test = extract_Y (data, window, source_Y, trials_test, horizon = horizon, multivariate= multivariate)
      print ("y_test.shape = ", y_test.shape)

      #Extract X
      x_train = extract_X (data, window, source_X, trials_train,  horizon  = 1,   split = split)
      print ("x_train.shape = ", x_train.shape)

      x_valid = extract_X (data, window, source_X, trials_valid, horizon = 1 , split = split)
      print ("x_valid.shape = ", x_valid.shape)

      x_test = extract_X (data, window, source_X, trials_test, horizon = horizon, split = split)
      print ("x_test.shape = ", x_test.shape)

  

    return (x_train, y_train), (x_valid, y_valid), (x_test, y_test)

def teacher_forcing(encoder_input_data, decoder_target_data ):
  # lagged target series for teacher forcing
  # i.e, during training, the true series values (lagged by one time step) are fed as inputs to the decoder.
  # Intuitively, we are trying to teach the NN how to condition on previous time steps to predict the next.
  # At prediction time, the true values in this process will be replaced by predicted values for each previous time step.
  decoder_input_data = np.zeros((decoder_target_data.shape[0], decoder_target_data.shape[1], encoder_input_data.shape[2]))
  '''
  decoder_input_data[:, 1:, :] = decoder_target_data[:, :-1, :]  # target = input shifted by one
  decoder_input_data[:, 0, :] = encoder_input_data[:, -1, :]
  '''
  return encoder_input_data,decoder_input_data, decoder_target_data


def split_trials(trials):
  #### separation of train tests / valid / test
  train_num = int(np.around(len(trials) * 0.8))
  valid_num = int(np.around(len(trials) * 0.1))

  trials_train = trials[0:train_num]
  trials_valid = trials[train_num:train_num+valid_num]
  trials_test = trials[train_num+valid_num:]

  return trials_train, trials_valid, trials_test

 
def get_info(pred, input_task, stimulus, format_1):

    '''
      param: pred -(int), parameter to predict the channel in the eeg experiment
      param: input_task -  (string),  indicating which task to perform 1 --> Stiluli to EEG
                                                                  2 --> EEG to stimuli 
                                                                  3 --> EEG to EEG porecasting
      param: stimulus - (string),  indicating to whether include stimuli or not in the data 
                                                                  1 --> Include stimuli information
                                                                  2 --> Not include stimuli information

      return source_X(List of int), source_Y(List of int), window(int)

    '''
    window = 160

    if input_task == '1':
        electi = [pred]
        print(electi)

        if stimulus == "2":
            source_Y = electi      #retrieving the electrode number as a whole number - implies that there is only one electrode chosen in this direction
            source_X = [0]          #conversion of the stimuli line in the form of a list - necessary for the for loop: see below - extraction X
        else:
        #Use stimuli
            source_Y = electi
            source_X = [0] + electi

    elif input_task == '2':
        print("Hello")
        electi = [pred]
        print(electi)
        format_1 = np.flip(format_1,2)     # data inversion according to the time dimension - problem ????
        source_Y = [0]
        source_X = electi
        print("Source_X value in get info loop is ", source_X)
        
    elif input_task == '3':

        electi = [i for i in range(1, 65) if i!=pred] 

        if len(electi)!= 64: 
          n_channel = [pred]  
        else:
          n_channel = electi
          print("The value of channel to be predicted is ", n_channel)

        
        if stimulus == "2":
            source_Y = n_channel
            source_X = n_channel if forecasting_self else electi
        #Use stimuli
        else: 
            source_Y = n_channel
            source_X = electi + [0] 

    return source_X, source_Y, window, format_1

def data(pred, input_task, stimulus,  horizon,  split, multivariate):
    
    '''

    param: pred - (int), parameter to predict the channel in the eeg experiment
    param: input_task - (string),  indicating which task to perform 1 --> Stiluli to EEG
                                                                2 --> EEG to stimuli 
                                                                3 --> EEG to EEG porecasting
    param: stimulus - (String),  indicating whether to include stimuli or not in the data 
                                                                1 --> Include stimuli information
                                                                2 --> Not include stimuli information
    param: horizon - (int),  number of time steps to predicted in the future
    param: split   - (Boolean) Indicating  whether to use LR (False) or not (True - other models)
    param: mutivariate -  (Boolean) indicating whether you want to split the data into features or not
                                                                True --> Used for case for mutistep forecasting 
                                                                False ---> Used for isingle step forecasting
                                          
    return: (Tuple of 3 np.array's), splits the EEG data into train, validation and test set          
    '''                                            


   

    #get data
    data, trials = get_data()

    source_X, source_Y, window, data = get_info(pred, input_task, stimulus, data)
    print("Value of source_Y is", source_Y)
    print("Value of source_X is", source_X)



    return(split_data(data, window, trials, source_Y, source_X, horizon, split, multivariate))



