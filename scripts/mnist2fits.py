#!/usr/bin/env python

from __future__ import print_function

##################################################
###          MODULE IMPORT
##################################################
## STANDARD MODULES
import sys
import numpy as np
import os
import re
import json
from collections import defaultdict
import operator as op
import copy
from distutils.version import LooseVersion
import warnings

## COMMAND-LINE ARG MODULES
import getopt
import argparse
import collections

## ASTROPY MODULES
from astropy.io import fits

## TENSORFLOW
from keras.datasets import mnist

## GRAPHICS MODULES
import matplotlib.pyplot as plt

## LOGGER
import logging
import logging.config
logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)-15s %(levelname)s - %(message)s",datefmt='%Y-%m-%d %H:%M:%S')
logger= logging.getLogger(__name__)
logger.setLevel(logging.INFO)

#### GET SCRIPT ARGS ####
def str2bool(v):
	if v.lower() in ('yes', 'true', 't', 'y', '1'):
		return True
	elif v.lower() in ('no', 'false', 'f', 'n', '0'):
		return False
	else:
		raise argparse.ArgumentTypeError('Boolean value expected.')

###########################
##     ARGS
###########################
def get_args():
	"""This function parses and return arguments passed in"""
	parser = argparse.ArgumentParser(description="Parse args.")

	# - Input options
	parser.add_argument('-selclass','--selclass', dest='selclass', required=False, type=int, default=-1, help='Selected digit class to be read and converted to FITS (default=-1=all).') 
	parser.add_argument('-nmax', '--nmax', dest='nmax', required=False, type=int, default=-1, action='store',help='Max number of images to be read (-1=all) (default=-1)')
	parser.add_argument('--read_test', dest='read_test', action='store_true',help='Read test data')	
	parser.set_defaults(read_test=False)
	
	args = parser.parse_args()	

	return args



##############
##   MAIN   ##
##############
def main():
	"""Main function"""

	#===========================
	#==   PARSE ARGS
	#===========================
	logger.info("Get script args ...")
	try:
		args= get_args()
	except Exception as ex:
		logger.error("Failed to get and parse options (err=%s)",str(ex))
		return 1

	# - Options
	selclass= args.selclass
	nmax= args.nmax
	read_test= args.read_test

	#===========================
	#==   LOAD DATA
	#===========================
	(x_train, y_train), (x_test, y_test) = mnist.load_data()

	# - Select data to be converted
	data= x_train
	labels= y_train
	if read_test:
		data= x_test
		labels= y_test
	
	#===========================
	#==   CONVERT DATA
	#===========================
	nimgs= data.shape[0]
	counter= 0

	for i in range(nimgs):
		label= labels[i]

		# - Check if this class is selected 
		if label!=selclass:
			continue

		# - Check if max number of images is reached
		if nmax>0 and counter>=nmax:
			logger.info("Max number of images reached (%d), exit loop ..." % (counter))
			break

		# - Convert data to FITS
		counter+= 1
		digits= '000'
		if counter>=10 and counter<100:
			digits= '00'
		elif counter>=100 and counter<1000:
			digits= '0'
		elif counter>=1000 and counter<10000:
			digits= ''
		outfilename= "mnist_class" + str(label) + str("_") + digits + str(counter) + '.fits'

		logger.info("Converting image %d to FITS file %s ..." % (i, outfilename))
		img_data= data[i]

		#hdu_out= fits.PrimaryHDU(img_data, header)
		hdu_out= fits.PrimaryHDU(img_data)
		hdul = fits.HDUList([hdu_out])
		hdul.writeto(outfilename, overwrite=True)


	return 0


###################
##   MAIN EXEC   ##
###################
if __name__ == "__main__":
	sys.exit(main())
