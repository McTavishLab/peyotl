#!/bin/sh
# Checks out mini_* repos into 
#   peyotl/test/data/template_mini_par
d="$(dirname $0)"
cd "$d"
if test -d peyotl/test/data/template_mini_par
then
    echo peyotl/test/data/template_mini_par exists
    exit 1
fi
set -x
mkdir peyotl/test/data/template_mini_par || exit
cd peyotl/test/data/template_mini_par || exit
if test -d mini_phyl
then
    echo "mini_phyl exists"
else
    git clone https://github.com/mtholder/mini_phyl.git || exit
fi
if test -d mini_system
then
    echo "mini_system exists"
else
    git clone https://github.com/mtholder/mini_system.git || exit
fi
if test -d mini_collections
then
    echo "mini_collections exists"
else
    echo "fetching mini_collections..."
    git clone https://github.com/jimallman/mini_collections.git || exit
    echo "got mini_collections!"
fi
cd .. || exit
cp -r template_mini_par mini_par
