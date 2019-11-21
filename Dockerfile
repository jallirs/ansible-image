FROM docker.io/ubuntu:xenial

RUN set -ex ;\
    apt-get update ;\
    apt-get upgrade -y ;\
    apt-get install -y \
      python3 \
      python3-virtualenv \
      python3-dev \
      gcc \
      git \
      openssh-client

COPY install-ansible.sh /usr/local/bin/install-python-packages.sh

RUN /usr/local/bin/install-python-packages.sh \
      ansible \
      "ara[server]" \
      openstackclient \
      kubernetes \
      pyghmi \
      git+https://git.openstack.org/openstack/ospurge

ENV PATH=/var/lib/ansible-venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
