#!/usr/bin/env bash

CPU_EMULATOR="../../tools/CPUEmulator.sh"
RED='\033[0;31m'
NC='\033[0m' # No Color
nb_failures=0

test_folder=('ArrayTest' 'ExpressionLessSquare' 'Square')
TOKENIZER_EXE="python jack_analyzer.py --tokenize-only --output-folder test_folder"

mkdir test_folder

for test_folder in "${test_folder[@]}"; do
    for jack_file in $test_folder/*.jack; do
        $TOKENIZER_EXE $jack_file
        compare_file=${jack_file%.jack}T.xml
        var_with_no_name=test_folder${jack_file#$test_folder}
        output_file=${var_with_no_name%.jack}.xml
        diff -w $compare_file $output_file > /dev/null
        if [[ $? -ne 0 ]]; then
            echo -e ${RED}${jack_file} ": KO"${NC}
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
