FROM docker.io/ubuntu:xenial

RUN set -ex ;\
    apt-get update ;\
    apt-get upgrade -y ;\
    apt-get install -y \
      python \
      virtualenv \
      python-dev \
      gcc \
      openssh-client

COPY install-ansible.sh /usr/local/bin/install-python-packages.sh

RUN /usr/local/bin/install-python-packages.sh \
      ansible \
      ara==0.16.5 \
      openstackclient \
      kubernetes \
      pyghmi \
      git+https://git.openstack.org/openstack/ospurge

ENV PATH=/var/lib/ansible-venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
