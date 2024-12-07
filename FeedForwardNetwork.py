# -*- coding: utf-8 -*-
"""FeedForwardNetwork.ipynb

Automatically generated by Colab.
"""

import tensorflow.compat.v1 as tf
import numpy as np
import urllib
tf.compat.v1.disable_eager_execution()
#
numTrainingIters = 10000
hiddenUnits = 500
numClasses = 3
batchSize = 100
#
def addToData (maxSeqLen, data, test, fileName, classNum, linesToUse, testLines):
    response = urllib.request.urlopen(fileName)
    content = response.readlines ()
    myInts = np.random.choice(len(content), linesToUse + testLines, False)
    i = len(data)
    k = len(test)
    counter = 0
    for whichLine in myInts.flat:

        line = content[whichLine].decode("utf-8")
        if line.isspace () or len(line) == 0:
            continue;
        if len (line) > maxSeqLen:
            maxSeqLen = len (line)
        temp = np.zeros((len(line), 256))
        j = 0
        for ch in line:
            if ord(ch) >= 256:
                continue
            temp[j][ord(ch)] = 1
            j = j + 1
        if counter < testLines: #first testLines lines read are stored as testing data
            test[k] = (classNum, temp)
            k = k + 1
        else:
            data[i] = (classNum, temp)
            i = i + 1
        counter += 1
    return (maxSeqLen, data, test)

def pad (maxSeqLen, data):
   for i in data:
        temp = data[i][1]
        label = data[i][0]
        len = temp.shape[0]
        padding = np.zeros ((maxSeqLen - len,256))
        data[i] = (label, np.transpose (np.concatenate ((padding, temp), axis = 0)))
   return data

# this also generates a new batch of training data, but it represents
# the data as a NumPy array with dimensions [batchSize, 256 * maxSeqLen]
# where for each data point, all characters have been appended.  Useful
# for feed-forward network training
def generateDataFeedForward (maxSeqLen, data):
    #
    # randomly sample batchSize lines of text
    myInts = np.random.randint (0, len(data), batchSize)
    #
    # stack all of the text into a matrix of one-hot characters
    x = np.stack ([data[i][1].flatten() for i in myInts.flat])
    #
    # and stack all of the labels into a vector of labels
    y = np.stack ([np.array((data[i][0])) for i in myInts.flat])
    #
    # return the pair
    return (x, y)


maxSeqLen = 0
data = {}
test = {}

# TODO: replace files 
(maxSeqLen, data, test) = addToData (maxSeqLen, data, test, "dataset1.txt", 0, 10000, 1000)
(maxSeqLen, data, test) = addToData (maxSeqLen, data, test, "dataset2.txt", 1, 10000, 1000)
(maxSeqLen, data, test) = addToData (maxSeqLen, data, test, "dataset3.txt", 2, 10000, 1000)

data = pad (maxSeqLen, data)
test = pad (maxSeqLen, test)

inputX = tf.placeholder(tf.float32, [batchSize, 256 * maxSeqLen])
inputY = tf.placeholder(tf.int32, [batchSize])



# the weight matrix that maps the inputs and hidden state to a set of values

# layer 1
W1 = tf.Variable(np.random.normal (0, 0.05, (256 * maxSeqLen, hiddenUnits)),dtype=tf.float32)
b1 = tf.Variable(np.zeros((1,hiddenUnits)), dtype=tf.float32)
# weights and bias for the final classification
W2 = tf.Variable(np.random.normal (0, 0.05, (hiddenUnits, numClasses)),dtype=tf.float32)
b2 = tf.Variable(np.zeros((1,numClasses)), dtype=tf.float32)

# unpack the input sequences so that we have a series of matrices,
# each of which has a one-hot encoding of the current character from
# every input sequence


# now we implement the forward pass



# compute the set of outputs
fir = tf.matmul(inputX, W1) + b1 #layer 1
#this is a cat: ^.w.^
outputs = tf.matmul(fir, W2) + b2 #final layer

predictions = tf.nn.softmax(outputs)

# compute the loss
losses = tf.nn.sparse_softmax_cross_entropy_with_logits(logits=outputs, labels=inputY)
totalLoss = tf.reduce_mean(losses)

# use gradient descent to train
trainingAlg = tf.compat.v1.train.AdagradOptimizer(0.025).minimize(totalLoss)

# and train!!
with tf.Session() as sess:
    #
    # initialize everything
    sess.run(tf.compat.v1.global_variables_initializer())
    #
    # and run the training iters
    for epoch in range(numTrainingIters):
        #
        # get some data
        x, y = generateDataFeedForward (maxSeqLen, data)
        #
        # do the training epoch
        _currentState = np.zeros((batchSize, hiddenUnits))
        _totalLoss, _trainingAlg, _predictions, _outputs = sess.run(
                [totalLoss, trainingAlg, predictions, outputs],
                feed_dict={
                    inputX:x,
                    inputY:y,
                })

        numCorrect = 0
        for i in range (len(y)):
           maxPos = -1
           maxVal = 0.0
           for j in range (numClasses):
               if maxVal < _predictions[i][j]:
                   maxVal = _predictions[i][j]
                   maxPos = j
           if maxPos == y[i]:
               numCorrect = numCorrect + 1

        #
        # print out to the screen
        print("Step", epoch, "Loss", _totalLoss, "Correct", numCorrect, "out of", batchSize)
    saver = tf.train.Saver()
    saver.save(sess, "task2.tf")

# testing
with tf.Session() as sess:
    saver = tf.train.Saver()
    saver.restore(sess, "task2.tf")
    testOrder = np.arange(3000)
    np.random.shuffle(testOrder)
    num = 0
    numCorrect = 0
    while num < 3000:
        selected = testOrder[i:i+batchSize]
        x = np.stack ([test[i][1].flatten() for i in selected.flat])
        y = np.stack ([np.array((test[i][0])) for i in selected.flat])
        _totalLoss, _predictions = sess.run([totalLoss, predictions], feed_dict={
            inputX:x,
            inputY:y
        })
        num += batchSize
        for i in range (len(y)):
           maxPos = -1
           maxVal = 0.0
           for j in range (numClasses):
               if maxVal < _predictions[i][j]:
                   maxVal = _predictions[i][j]
                   maxPos = j
           if maxPos == y[i]:
               numCorrect = numCorrect + 1
    print("Loss for 3000 randomly chosen documents is ", _totalLoss, "number correct labels is ", numCorrect, "out of 3000")