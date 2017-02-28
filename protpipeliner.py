#!/usr/bin/python

#PYTHON SCRIPT 
#written by: Richard Wolfe
#
################################################################################
# This script is a modification of protpipeliner.rb which included the following:
#Copyright (c) 2013 Brian C. Thomas
#
#Permission is hereby granted, free of charge, to any person obtaining
#a copy of this software and associated documentation files (the
#"Software"), to deal in the Software without restriction, including
#without limitation the rights to use, copy, modify, merge, publish,
#distribute, sublicense, and/or sell copies of the Software, and to
#permit persons to whom the Software is furnished to do so, subject to
#the following conditions:
#
#The above copyright notice and this permission notice shall be
#included in all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
#LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
#OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
#WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
##############################################################################
#
#   requires:
#        python 2.6 
#        muscle  version 3.8.31 to be in path (not tried with other versions)
#        /opt/scripts/bin/fasta_fastq/fasta2phy
#        /opt/scripts/bin/Phylogeny_Protpipe/phyToFasta.pl 
#        grep
#        Gblocks version 0.91b (not tried with other versions)
#        java
#        java -jar /opt/prottest-3.4-20140123/prottest-3.4.jar
#        awk
#        raxmlHPC-PTHREADS to be in path
#
#   if error: /usr/bin/python^M: bad interpreter: No such file or directory
#      -there is a windows endl after shebang
#      -open in vi 
#         once in vi type:
#           :set ff=unix<return>
#           :x<return>
#
#
#
# 
#
#   -i --input_file   <fasta file>      (required)    
#   -t --threads  <int>     (required)         
#   -b --bootstraps <int>  (required)
#   -m --mode  "high" "med" "low" or "none"
#   -a --aligned_file T or F  if T then do not run muscle
#   --osc (no args) use if running on OSC (optional)
# 
#   -input file would be a fasta file 
#   -output file  is the name you want to call the output file
#
#   Example command to run if input file is not an aligned fasta file:
#      protpipeliner.py -i  FraDNamedCleanUp.fasta -t 20 -b 50 -m none -a F
#
#   Example command to run if input file is an aligned fasta file:
#      protpipeliner.py -i  FraDNamedCleanUp.aln -t 20 -b 50 -m none -a T
#
#  This script makes the folowing output files
#  1. <input file name>.rename (file with changed header ids)
#  2. <input file name>.al (muscle output file)
#  3. <input file name>.temp (fasta file)
#  4. <input file name>.temp.fst (GBlocks output file)
#  5. <input file name>.phy (phylip file)
#  6. <input file name>.model (protest output file)
#  7. <input file name>.phy.reduced (???)
#  8. snapshot (this is a folder)
#  9. RAxML_info.<input file name> (raxml output file)
#  10. RAxML_bestTree.<input file name> (raxml tree with g_xx labels)
#  11. RAxML_bipartitionsBranchLabeels.<input file name> (raxml tree with g_xx labels)
#  12. RAxML_bipartitions.<input file name> (raxml output file)
#  13. RAxML_bootstrap.<input file name>    (raxml outputfile)
#  14. bestTree.<input file name>_mode_<mode>.renamed (results tree)
#  15. bipartitionsBrachLabels.<input file name>_mode_<mode>.renamed (results tree)
#  16. bipartitions.<input file name>_mode_<mode>.renamed (results tree)
#


import sys      #for exit command and maxint
import argparse #to get command line args 
                #needed to install argparse module because using python 2.6
                #and argparse comes with python 2.7
                #  sudo easy_install argparse
import os       #to run system commands



#create an argument parser object
#description will be printed when help is used
parser = argparse.ArgumentParser(description='A script to run protpipeliner')

