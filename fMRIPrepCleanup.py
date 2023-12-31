#Imports relevant modules.
from __future__ import print_function
import os
import sys
import shutil
import sys

#ANSI escape sequences for text formatting
if sys.version_info[0] < 3:
	BOLD = '\x1b[1m'
	RED = '\x1b[91m'
	GREEN = '\x1b[92m'
	RESET = '\x1b[0m'
else:
	BOLD = '\033[1m'
	RED = '\033[91m'
	GREEN = '\033[92m'
	RESET = '\033[0m'

#A list of 'target strings' that we'll use to index files we want to keep. This will effectively capture preprocessed
#structural and functional images in any output sapce requested, corresponding brain masks, confounds generated by fMRIPrep,
#the HTML output report for each subject, the HTML and SVG images used to populate the output report, and the estimated
#carbon emissions file generated by CodeCarbon.
target_strings = ['preproc', 'brain_mask', 'confounds', 'html', 'svg', 'emissions']

#This function will be used at several points to verify if the user is happy to continue executing the script. Users must
#type 'Y' to continue, or 'N' to exit the script.
def continue_check():
	while True:
		if sys.version_info[0] < 3:
			choice = raw_input('Do you want to continue? (Y/N)').lower()
		else:
			choice = input('Do you want to continue? (Y/N)').lower()
		if choice == 'n' or choice == 'no':
			print("Exiting...")
			sys.exit()
		elif choice == 'y' or choice == 'yes':
			print("Proceeding...")
			break
		else:
			print("***Please type either 'Y' to proceed and delete non-target files, or 'N' to quit.  ***")



# ------------------------------------- COMMAND LINE ARGUMENTS -------------------------------------



#Collects arguments given by the user in the command line. Defines list of arguments that need to be present, and optional arguments.
args = sys.argv[1:]
arg_dict = {}
expected_args = ['-dir', '-method']
optional_args = ['-also_keep', '-also_delete', '-out_path']

#Checks that the user has provided the correct number of arguments and all expected arguments are present, and quits if not.
if len(args) < 4 or any(arg not in args for arg in expected_args):
	print("Incorrect usage. Usage should be at least: fMRIPrepCleanup.py -dir <fMRIPrep directory> -method <'sim_link'/'sim_copy'/'delete'>")
	print("Optional arguments include -also_keep <strings seperated by commas, no spaces> and -also_delete <strings seperated by commas, no spaces>")
	sys.exit(1)

#Parse the command line arguments.
for i in range(0, len(args), 2):
	arg = args[i]
	value = args[i+1]
	if arg not in expected_args and arg not in optional_args:
		print("Invalid argument: {}".format(arg))
		sys.exit(1)

	#For the also_delete and also_keep arguments (if present), checks that strings have been provided in the correct form.
	if 'also' in arg:
		if ' ' in value:
			print("Incorrect usage: For {}, please provide comma seperated strings without spaces.".format(arg))
			print("E.g., {} string1,string2,string3".format(arg))
			sys.exit(1)

	arg_dict[arg] = value

#Saves command line arguments as variables that will be used below. First, checks whether fmriprep_dir exists.
fmriprep_dir = arg_dict['-dir']
if not os.path.exists(fmriprep_dir):
	print("The specified fMRIPrep directory ({}) cannot be found or does not exist.".format(fmriprep_dir))
	sys.exit()

#Method is saved as insensitive to case, to be more flexible to the user.
method = arg_dict['-method'].lower()

#If the user has provided an outpuit path...
if '-out_path' in arg_dict:
	out_path = arg_dict['-out_path']

	#This is irrelevant for deletion mode, so the script quits if both conditions are met, the user may intended simulation mode.
	if method == 'delete':
		print("Optional output paths are not valid in DELETION mode, given that no files are linked or copied.")
		print("If intending to engage SIMULTION mode, please ensure to correctly specify -method as sim_copy or sim_link.")
		sys.exit()

	#If the output path doesn't exist, the user is warned and the script quits.
	elif not os.path.exists(out_path):
		print("The specified output directory ({}) cannot be found or does not exist.".format(out_path))
		print("Please provided an existing directory, a simulation output folder will then be created within it.")
		sys.exit()

