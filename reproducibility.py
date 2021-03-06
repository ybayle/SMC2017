# -*- coding: utf-8 -*-
#!/usr/bin/python
#
# Author    Yann Bayle
# E-mail    bayle.yann@live.fr
# License   MIT
# Created   19/01/2017
# Updated   08/03/2017
# Version   1.0.0
#

"""
Description of reproducibility.py
=================================

Launch source code file in order to reproduce results of the article

:Example:

python reproducibility.py

"""

import os
import sys
from statistics import mean, stdev
from sklearn.metrics import precision_recall_curve, precision_score, recall_score, classification_report, f1_score, accuracy_score
sys.path.insert(0, './src/')
import isrc
import vqmm
import stats
import utils
import bayle
import ghosal
import shutil
import svmbff
import classify
import subprocess

def clean_filenames(tracks_dir = "tracks/"):
    """Description of clean_filenames
    """
    for old_fn in os.listdir(tracks_dir):
        new_fn = old_fn
        new_fn = new_fn.replace(" ", "_")
        new_fn = new_fn.replace(",", "_")
        new_fn = new_fn.replace("(", "_")
        new_fn = new_fn.replace(")", "_")
        os.rename(tracks_dir + old_fn, tracks_dir + new_fn)

def yaafe_feat_extraction(dir_tracks):
    """Description of yaafe_feat_extraction
    yaafe.py -r 22050 -f "mfcc: MFCC blockSize=2048 stepSize=1024" audio_fn.txt
    """
    utils.print_success("YAAFE features extraction (approx. 8 minutes)")
    
    # Assert Python version
    if sys.version_info.major != 2:
        utils.print_error("Yaafe needs Python 2 environment")
    
    # Assert folder exists
    dir_tracks = utils.abs_path_dir(dir_tracks)    
    
    filelist = os.listdir(dir_tracks)
    dir_feat = utils.create_dir(utils.create_dir("features") + "database1")
    # dir_tmp = utils.create_dir("tmp")
    # dir_yaafe = utils.create_dir(dir_tmp + "yaafe")
    # fn_filelist = dir_yaafe + "filelist.txt"
    dir_current = os.getcwd()
    os.chdir(dir_tracks)
    yaafe_cmd = 'yaafe -r 22050 -f "mfcc: MFCC blockSize=2048 stepSize=1024" '
    yaafe_cmd += "--resample -b " + dir_feat + " "
    for index, filen in enumerate(filelist):
        utils.print_progress_start(str(index+1) + "/" + str(len(filelist)) + " " + filen)
        os.system(yaafe_cmd + filen + "> /dev/null 2>&1")
    utils.print_progress_end()
    os.chdir(dir_current)

def read_item_tag(filename):
    """Description of read_file

    example line:
    filename,tag
    """

    filename = utils.abs_path_file(filename)
    groundtruths = {}
    with open(filename, "r") as filep:
        for row in filep:
            line = row.split(",")
            groundtruths[line[0]] = line[1][:-1]
    return groundtruths

def results_experiment_2(algo_name, predictions, groundtruths):
    instru_gts = []
    instru_pred = []
    song_gts = []
    song_pred = []
    song_tmp_gts = []
    song_tmp_pred = []
    cpt = 0
    nb_instru = groundtruths.count("i")
    for index, tag in enumerate(groundtruths):
        if "i" in groundtruths[index]:
            instru_gts.append("i")
            instru_pred.append(predictions[index])
        else:
            if cpt == nb_instru:
                song_gts.append(song_tmp_gts)
                song_pred.append(song_tmp_pred)
                song_tmp_gts = []
                song_tmp_pred = []
                cpt = 0
            else:
                song_tmp_gts.append("s")
                song_tmp_pred.append(predictions[index])
                cpt += 1

    acc = []
    f1 = []
    for index, row in enumerate(song_gts):
        groundtruths = instru_gts + song_gts[index]
        predictions = instru_pred + song_pred[index]
        acc.append(accuracy_score(groundtruths, predictions))
        f1.append(f1_score(groundtruths, predictions, average='weighted'))

    print("Accuracy " + str(sum(acc)/float(len(acc))) + " ± " + str(stdev(acc)))
    print("F-Measure " + str(sum(f1)/float(len(f1))) + " ± " + str(stdev(f1)))
    dir_stats = utils.create_dir("stats/")
    with open(dir_stats + "table2_accuracy.csv", "a") as filep:
        filep.write(algo_name)
        for val in acc:
            filep.write("," + str(val))
        filep.write("\n")
    with open(dir_stats + "table2_f1.csv", "a") as filep:
        filep.write(algo_name)
        for val in f1:
            filep.write("," + str(val))
        filep.write("\n")

def experiment_2():
    utils.print_success("Experiment 2")
    groundtruths_file = "groundtruths/database2.csv"
    dir_pred = "predictions/"
    predictions_files = os.listdir(dir_pred)
    gts = read_item_tag(groundtruths_file)
    for pred_file in predictions_files:
        algo_name = pred_file.split("/")[-1][:-4]
        utils.print_info(algo_name)
        if "Ghosal" in algo_name:
            # Change threshold as RANSAC does not produces pred in [0;1] 
            threshold = 0.
        else:
            threshold = 0.5
        test_groundtruths = []
        predictions = []
        with open(dir_pred + pred_file, "r") as filep:
            for line in filep:
                row = line[:-1].split(",")
                isrc = row[0]
                if isrc in gts:
                    test_groundtruths.append(gts[isrc]) 
                    predictions.append("s" if float(row[1]) > threshold else "i")
        results_experiment_2(algo_name, predictions, test_groundtruths)

    algo_name = "Random"
    utils.print_info(algo_name)
    test_groundtruths = ["s", ] * test_groundtruths.count("s") + ["i", ] * test_groundtruths.count("i")
    predictions = ["s", "i", ] * int(len(test_groundtruths)/2)
    if len(test_groundtruths) % 2:
        predictions += ["s"]
    results_experiment_2(algo_name, predictions, test_groundtruths)