#add the available arguments -h and --help are added by default
#if the input file does not exist then program will exit
#if output file does not exit it will be created
# args.input is the input file Note: cant write to this file because read only
# args.output is the output file
# args.m is the minimum seq length
parser.add_argument('-i', '--input_file', type=argparse.FileType('rU'), help='fasta file',required=True)
parser.add_argument('-t', '--threads', type=int, help='number of threads', required=True)
parser.add_argument('-b', '--bootstraps', type=int, help='number of bootstraps for RAxML', required=True)
parser.add_argument('-m', '--mode', help='either high (n) or med (h) or low (a) or none (NO_GBLOCKS)', required=True)
parser.add_argument('-a', '--aligned_file', help='Is input file aligned fasta file either T or F', required=True)
parser.add_argument('--osc', help='Running on OSC', action="store_true")
parser.add_argument('--stop_after_prottest', help='Stop script after running prottest', action="store_true")
parser.add_argument('--skip_prottest', help='skip protest and the model to use', default="USE_PROTEST")



#get the args
args = parser.parse_args()

#additional argument tests


if args.threads <= 0:
	print "Error: argument --threads <= 0"
	sys.exit(0)

if args.bootstraps <= 0:
	print "Error: argument --bootstraps <= 0"
	sys.exit(0)


mode = ""

if args.mode == "high":
	mode = "n"
elif args.mode == "med":
	mode = "h"
elif args.mode == "low":
	mode = "a"
elif args.mode =="none":
	mode = "NO_GBLOCKS"
else:
	print "Error -m needs to be high or med or low or none"
	sys.exit(1)


if args.aligned_file != "T":
	if args.aligned_file != "F":
		print "Error -a needs to be T or F"
		sys.exit(1)


#DELETE_FILES = "TRUE"
DELETE_FILES = "FALSE"


#if args.stop_after_prottest:
#	sys.exit(0)

##############################################
#set paths to programs on OSC -- use string that runs command on the system
muscle_path = "muscle"
fasta2phy_path = "/opt/scripts/bin/fasta_fastq/fasta2phy"
phyToFasta_path = "/opt/scripts/bin/Phylogeny_Protpipe/phyToFasta.pl"
gblocks_path = "Gblocks"
prottest_path = "/opt/prottest-3.4-20140123/prottest-3.4.jar"
raxml_path = "raxmlHPC-PTHREADS"

if args.osc:  #if running on OSC need to change paths
	muscle_path = "/users/PAS1018/osu9681/bin/protpipeliner/muscle"
	fasta2phy_path = "/users/PAS1018/osu9681/bin/protpipeliner/fasta2phy"
	phyToFasta_path = "/users/PAS1018/osu9681/bin/protpipeliner/phyToFasta.pl"
	gblocks_path = "/users/PAS1018/osu9681/bin/protpipeliner/Gblocks"
	prottest_path = "/users/PAS1018/osu9681/bin/protpipeliner/prottest-3.4-20140123/prottest-3.4.jar"
	raxml_path = "/users/PAS1018/osu9681/bin/protpipeliner/raxmlHPC-PTHREADS"




print "Script started ..."

#need to get the filename from the -i path
file_name = os.path.basename(args.input_file.name)
print file_name




#close the files so there are no problems
args.input_file.close()



#need to check if the raxml files with this name already exist
#if they do then raxml will be in error
#if they exist then we will exit and let the user delete the files
if os.path.isfile("RAxML_bestTree." + file_name):
	print "ERROR...RAxML_bestTree." + file_name + " file already exists"
	sys.exit(1)
if os.path.isfile("RAxML_bipartitionsBranchLabels." + file_name):
	print "ERROR...RAxML_bipartitionsBranchLabels." + file_name + " file already exists"
	sys.exit(1)
if os.path.isfile("RAxML_bipartitions." + file_name):
	print "ERROR...RAxML_bipartitions." + file_name + " file already exists"
	sys.exit(1)
if os.path.isfile("RAxML_bootstrap." + file_name):
	print "ERROR...RAxML_bootstrap." + file_name + " file already exists"
	sys.exit(1)
if os.path.isfile("RAxML_info." + file_name):
	print "ERROR...RAxML_info." + file_name + " file already exists"
	sys.exit(1)

  