#If the user has provided an -also_delete argument, a list of the strings to be deleted is pulled out.
#Whether or not it's provided, a list is created with the string 'index' contained, given that we'll want
#to delete this by default, but it'll slip through the cracks otherwise.
if '-also_delete' in arg_dict:
	also_delete = arg_dict['-also_delete'].split(',')
	also_delete.append('index')
else:
	also_delete = ['index']

#If the user has provided an -also_keep argument, a list of strings to be kept is pulled out.
if '-also_keep' in arg_dict:
	also_keep = arg_dict['-also_keep'].split(',')

	#Iterates over these strings.
	for keep_string in also_keep:

		#If the user has provided both -also_keep and -also_delete...
		if '-also_delete' in arg_dict:
			for del_string in also_delete:

				#Any strings that occur within an item in both lists are removed from also_delete, to be careful.
				if del_string in keep_string or keep_string in del_string:
					also_delete.remove(del_string)

#Again, if the user has provided -also_delete...
if '-also_delete' in arg_dict:
	for target in target_strings:
		for del_string in also_delete:

			#Targets are removed from our master list if they also occur within also_delete.
			#Overall, this means that to_keep trumps to_delete, which in turn trumps our default settings.
			if del_string in target:
				target_strings.remove(target)



# ---------------------------------------- USER SANITY CHECK ---------------------------------------



#Before proceeding, the script will require the user to confirm that they are happy to proceed with either
#simulation (symbolic links or copies of files to be kept will be made) or deletion (non-target files will be deleted).
print()
print("---------------------------------- Welcome to fMRIPrepCleanup! ----------------------------------")
print()

#If in in simulation mode, the warnings printed will depend on whether files are being linked or copied. These messages are also
#conditional on whether the user has specified an output directory for the simulated file structure (current working directory is used if not).
if method == 'sim_link':
	if '-out_path' in arg_dict:
		print("You have selected SIMULATION LINK mode. Symbolic links will be used to create a replica of how your fMRIPrep data would look after cleanup (deleting), within your provided output directory {}{}'{}'{}.".format(BOLD, GREEN, out_path, RESET))
	else:
		print("You have selected SIMULATION LINK mode. Symbolic links will be used to create a replica of how your fMRIPrep data would look after cleanup (deleting), in your current working directory.")
	print("This will include the creation of 'Deleted' and 'Retained' folders, so you can check that you'd keep what you'd expect to keep, and nothing important would be deleted.")	
	print("No actual files will be lost or moved. This will simulate deleting all files within {}{}'{}'{} that do not contain one of the following strings:".format(BOLD, RED, fmriprep_dir, RESET))

elif method == 'sim_copy':
	if '-out_path' in arg_dict:
		print("You have selected SIMULATION COPY mode. Target files will be copied to create a replica of how your fMRIPrep data would look after cleanup (deleting), within your provided output directory {}{}'{}'{}.".format(BOLD, GREEN, out_path, RESET))
	else:
		print("You have selected SIMULATION COPY mode. Target files will be copied to create a replica of how your fMRIPrep data would look after cleanup (deleting), in your current working directory.")
	print("This will include the creation of 'Deleted' and 'Retained' folders, so you can check that you'd keep what you'd expect to keep, and nothing important would be deleted. Please be sure to delete the copied directory after you've checked this, to avoid using unnecessary storage.")	
	print("Files in your original directory will not be impacted. This will simulate deleting all files within {}{}'{}'{} that do not contain one of the following strings:".format(BOLD, RED, fmriprep_dir, RESET))

#If deletion mode is selected, the warning of what is about to happen is clearly printed.
elif method == 'delete':
	print("{}{}WARNING, you have selected DELETION mode{}, and are about to delete all files within {}{}'{}'{} that do not contain one of the following strings:".format(BOLD, RED, RESET, BOLD, RED, fmriprep_dir, RESET))

#Quits if the mode provided is not a valid one.
else:
	print("Invalid 'method' provided. In the command line, please provide a -method that is either 'sim_link' (simulation link mode), 'sim_copy' (simulation copy mode), or 'delete' (deletion mode)")
	sys.exit()

#Prints out each target string that is kept by default.
for target in target_strings:
	print("- '{}'".format(target))
print("This should include ALL files generated in the 'working directory', as well as any in the 'fsaverage' subfolder.")

