#!/usr/bin/env bash

for keyword in REPETITIONS FORCES DIVISOR STRUCTURE MINDIST MAXDIST PIDMD_DIR BOX OUTDIR LOG QUEUE
do
  if [ -z ${!keyword} ]; then echo "$keyword is unset"; exit; fi
done

basedir=$(pwd)
mkdir -p ${OUTDIR}
for rep in $(seq 1 ${REPETITIONS})
do
  mkdir ${rep}
  cd ${rep}
  for i in $(seq 0 ${FORCES})
  do
    force=$(awk "BEGIN {print $i / $DIVISOR}") 
    mkdir ${force}
    cd ${force}
    echo "python ../../src/generate_python.py ../../$STRUCTURE/conf.json constraint $MINDIST $MAXDIST $force" >> ${basedir}/LOG
    python ../../src/generate_python.py -c ../../${STRUCTURE}/infiles/conf.json -o constraint -n ${MINDIST} -x ${MAXDIST} -s ${force} >> ${basedir}/LOG
    echo "$PIDMD_DIR/complex.linux -P $PIDMD_DIR/parameter/ -I ../../$STRUCTURE/infiles/in.pdb -D $BOX -p "${STRUCTURE}"_param -s "${STRUCTURE}"_state -C ../../infiles/stahar -c stahar"_ >> ${basedir}/LOG
    ${PIDMD_DIR}/complex.linux -P ${PIDMD_DIR}/parameter/ -I ../../${STRUCTURE}/infiles/in.pdb -D ${BOX} -p "$STRUCTURE"_param -s "$STRUCTURE"_state -C ../../infiles/stahar -c stahar_ 2>> ${basedir}/LOG
    cat constraint stahar_ > "$STRUCTURE"_cons
    cd ../
  done
  cd ../
  mv ${rep} ${OUTDIR}/
  cd ${OUTDIR}/${rep}
  for force in $(ls)
  do
    cd ${force}
    qsub -b y -cwd -N DMD_R_"$STRUCTURE" -q ${QUEUE} ${PIDMD_DIR}/pdmd.linux -i ${basedir}/inputs/relaxation.input -p "$STRUCTURE"_param -s "$STRUCTURE"_state -c "$STRUCTURE"_cons
    cd ../
  done
  cd ${basedir}/
done