#need to rename the fasta sequences as g_0 g_1 g_2...g_XX (should be ok for g_9999999 or 9,999,999 sequences max?)
#makes a new fasta file same as input file plus .renamed
print "\n\n-- Renaming input fasta sequences"


infile = open(args.input_file.name, 'rU')  #open the input file
outfilename = file_name + '.rename'
outfile = open(outfilename, 'w')  #open an output file

scaffold = 0

line = infile.readline()  #read first line
while line:
	if line.startswith('>'):  #if header line
		line = ">g_" + str(scaffold) + "\n"
		scaffold += 1 

	outfile.write(line)

	line = infile.readline()

infile.close()
outfile.close()



#running muscle which alligns the sequences
if args.aligned_file == 'F': 
	print "-- Starting muscle MSA on " + file_name + ".rename"

	cmd = muscle_path + ' -in ' + file_name + '.rename' + ' -out ' + file_name + '.al'

	retvalue = os.system(cmd) #returns 0 if no error in command

	if retvalue != 0:  #if command failed
		print "ERROR command did not return 0 and failed"
		sys.exit(1)  #return 0 if sucess

	print "-- done with muscle"

#print args.aligned_file
if args.aligned_file == 'T':
        print "Input file is aligned fasta so copy input file to input file .al"
	cmd = 'cp ' + file_name + '.rename ' + file_name + '.al'
        retvalue = os.system(cmd) #returns 0 if no error in command

        if retvalue != 0:  #if command failed
                print "ERROR command did not return 0 and failed"
                sys.exit(1)  #return 0 if sucess

#convert to phylip format
print "-- Converting to phylip format and cleaning up"

#cmd = 'cat ' + file_name + '.al | ' + fasta2phy_path + ' | ' + phyToFasta_path + ' > ' + file_name + '.tmp'

#retvalue = os.system(cmd) #returns 0 if no error in command

#if retvalue != 0:  #if command failed
#	print "ERROR command did not return 0 and failed"
#	sys.exit(1)  #return 0 if sucess

cmd = "cp " + file_name + ".al " + file_name + ".tmp"
retvalue = os.system(cmd) #returns 0 if no error in command
if retvalue != 0:  #if command failed
	print "ERROR command did not return 0 and failed"
	sys.exit(1)  #return 0 if sucess

cmd = 'grep -c ">" ' + file_name + '.al'

f = os.popen(cmd)
seqs = f.read()
seqs = seqs.strip()  #remove whitespace and endlines

print "The number of sequences in alignment file = ", seqs


if mode != "NO_GBLOCKS":

	#running gblocks
	print "-- Running Gblocks to detect conversed regions in the MSA"

	cmd = gblocks_path + ' ' + file_name + '.tmp' + ' -t=p -p=n -e=.fst -b1=$(((' + str(seqs) + '/2)+1)) -b2=$(((' + str(seqs) + '/2)+1)) -b3=$(((' + str(seqs) + '/2))) -b4=2 -b5=' + mode

	print "cmd = "
	print cmd

	retvalue = os.system(cmd) #returns 0 if no error in command

	print "-- done with Gblocks"
	
	#if retvalue != 0:  #if command failed
	#	print "ERROR command did not return 0 and failed"
	#	sys.exit(1)  #return 0 if sucess

else:
	#not running gblocks so rename the alignment file
	cmd = 'mv ' + file_name + '.tmp ' + file_name + '.tmp.fst'

	retvalue = os.system(cmd) #returns 0 if no error in command

	if retvalue != 0:  #if command failed
		print "ERROR command did not return 0 and failed"
		sys.exit(1)  #return 0 if sucess



#convert to phy 
# cat sample_10_sequences.faa.tmp.fst | /opt/scripts/bin/fasta_fastq/fasta2phy > sample_10_sequences.faa.phy

cmd = 'cat ' + file_name + '.tmp.fst | ' + fasta2phy_path + ' > ' +  file_name + '.phy' 
 
retvalue = os.system(cmd) #returns 0 if no error in command

