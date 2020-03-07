#!/usr/bin/env bash

REFERENCE_ASSEMBLER="../../tools/Assembler.sh"
RED='\033[0;31m'
NC='\033[0m' # No Color
result=0

for filename in */*.asm; do
    $REFERENCE_ASSEMBLER $filename > /dev/null
    expected_output=${filename%asm}hack
    python assembler.py $filename tmp.hack
    diff $expected_output tmp.hack > /dev/null
    if [[ $? -ne 0 ]]; then
        echo -e ${RED}${filename} ": KO"${NC}
        result=1
    else
        echo ${filename} ": OK"
    fi
    rm $expected_output
done

rm tmp.hack

if [[ $result -eq 0 ]]; then
    echo "All tests passed!"
else
    echo "Some diffs were found"
fi

exit $result
