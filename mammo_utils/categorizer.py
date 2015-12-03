# Contains utility functions for performing categorization

__all__ = ['get_nlp_result', 'categorize_file', 'random_select_n']

import csv
import os
import sys
import xml.etree.ElementTree as ET
from ibiis_nlp import process_entry

# Returns the
def get_nlp_result(acc_id):
    filename = '../nlp/' + acc_id + '_selen.txt'
    if os.path.isfile(filename):
        return ET.parse(filename).getroot()
    else:
        return None

# Helper for categorize_file
# write_cat(i, acc_id, text, out_data)
def _categorize_file_helper(input_file, categories, write_cat, out_data):
    with open(input_file, 'r') as csvfile:
        counter = 0
        reader = csv.reader(csvfile)

        for row in reader:
            if not row:
                break
            counter += 1
            # if counter % 1000 == 0:
            #   sys.stdout.write("\rEntry {}".format(counter))
            #   sys.stdout.flush()

            # Performs categorization
            has_cat = False
            for i in range(len(categories)):
                if categories[i][1](row[0], row[1].lower()):
                    write_cat(i, row[0], row[1], out_data)
                    has_cat = True
                    break

            # Entry falls into the "other" category
            if not has_cat:
                write_cat(-1, row[0], row[1], out_data)

# Performs file categorization.
# categories: a list of (<category name>, <categorizer function>) tuples
# dry_run: if set to true, displays how many entries would fall into each category,
#   but does not actually perform categorization
def categorize_file(input_file, out_path, categories, other_name='other', dry_run=False):
    print "Performing categorization on " + input_file

    if dry_run:
        def count_func(i, acc_id, text, out_arr):
            out_arr[i] += 1

        counts = [0] * (len(categories) + 1)
        _categorize_file_helper(input_file, categories, count_func, counts)
        for i in range(len(categories)):
            print "{}: {}".format(categories[i][0], counts[i])
        print "Other: {}".format(counts[-1])
    else:
        def write_to_file(i, acc_id, text, out_arr):
            out_arr[i].write('\"{}\",\"{}\"\n'.format(acc_id, text.replace('\"', '\"\"')))

        out_files = []
        for cat in categories:
            out_files.append(open('{}/{}.csv'.format(out_path, cat[0]), 'w+'))
        out_files.append(open('{}/{}.csv'.format(out_path, other_name), 'w+'))

        _categorize_file_helper(input_file, categories, write_to_file, out_files)
        for f in out_files:
            f.close()
        print "Categories saved to " + out_path


# This method has not been checked to work yet.
def random_select_n(inputs, nlp_path, mass_file_dir, no_mass_file_dir, n):
    entries = []
    mass_files, no_mass_files = [], []

    # Generate list of all accession_ids
    for i in range(len(inputs)):
        fname = inputs[i]
        idx = fname.rfind('/')
        if not idx == -1:
            fname = fname[idx + 1 : ]
        mass_files.append(open(mass_file_dir + '/' + fname, 'a+'))
        no_mass_files.append(open(no_mass_file_dir + '/' + fname, 'a+'))

        with open(inputs[i], 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if not row:
                    break
                entries.append((row[0], row[1], i))

    # Shuffle accession IDs
    random.shuffle(entries)
    mass_count = 0
    tot_count = 0

    print "Extracting {} masses from a total of {} entries".format(n, len(entries))

    # Write results
    for acc_id, text, src_idx in entries:
        if mass_count >= n:
            break
        tot_count += 1

        if process_entry(tot_count, acc_id, text, 0, nlp_path):
            if nlp_result_has_mass(nlp_path + '/' + acc_id + '_selen.txt'):
                mass_count += 1
                mass_files[src_idx].write('\"{}\",\"{}\"\n'.format(acc_id, text.replace('\"', '\"\"')))
            else:
                no_mass_files[src_idx].write('\"{}\",\"{}\"\n'.format(acc_id, text.replace('\"', '\"\"')))
        else:
            pass

    for f in mass_files:
        f.close()
    for f in no_mass_files:
        f.close()

    print "Masses: {} / {} entries".format(mass_count, tot_count)