if retvalue != 0:  #if command failed
	print "ERROR command did not return 0 and failed"
	sys.exit(1)  #return 0 if sucess


#run protTest
if args.skip_prottest == "USE_PROTEST":
	print "\n\n-- Starting ProtTest"

	cmd = 'java -jar ' + prottest_path + ' -i ' + file_name + '.phy -o ' + file_name + '.model -all-matrices -all-distributions -log disabled -threads ' + str(args.threads)

	#run and collect and redirect screen output to variable
	f = os.popen(cmd)
	output = f.read()



	#extract best model
	#note use tripple quotes because we want to include the single quote in the string
	cmd = 'grep "Best model according to" ' + file_name + """.model | awk '{print$6}' | awk -F+ '{print $1'} | tr "[:lower:]" "[:upper:]" """

	f = os.popen(cmd)
	model = f.read()
	model = model.strip() #remove white space both ends

	#I added this because i got 2 best results when i tried a sample
	#I got WAG\nWAG
	best = model.split() #will split on whitespace including endl
	model = best[0] #take first element

	print "\n\nBest model from ProtTest was: " + model





	if args.stop_after_prottest:
		sys.exit(0)




	#run raxml
	print "\n\n--Starting raxmlHPC"

	#Iadded -p paramater this should be a random number and not fixed each time
	cmd = raxml_path + ' -f a -m PROTCAT'+ model + ' -n ' + file_name + ' -N ' + str(args.bootstraps) + ' -p 1234 -s ' + file_name + '.phy -x 1234 -T ' + str(args.threads)

	f = os.popen(cmd)

	#print the output from raxml
	for line in f:
   		print line,
	f.close()

else:
	if args.stop_after_prottest:
		sys.exit(0)

	#run raxml
	print "\n\n--Starting raxmlHPC"

	#Iadded -p paramater this should be a random number and not fixed each time
	cmd = raxml_path + ' -f a -m ' + args.skip_prottest + ' -n ' + file_name + ' -N ' + str(args.bootstraps) + ' -p 1234 -s ' + file_name + '.phy -x 1234 -T ' + str(args.threads)

	f = os.popen(cmd)

	#print the output from raxml
	for line in f:
   		print line,
	f.close()


#rename the tree with original names
print "\n\nRenaming output tree to use original names"

#read the raxml file into a variable raxml_file
#cmd = 'cat RAxml_bestTree.' + args.input_file.name
#r = os.popen(cmd)
fn = 'RAxML_bestTree.' + file_name

try:
	r = open(fn, 'r')

except IOError:
	print "Error.. raxml did not make file " + fn
        sys.exit(1)

raxml_file = r.read() #read entire file into variable

#open the original input file
f = open(args.input_file.name, 'rU')
index = 0
for line in f:
	if line.startswith('>'):
		gene_label = 'g_' + str(index) + ':'
		line_list = line.split()
  		orig_label = line_list[0] #the first element
 		orig_label.strip() #remove whitespace and endline
		orig_label = orig_label.replace(">", "") #remove >
		#replace any illegal characters in id
		orig_label = orig_label.replace(":", "_") #remove : it will conflict with tree
                orig_label = orig_label.replace(")", "_")
                orig_label = orig_label.replace("(", "_")
                orig_label = orig_label.replace(",", "_")
                orig_label = orig_label.replace(";", "_")   
 
		orig_label = orig_label + ':' #add : at end of label

     		raxml_file = raxml_file.replace(gene_label, orig_label)
                index = index + 1

f.close()

out_filename = "bestTree." + file_name + "_mode_" + args.mode + ".renamed"
out_file = open(out_filename, 'w')
out_file.write(raxml_file)
out_file.close()



#rename the tree Branchlabels tree with original names
print "\n\nRenaming Branch labels output tree to use original names"

#read the raxml file into a variable raxml_file
#cmd = 'cat RAxml_bestTree.' + args.input_file.name
#r = os.popen(cmd)
fn = 'RAxML_bipartitionsBranchLabels.' + file_name

