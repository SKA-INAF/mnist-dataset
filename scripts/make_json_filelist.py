from __future__ import print_function

##################################################
###          MODULE IMPORT
##################################################
## STANDARD MODULES
import os
import sys
import subprocess
import string
import time
import signal
from threading import Thread
import datetime
import numpy as np
import random
import math
import logging
import fnmatch

## COMMAND-LINE ARG MODULES
import getopt
import argparse
import collections
import json

#### GET SCRIPT ARGS ####
def str2bool(v):
	if v.lower() in ('yes', 'true', 't', 'y', '1'):
		return True
	elif v.lower() in ('no', 'false', 'f', 'n', '0'):
		return False
	else:
		raise argparse.ArgumentTypeError('Boolean value expected.')

## LOGGER
import logging
import logging.config
logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)-15s %(levelname)s - %(message)s",datefmt='%Y-%m-%d %H:%M:%S')
logger= logging.getLogger(__name__)
logger.setLevel(logging.INFO)

###########################
##     ARGS
###########################
def get_args():
	"""This function parses and return arguments passed in"""
	parser = argparse.ArgumentParser(description="Parse args.")

	parser.add_argument('-fileext','--fileext', dest='fileext', required=False, type=str, default='fits', help='File extension to be placed in list')
	parser.add_argument('-rootdir','--rootdir', dest='rootdir', required=False, type=str, default='', help='Directory where to start searching file to be placed in list') 
	parser.add_argument('-fileprefix','--fileprefix', dest='fileprefix', required=False, type=str, default='', help='File prefix filter') 
	parser.add_argument('-filesubfix','--filesubfix', dest='filesubfix', required=False, type=str, default='', help='File subfix filter') 
	parser.add_argument('-sname_strip_patterns','--sname_strip_patterns', dest='sname_strip_patterns', required=False, type=str, default='', help='String patterns to be stripped from filename to get source name') 
	parser.add_argument('-exclude_patterns','--exclude_patterns', dest='exclude_patterns', required=False, type=str, default='', help='Exclude files containing these patterns') 
	
	parser.add_argument('--recursive', dest='recursive', action='store_true',help='Search recursively down from ROOT_DIR ')	
	parser.set_defaults(recursive=False)	
	parser.add_argument('-outfile','--outfile', dest='outfile', required=False, type=str, default='filelist.json', help='Output file name with file list')
	parser.add_argument('-class_label','--class_label', dest='class_label', required=False, type=str, default='UNKNOWN', help='Label to be specified for each image')
	parser.add_argument('-class_id','--class_id', dest='class_id', required=False, type=int, default=-1, help='Class id to be specified for each image')
	parser.add_argument('-normalizable_flag','--normalizable_flag', dest='normalizable_flag', required=False, type=int, default=1, help='Normalizable flag (1/0)')
	
	args = parser.parse_args()	

	return args

def file_sorter(item):
	""" Custom sorter of filename according to rank """
	return item[1]

def get_file_rank(filename):
	""" Return file order rank from filename """

	# - Check if radio
	is_radio= False
	score= 0
	if "meerkat_gps" in filename:
		is_radio= True
	if "askap" in filename:
		is_radio= True
	if "first" in filename:
		is_radio= True
	if is_radio:
		score= 0

	# - Check if 12 um
	if "wise_12" in filename:
		score= 1

	# - Check if 22 um
	if "wise_22" in filename:
		score= 2

	# - Check if 3.4 um
	if "wise_3_4" in filename:
		score= 3

	# - Check if 4.6 um
	if "wise_4_6" in filename:
		score= 4

	# - Check if 8 um
	if "irac_8" in filename:
		score= 5

	# - Check if 70 um
	if "higal_70" in filename:
		score= 6

	return score

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

	rootdir= args.rootdir
	recursive= args.recursive
	fileprefix= args.fileprefix
	filesubfix= args.filesubfix
	fileext= args.fileext
	sname_strip_patterns= [str(x.strip()) for x in args.sname_strip_patterns.split(',')]
	exclude_patterns= [str(x.strip()) for x in args.exclude_patterns.split(',')]
	class_id= args.class_id	
	class_label= args.class_label
	normalizable_flag= args.normalizable_flag
	outfile= args.outfile

	#===========================
	#==   LIST FILES
	#===========================
	file_pattern= "{}*{}.{}".format(fileprefix,filesubfix,fileext)
	logger.info("Searching for files matching with pattern %s ..." % file_pattern)
	
	data_dict= {"data": []}

	for root, dirs, files in os.walk(rootdir):

		# - Search for files matching pattern
		filenames= []
		
		for filename in fnmatch.filter(files, file_pattern):
			filename_full= os.path.join(root, filename)
			filenames.append(filename_full)

		#print("filenames")
		#print(filenames)
		
		# - Exclude files containing exclusion patterns
		if filenames:
			filenames_sel= []
			for filename in filenames:
				exclude= False
				for pattern in exclude_patterns:
					#print("pattern=%s" % (pattern))
					if pattern!="" and pattern in filename:
						exclude= True
						break
				if not exclude:
					filenames_sel.append(filename)

			filenames= filenames_sel

			#print("filenames")
			#print(filenames)


		# Create file dictionary
		if filenames:
			# - Sort filename (bash equivalent)
			filenames_sorted= sorted(filenames)
			filenames= filenames_sorted

			#print("filenames")
			#print(filenames)

			# - Sort filename according to specified ranks
			filenames_ranks = []
			for filename in filenames:
				rank= get_file_rank(filename)
				filenames_ranks.append(rank)

						
			filenames_tuple= [(filename,rank) for filename,rank in zip(filenames,filenames_ranks)]
			filenames_tuple_sorted= sorted(filenames_tuple, key=file_sorter)
			##print("filenames_tuple_sorted")
			filenames_sorted= []
			for item in filenames_tuple_sorted:
				 filenames_sorted.append(item[0])

			filenames= filenames_sorted

			print("filenames (after sort)")
			print(filenames)

			# - Loop over filenames
			for item in filenames:

				# - Create normalizable flags
				normalizable= [normalizable_flag]		

				# - Compute source name from file
				filename_base= os.path.basename(item)
				filename_base_noext= os.path.splitext(filename_base)[0]
				sname= filename_base_noext
				for sname_strip_pattern in sname_strip_patterns:
					sname_tmp= sname.replace(sname_strip_pattern,'')
					sname= sname_tmp

				print("sname=%s" % (sname))

				# - Add entry in dictionary
				d= {}
				d["filepaths"]= [item]
				d["normalizable"]= normalizable
				d["sname"]= sname
				d["id"]= class_id
				d["label"]= class_label
				data_dict["data"].append(d)

		if not recursive:
			break

	
	#print("Data")
	#print(data_dict)

	#===========================
	#==   SAVE FILELIST
	#===========================
	logger.info("Saving json datalist ...")
	with open(outfile, 'w') as fp:
		json.dump(data_dict, fp)

	return 0

###################
##   MAIN EXEC   ##
###################
if __name__ == "__main__":
	sys.exit(main())

