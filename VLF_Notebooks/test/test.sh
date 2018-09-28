#!/usr/bin/env bash
MADGRAPH=madgraph
if [ "$1" ];then
    source "$1"
fi
if [ ! "which root" ]; then
    echo "ERROR: ROOT not yet configured"
    echo "Try $0 [thisroot.sh PATH]"
    tr=$(locate bin/thisroot.sh | head -n1)
    if [ "tr" ];then
	echo "May be:"
	echo "$0  $tr"
    fi
    exit
fi

echo "========TEST =================="
echo "ROOT OK at: $(which root)"

#clean
if [ -d ./BP_750_110_vs_lambdaL ];then
    rm -rf ./BP_750_110_vs_lambdaL
fi

echo "========TEST =================="
echo "Test madgraph"
cd ../$MADGRAPH
time ./bin/mg5_aMC ../test/test.txt
if [ -d ../test/BP_750_110_vs_lambdaL/Events/run_01 ];then
    echo "madGRAPH seem OK: ../test/BP_750_110_vs_lambdaL/Events/run_01 generated"
fi
cd ../test
echo "========  NEXT TEST =================="
echo "<Enter> to test Pythia and Delphes"
read 
cd BP_750_110_vs_lambdaL
time ./bin/madevent ../pythia.txt
if [ -f "$(ls Events/run_01/*.root 2>/dev/null | head -n1)" ];then
    echo "========TEST =================="
    echo "Pythia and Delphes is OK: $(ls Events/run_01/*.root | head -n1)"
fi

    