#Again, another final warning is printed in deletion mode.
if method == 'delete':
	print("{}{}Please carefully check that you have selected the correct path, and that all folders and files contained are output from fMRIPrep. {}".format(RED, BOLD, RESET))

#If the user has specified other files to be kept or deleted, these are also printed with a clear warning for the also_delete strings.
if '-also_keep' in arg_dict:
	print("You have additionally selected to {}{}KEEP{} (or simulate keeping) any files with the following strings in their names:".format(GREEN, BOLD, RESET))
	for file_string in also_keep:
		print("- '{}'".format(file_string))
		target_strings.append(file_string)

if '-also_delete' in arg_dict:
	if len(also_delete) > 1:
		print("You have additionally selected to {}{}DELETE{} (or simulate deleting) any files with the following strings in their names:".format(RED, BOLD, RESET))
		for file_string in also_delete[:-1]:
			print("- '{}'".format(file_string))
		if method == 'delete':
			print("{}{}Please check these strings VERY carefully before proceeding, to prevent accidental deletion of important files.{}".format(RED, BOLD, RESET))

#Using the above function, the user is asked if they want to continue.
continue_check()

#From here, any also_keep strings are integrated with our target string list, for the sake of simplicity.
if '-also_keep' in arg_dict:
	for keep_string in also_keep:		
		target_strings.append(keep_string)



# ----------------------------------------- FMRIPREP FOLDER VALIDATION ----------------------------------------



#We provide a very light version of validation, to check whether the folder provided looks roughly how we'd expect it to.
#To start, these statements are set at FALSE by default.
sub_folder_found = False
preproc_found = False

#Iterates through everything in the fmriprep_dir
for root, dirs, files in os.walk(fmriprep_dir):
	for dir_name in dirs:

		#Looks for any folder containing the string 'sub', would suggest the output folder of a subject.
		#If found, the relevant variable above is set to TRUE.
		if 'sub-' in dir_name:
			sub_folder_found = True

			#Looks at everything within this folder, and searches for the string 'preproc', would suggest
			#a preprocessed file. If found, the relevant variable is set to TRUE and the loop breaks.
			for root2, dirs2, files2 in os.walk(os.path.join(root, dir_name)):
				for file_name in files2:
					if 'preproc' in file_name:
						preproc_found = True
					if preproc_found:
						break
		if preproc_found:
			break

#Depending on whether one or both of these conditions have been met, messages are printed to the user and they are asked if they want to continue. If we haven't
#found both expected strings, the user is asked if they want to continue. This will catch cases where typical fMRIPrep output is present, but won't account
#for cases where things other than fMRIPrep output is contained within the specified folder - this stuff would still be deleted.
if sub_folder_found and preproc_found:
	print("fMRIPrep folder appears to contain fMIRPrep output...")
elif sub_folder_found:
	print("This does not appear to be an fMRIPrep output folder. While it contains folders with the string 'sub' in their name, no files within contain the string 'preproc' (preprocessed files).")
	print("Please carefully check your provided fMRIPrep directory ({}{}{}{}) before proceeding.".format(BOLD, RED, fmriprep_dir, RESET))
	continue_check()
else:
	print("This does not appear to be an fMRIPrep output folder, as it does not contain any folders with the string 'sub-' in their name.")
	print("Please carefully check your provided fMRIPrep directory ({}{}{}{}) before proceeding.".format(BOLD, RED, fmriprep_dir, RESET))
	continue_check()

# ----------------------------------------- SIMULATION MODE ----------------------------------------