def experiment_3():
    utils.print_success("Experiment 3")
    groundtruths_file = "groundtruths/database2.csv"
    dir_pred = "predictions/"
    predictions_files = os.listdir(dir_pred)
    gts = read_item_tag(groundtruths_file)
    for pred_file in predictions_files:
        algo_name = pred_file.split("/")[-1][:-4]
        utils.print_info(algo_name)
        if "Ghosal" in algo_name:
            # Change threshold as RANSAC does not produces pred in [0;1] 
            threshold = 0.
        else:
            threshold = 0.5

        test_groundtruths = []
        predictions = []
        with open(dir_pred + pred_file, "r") as filep:
            for line in filep:
                row = line[:-1].split(",")
                isrc = row[0]
                if isrc in gts:
                    test_groundtruths.append(gts[isrc]) 
                    predictions.append("s" if float(row[1]) > threshold else "i")
        
        print("Accuracy : " + str(accuracy_score(test_groundtruths, predictions)))
        print("F-score  : " + str(f1_score(test_groundtruths, predictions, average='weighted')))
        print("Precision: " + str(precision_score(test_groundtruths, predictions, average=None)))
        print("Recall   : " + str(recall_score(test_groundtruths, predictions, average=None)))
        print("F-Measure " + str(f1_score(test_groundtruths, predictions, average=None)))

    utils.print_info("Random")
    test_groundtruths = ["s", ] * test_groundtruths.count("s") + ["i", ] * test_groundtruths.count("i")
    predictions = ["s", "i", ] * int(len(test_groundtruths)/2)
    if len(test_groundtruths) % 2:
        predictions += ["s"]
    print("Accuracy : " + str(accuracy_score(test_groundtruths, predictions)))
    print("F-score  : " + str(f1_score(test_groundtruths, predictions, average='weighted')))
    print("Precision: " + str(precision_score(test_groundtruths, predictions, average=None)))
    print("Recall   : " + str(recall_score(test_groundtruths, predictions, average=None)))
    print("F-Measure " + str(f1_score(test_groundtruths, predictions, average=None)))

def clean():
    """Description of clean.py
    
    Clean all files generated by reproduciblity.py
    
    ..todo::
    make available clean only if option selected

    """
    utils.print_success("Cleaning all files from previous launch")
    folders_list = ["results", "figures", "src/tmp", "src/__pycache__"]

    for folder in folders_list:
        if os.path.exists(folder) and os.path.isdir(folder):
            shutil.rmtree(folder)

    utils.print_success("Cleaning successful")

def main():
    """Description of main

    ..todo::

    # TODO
    # instead of using my own wav processed file, download and compute the one from scientists website 
    # ramona_url = "http://www.mathieuramona.com/uploads/Main/"
    # jamendo_db = ["jam_train_audio.tar.gz",
    #     "jam_valid_audio.tar.gz",
    #     "jam_test_audio.tar.gz"]
    # for dataset in jamendo_db:
    #     utils.print_warning("TODO")
    #     urllib.urlretrieve("http://www.example.com/songs/mp3.mp3", "mp3.mp3")
    # https://members.loria.fr/ALiutkus/kam/
    # https://infinit.io/_/XnG7U95
    # utils.print_info("For MedleyDB, you must request access to:")
    # utils.print_info("http://medleydb.weebly.com/downloads.html")
    # utils.print_error("Stopping programm, cannot continue further.")

    """

    # utils.print_success("Reproducible research (approx. 8h)")
    # # clean()

    # # Variables
    # groundtruths_filename = "groundtruths/database2.csv"
    # results_dir = utils.create_dir("figures/")
    
    # # Figure 1
    # isrc.plot_isrc_year_distribution(groundtruths_filename, results_dir)
    
    # # Figure 2
    # isrc.plot_isrc_country_repartition(groundtruths_filename, results_dir)

    # tracks_dir = "tracks/"
    # clean_filenames(tracks_dir)
    # svmbff.experiment_1()
    # subprocess.call(["./yaafe_wrapper.sh"]) # yaafe_feat_extraction("tracks")
    # ghosal.experiment_1()
    # svmbff_train = "features/svmbff_database1.arff"
    # svmbff_test = "features/svmbff_database2.arff"
    # dir_tmp = utils.create_dir(utils.create_dir("src/tmp") + "svmbff")
    # svmbff_out = dir_tmp + "SVMBFF.csv"
    # svmbff.run_kea(svmbff_train, svmbff_test, svmbff_out)
    # svmbff.experiment_2_3()
    # ghosal.experiments_2_3("src/tmp/ghosal/database1.csv")
    # vqmm.main() # vqmm.process_results()    
    # experiment_2()
    # bayle.main()
    # experiment_3()
    
    indir = "predictions"
    gts_file = "groundtruths/database2.csv"
    outdir = utils.create_dir("figures")
    classify.plot_roc(indir, gts_file, outdir)
    classify.plot_precision_recall(indir, gts_file, outdir)
    # stats.main() # make 10 replicates for expe1

    # todo
    # vqmm.py train() output to trash
    # Thibault Langlois vqmm reading filename without whole path

if __name__ == "__main__":
    main()
