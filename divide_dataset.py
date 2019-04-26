#This code was taken from https://github.com/spmallick/learnopencv
#It creates Two .txt used to train the neural network
#This files uses the images from the dataset to divide the dataset in training and validation sets
#Francisco Silva
#Matthew Roberts
#Team_307
#4/26/2019

import random
import os
import subprocess
import sys

def split_data_set(image_dir):

    f_val = open("human_val.txt", 'w')
    f_train = open("human_train.txt", 'w')

    path, dirs, files = next(os.walk('/home/ubuntu/yolov3/images'))
    data_size = len(files)

    ind = 0
    data_test_size = int(0.25 * data_size)
    test_array = random.sample(range(data_size), k=data_test_size)

    for f in os.listdir(image_dir):
        if(f.split(".")[1] == "png"):
            ind += 1

            if ind in test_array:
                f_val.write(image_dir+'/'+f+'\n')
            else:
                f_train.write(image_dir+'/'+f+'\n')


split_data_set(sys.argv[1])