#If simulation mode is selected...
if 'sim' in method:

	#Create a new folder for symbolic links or copies. If the folder already exists, it's deleted. The exact path depends on whether copy or
	#link mode has been selected, as well as whether an output path has been specified. If not, current working directory is used.
	if '-out_path' in arg_dict:
		sim_dir = os.path.join(out_path, 'fMRIPrepCleanup_Simulation_{}'.format(method[-4:]))
	else:
		sim_dir = os.path.join(os.getcwd(), 'fMRIPrepCleanup_Simulation_{}'.format(method[-4:]))

	if not os.path.exists(sim_dir):
		os.mkdir(sim_dir)
		print("Simulation folder created:", sim_dir)

	else:
		print("Emptying and replacing simulation folder...:", sim_dir)
		shutil.rmtree(sim_dir)
		os.mkdir(sim_dir)

	#For all cases below, the specific 'simulation path' will be defined depending on whether a file is being targetted for
	#retention or deletion. Within the generated simulation directory, this will produce two folders allowing users to see
	#what the script would and would not delete in their specified directory.

	#Uses the 'walk' function to iterate over folders and files in the fMRIPrep directory.
	for root, dirs, files in os.walk(fmriprep_dir, topdown = False):
		for filename in files:
			file_path = os.path.join(root, filename)

			#Certain files are skipped here given that they'll slip through the cracks when looking for target strings.
			#However, we do first look through these folders if the to_keep command has been provided, to make sure these strings
			#are retained in any case.
			if 'single_subject' in file_path or 'fsaverage' in file_path:

				if '-also_keep' in arg_dict:
					if any(keep_string in filename for keep_string in also_keep):
						sim_path = os.path.join(sim_dir, 'Retained', os.path.relpath(file_path, fmriprep_dir))
					else:
						sim_path = os.path.join(sim_dir, 'Deleted', os.path.relpath(file_path, fmriprep_dir))

				else:
					sim_path = os.path.join(sim_dir, 'Deleted', os.path.relpath(file_path, fmriprep_dir))

			#For any files that contain one of our target strings (and aren't specified in also_delete), a symbolic link
			#or copy will be made of them in the 'Retained' folder using their relative path within the fMRIPrep directory.
			elif any(target in filename for target in target_strings) and not any(del_string in filename for del_string in also_delete):
			
				sim_path = os.path.join(sim_dir, 'Retained', os.path.relpath(file_path, fmriprep_dir))

			#All other files are placed into our simulated 'Deleted' folder.
			else:
				sim_path = os.path.join(sim_dir, 'Deleted', os.path.relpath(file_path, fmriprep_dir))

			#The simulation path is created if it doesn't exist, and the relevant copy/link is then created. By this point,
			#every file in the original directory should have a simulation path defined.
			if not os.path.exists(os.path.dirname(sim_path)):
				os.makedirs(os.path.dirname(sim_path))

			if 'link' in method:
				os.symlink(file_path, sim_path)
				print("Created symbolic link:", sim_path)
			elif 'copy' in method:
				shutil.copy(file_path, sim_path)
				print("Copied file:", sim_path)


# ------------------------------------------ DELETION MODE -----------------------------------------


#If deletion mode is selected...
elif method == 'delete':

	#Uses the 'walk' function to iterate over folders and files in the fMRIPrep directory.
	for root, dirs, files in os.walk(fmriprep_dir, topdown = False):
		for filename in files:
			file_path = os.path.join(root, filename)

			#If there aren't any target strings in a given filename (or if they're caught by any 'also_delete' strings), they are deleted.
			if not any(target in filename for target in target_strings) or any(del_string in filename for del_string in also_delete):

				print("Deleting file:", file_path)
				os.remove(file_path)

		#Iterates over each folder in the fMRIPrep directory.
		for dir_name in dirs:
			subdirectory = os.path.join(root, dir_name)

			#A folder is removed if it contains the string 'single_subject' or 'fsaverage'. These are folders that we don't need, but
			#several files within them slip through the cracks when searching for our target strings. These are deleted outright if also_keep
			#has not been specified. If it has been, we double check wheter any also_keep string are present in these filenames before deleting.
			if 'single_subject' in subdirectory or 'fsaverage' in subdirectory:

				if '-also_keep' not in arg_dict:
					shutil.rmtree(subdirectory)
					continue

				else:

					#Iterates through these specific folders to look for also_keep strings...
					for root2, dirs2, files2 in os.walk(subdirectory, topdown = False):
						for filename2 in files2:
							file_path2 = os.path.join(root2, filename2)

							if not any(keep_string in filename2 for keep_string in also_keep):
								print("Deleting file:", file_path2)								
								os.remove(file_path2)

		#Iterates over each folder in the fMRIPrep directory.
		for dir_name in dirs:
			subdirectory = os.path.join(root, dir_name)

			try:
				#If a folder is totally empty, it's removed.
				if len(os.listdir(subdirectory)) == 0:
					os.rmdir(subdirectory)
					print("Deleted empty directory:", subdirectory)

			#Ignores any cases where the script is asked to delete a folder that does not exist.
			except OSError:
				continue
