'''This script is designed to iterate through a directory containing output for fMRIPrep (provided by the user in the command line),
and delete files that won't be needed. It was written on the assumption that temporary 'working directory' files, final output files,
and any log files are all located within this directory in some form, although the specific folder naming convention does not matter. 

PLEASE NOTE: There may be files that are important to you that we have not specified as needed, these will be deleted. If you are
concerned about irrevocably deleting important files, be sure to update the code below, including the 'target strings' we'll keep,
and the subfolders that will be deleted regardless.'''

#Imports relevant modules.
import os
import sys
import shutil

#Checks whether the fmriprep_dir argument is provided.
if len(sys.argv) < 2:
    print("Please provide the fMRIPrep directory as a command-line argument.")
    sys.exit()

#Retrieves the fmriprep_dir from the command-line argument.
fmriprep_dir = sys.argv[1]

#Checks whether this fMRIPrep directory exists. If not, a warning is printed to the user and the script quits.
if not os.path.exists(fmriprep_dir):
	print("The specified fMRIPrep directory ({}) does not exist.".format(fmriprep_dir))
	sys.exit()

#A list of 'target strings' that we'll use to index files we want to keep. This will effectively capture preprocessed
#structural and functional images in any output sapce requested, corresponding brain masks, confounds generated by fMRIPrep,
#the HTML output report for each subject, the HTML and SVG images used to populate the output report, and the estimated
#carbon emissions file generated by CodeCarbon.
target_strings = ['preproc', 'brain_mask', 'confounds', 'html', 'svg', 'emissions']

#Before proceeding, the script will require the user to confirm that they are happy to proceed with deletion.
#If 'Y' is given, the script will proceed. If 'N' is given, it'll quit.
print("WARNING, you are about to delete all files within '{}' that do not contain one of the following strings:".format(fmriprep_dir))
for target in target_strings:
	print(target)
print("This should include ALL files generated in the 'working directory', as well as any in the 'fsaverage' subfolder")
while True:
	method = input('Do you want to continue? (Y/N)').lower()
	if method == 'n':
		print("Exiting...")
		sys.exit()
	elif method == 'y':
		print("Proceeding...")		
		break
	else:
		print("***Please type either 'Y' to proceed and delete non-target files, or 'N' to quit.  ***")

#Uses the 'walk' function to iterate over folders and files in the fMRIPrep directory.
for root, dirs, files in os.walk(fmriprep_dir, topdown = False):
	for filename in files:
		file_path = os.path.join(root, filename)

		#Checks whether any of the target strings exists in the name of the file being iterated over. If not,
		#or if the string 'index' is present (this is the one unneeded file that slips through the cracks
		#when looking for target strings), the file is deleted.
		if not any(target in filename for target in target_strings) or 'index' in filename:
			print("Deleting file:", file_path)
			os.remove(file_path)

	#Iterates over each folder in the fMRIPrep directory.
	for dir_name in dirs:
		subdirectory = os.path.join(root, dir_name)

		#If a folder is totally empty, it's removed.
		if len(os.listdir(subdirectory)) == 0:
			os.rmdir(subdirectory)
			print("Deleted empty directory:", subdirectory)

		#A folder is also removed if it contains the string 'single_subject' or 'fsaverage'.
		#These are folders that we don't need, but several files within them slip through the cracks
		#when searching for our target strings.
		elif 'single_subject' in subdirectory or 'fsaverage' in subdirectory:
			shutil.rmtree(subdirectory)
