#!/usr/bin/env bash

CPU_EMULATOR="../../tools/CPUEmulator.sh"
RED='\033[0;31m'
NC='\033[0m' # No Color
nb_failures=0

for parent_dir in *; do
    if [[ -d $parent_dir ]]; then
    for full_dir in ${parent_dir}/*; do
        base_dir=${full_dir#${parent_dir}/}
        test_file=${full_dir}/${base_dir}.tst
        if [[ $base_dir == "BasicLoop" ]] || [[ $base_dir == "FibonacciSeries" ]] || [[
            $base_dir == "SimpleFunction" ]]; then
            opts="no_bootstrap"
        else
            opts=""
        fi
        python VMtranslator.py ${full_dir} ${opts}
        $CPU_EMULATOR $test_file > /dev/null

        if [[ $? -ne 0 ]]; then
            echo -e ${RED}${full_dir} ": KO"${NC}
            nb_failures=$((nb_failures + 1))
        else
            echo ${full_dir} ": OK"
        fi
        output_file=${full_dir}/${base_dir}.asm
        if [[ $1 == "clean" ]]; then
                rm $output_file
        fi
    done
fi
done

if [[ $nb_failures -eq 0 ]]; then
    echo "All tests passed!"
else
    echo ${nb_failures} "failures."
fi

exit $nb_failures
