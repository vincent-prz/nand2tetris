#!/usr/bin/env bash

RED='\033[0;31m'
NC='\033[0m' # No Color
nb_failures=0

input_folders=('Seven' 'ConvertToBin' 'Square' 'Average' 'Pong')
ref_folder=test_refs

COMPILER_EXE="python src/jack_compiler.py --output-folder test_folder"

test_folder=test_folder
mkdir -p $test_folder

for folder in "${input_folders[@]}"; do
    $COMPILER_EXE $folder
    for jack_file in $folder/*.jack; do
        jack_file_wo_prefix=${jack_file#${folder}/}
        compare_file=${ref_folder}/${jack_file%.jack}.vm
        output_file=${test_folder}/${jack_file_wo_prefix%.jack}.vm
        diff -w $compare_file $output_file > /dev/null
        if [[ $? -ne 0 ]]; then
            echo -e ${RED}${folder}/${jack_file} ": KO"${NC}
            nb_failures=$((nb_failures + 1))
        else
            echo ${jack_file} ": OK"
        fi
    done
done

rm -rf test_folder

if [[ $nb_failures -eq 0 ]]; then
    echo "All tests passed!"
else
    echo ${nb_failures} "failures."
fi

exit $nb_failures
