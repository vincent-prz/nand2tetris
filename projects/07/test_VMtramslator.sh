#!/usr/bin/env bash

CPU_EMULATOR="../../tools/CPUEmulator.sh"
RED='\033[0;31m'
NC='\033[0m' # No Color
nb_failures=0

for filename in */*/*.tst; do
    if [[ ! $filename =~ VME ]]; then # ignore VME files
        python VMtranslator.py ${filename%tst}vm # generates output vm file
        $CPU_EMULATOR $filename > /dev/null
        if [[ $? -ne 0 ]]; then
            echo -e ${RED}${filename} ": KO"${NC}
            nb_failures=$((nb_failures + 1))
        else
            echo ${filename} ": OK"
        fi
        output_filename=${filename%tst}asm
	if [[ $1 == "clean" ]]; then
            rm $output_filename
	fi
    fi
done

if [[ $nb_failures -eq 0 ]]; then
    echo "All tests passed!"
else
    echo ${nb_failures} "failures."
fi

exit $nb_failures