try:
	r = open(fn, 'r')

	raxml_file = r.read() #read entire file into variable

	#open original input file
	f = open(args.input_file.name, 'rU')
	index = 0
	for line in f:
		if line.startswith('>'):
			gene_label = 'g_' + str(index) + ':'
			line_list = line.split()
  			orig_label = line_list[0] #the first element
 			orig_label.strip() #remove whitespace and endline
			orig_label = orig_label.replace(">", "") #remove >
			#replace any illegal characters in id
			orig_label = orig_label.replace(":", "_") #remove : it will conflict with tree
                	orig_label = orig_label.replace(")", "_")
                	orig_label = orig_label.replace("(", "_")
                	orig_label = orig_label.replace(",", "_")
                	orig_label = orig_label.replace(";", "_")

			orig_label = orig_label + ':' #add : at end of label

     			raxml_file = raxml_file.replace(gene_label, orig_label)
                	index = index + 1

	f.close()

	out_filename = "bipartitionsBranchLabels." + file_name + "_mode_" + args.mode + ".renamed"
	out_file = open(out_filename, 'w')
	out_file.write(raxml_file)
	out_file.close()

except IOError:
	print "Error.. raxml did not make file " + fn
        #sys.exit(1)


#rename the tree RAxML_bipartitions tree with original names
print "\n\nRenaming Branch labels RAxML_bipartitions output tree to use original names"

#read the raxml file into a variable raxml_file
#cmd = 'cat RAxml_bestTree.' + args.input_file.name
#r = os.popen(cmd)
fn = 'RAxML_bipartitions.' + file_name

try:
	r = open(fn, 'r')

	raxml_file = r.read() #read entire file into variable

	#open original input file
	f = open(args.input_file.name, 'rU')
	index = 0
	for line in f:
		if line.startswith('>'):
			gene_label = 'g_' + str(index) + ':'
			line_list = line.split()
  			orig_label = line_list[0] #the first element
 			orig_label.strip() #remove whitespace and endline
			orig_label = orig_label.replace(">", "") #remove >
			#replace any illegal characters in id
			orig_label = orig_label.replace(":", "_") #remove : it will conflict with tree
                	orig_label = orig_label.replace(")", "_")
                	orig_label = orig_label.replace("(", "_")
                	orig_label = orig_label.replace(",", "_")
                	orig_label = orig_label.replace(";", "_")

			orig_label = orig_label + ':' #add : at end of label

     			raxml_file = raxml_file.replace(gene_label, orig_label)
                	index = index + 1

	f.close()

	out_filename = "bipartitions." + file_name + "_mode_" + args.mode + ".renamed"
	out_file = open(out_filename, 'w')
	out_file.write(raxml_file)
	out_file.close()

except IOError:
	print "Error.. raxml did not make file " + fn
        #sys.exit(1)




#Remove intermediate files no longer needed
print "--removing unneeded files"

#cmd = 'rm -f RAxML_bestTree.' + args.input_file.name
#retvalue = os.system(cmd) #returns 0 if no error in command

if DELETE_FILES == "TRUE":
	os.system('rm -f ' + file_name + '.rename')
	os.system('rm -f ' + file_name + '.al')
	os.system('rm -f ' + file_name + '.tmp')
	os.system('rm -f ' + file_name + '.tmp.fst')
	os.system('rm -f ' + file_name + '.phy')
	os.system('rm -f ' + file_name + '.phy.reduced')
	os.system('rm -f ' + file_name + '.model')

	os.system('rm -f ' + 'RAxML_bestTree.' + file_name)
	os.system('rm -f ' + 'RAxML_bipartitionsBranchLabels.' + file_name)
	os.system('rm -f ' + 'RAxML_bipartitions.' + file_name)
	os.system('rm -f ' + 'RAxML_bootstrap.' + file_name)
	os.system('rm -f ' + 'RAxML_info.' + file_name)

	os.system('rm -rf snapshot')




print "\n\nScript finished..."
