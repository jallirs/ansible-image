#!/bin/bash

if [[ "$(python -c 'import sys; print(sys.version_info[0])')" == "2" ]]; then
    TMP_VIRTUALENV="virtualenv"
else
    TMP_VIRTUALENV="python3 -m virtualenv --python=python3.6"
fi

# This little dance allows us to install the latest pip and setuptools
# without get_pip.py or the python-pip package (in epel on centos)
if (( $(${TMP_VIRTUALENV} --version | cut -d. -f1) >= 14 )); then
    SETUPTOOLS="--no-setuptools"
fi

# virtualenv 16.4.0 fixed symlink handling. The interaction of the new
# corrected behavior with legacy bugs in packaged virtualenv releases in
# distributions means we need to hold on to the pip bootstrap installation
# chain to preserve symlinks. As distributions upgrade their default
# installations we may not need this workaround in the future
PIPBOOTSTRAP=/var/lib/pipbootstrap

# Create the boostrap environment so we can get pip from virtualenv
${TMP_VIRTUALENV} --extra-search-dir=/tmp/wheels ${SETUPTOOLS} ${PIPBOOTSTRAP}
source ${PIPBOOTSTRAP}/bin/activate

# Upgrade to the latest version of virtualenv
bash -c "source ${PIPBOOTSTRAP}/bin/activate; pip3 install --upgrade ${PIP_ARGS} virtualenv"

# Forget the cached locations of python binaries
hash -r

# Create the virtualenv with the updated toolchain for openstack service
mkdir -p /var/lib/ansible-venv
chown "$(whoami)" /var/lib/ansible-venv
virtualenv --python=python3.6 /var/lib/ansible-venv

# Deactivate the old bootstrap virtualenv and switch to the new one
deactivate
source /var/lib/ansible-venv/bin/activate

# Install python packages not included as rpms
pip3 install --upgrade ${PIP_ARGS} $@

deactivate
rm /var/lib/ansible-venv/bin/python
cp /var/lib/ansible-venv/bin/python3 /var/lib/ansible-venv/bin/python
echo "export PATH=/var/lib/ansible-venv/bin:\${PATH}" >> ${HOME}/.bash_profile
source ${HOME}/.bash_profile
sh -c "echo PATH=/var/lib/ansible-venv/bin:\$PATH >> /etc/environment"
