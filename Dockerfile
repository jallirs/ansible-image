FROM docker.io/ubuntu:bionic

RUN set -ex ;\
    apt-get update ;\
    apt-get upgrade -y ;\
    apt-get install -y \
      python3 \
      python3-virtualenv \
      python3-dev \
      gcc \
      git \
      openssh-client --no-install-recommends

COPY install-ansible.sh /usr/local/bin/install-python-packages.sh

RUN /usr/local/bin/install-python-packages.sh \
      ansible \
      "Django>=2.1.5" \
      "djangorestframework>=3.9.1" \
      django-cors-headers \
      django-filter \
      django-health-check \
      "dynaconf[yaml]" \
      tzlocal \
      whitenoise \
      pygments \
      git+https://opendev.org/recordsansible/ara.git \
      openstackclient \
      kubernetes \
      pyghmi \
      git+https://git.openstack.org/openstack/ospurge

ENV PATH=/var/lib/ansible-venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
