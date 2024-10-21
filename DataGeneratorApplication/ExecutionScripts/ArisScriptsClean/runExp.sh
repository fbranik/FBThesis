wsSizeMultiplierX=(1 2)
wsSizeMultiplierY=(1 5)

problemSizeX=(2)
problemSizeY=(2)

Px=(4)
Py=(4)

NumPr=(16)

for mulIdx in "${!wsSizeMultiplierX[@]}"; do
  for iVersion in CompBoundJacobi; do
    for idx in "${!problemSizeX[@]}"; do
      for iSize in 131072; do
        for iNumMessages in 4; do
          for iIters in 16; do
            declare -i xSize="(${problemSizeX[$idx]} * ${wsSizeMultiplierX[$mulIdx]})"
            declare -i ySize="(${problemSizeY[$idx]} * ${wsSizeMultiplierY[$mulIdx]})"

            echo " "${NumPr[$idx]}" --map-by node ./$iVersion "$xSize" "$ySize" \
            "${Px[$idx]}" "${Py[$idx]}" $iSize $iNumMessages $iIters 4"
          done
        done
      done
    done
  done
done
