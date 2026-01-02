FROM rockylinux/rockylinux:8

RUN dnf install -y \
    epel-release

RUN dnf config-manager --set-enabled devel powertools

RUN dnf makecache --refresh

RUN dnf install -y \
    wget \
    curl \
    python39-devel \
    python39-setuptools \
    python39-pip \
    boost \
    boost-mpich \
    gcc-c++ \
    yaml-cpp \
    mpich \
    mpich-devel \
    git \
    xorg-x11-xauth \
    xerces-c-devel  \
    gsl-devel \
    git-lfs \
    git \
    cmake

RUN dnf install -y \
    xsd \
    zlib-devel

# Install Open Malaria 46.0
RUN git clone -b schema-46.0 --single-branch https://github.com/SwissTPH/openmalaria.git /openmalaria-schema-46.0 \
    && mkdir /openmalaria-schema-46.0/build \
    && cd /openmalaria-schema-46.0/build \
    && cmake .. \
    && cmake --build . --parallel 4

# Install Open Malaria XX.X
##RUN git clone -b schema-XX.X --single-branch https://github.com/SwissTPH/openmalaria.git /openmalaria-schema-XX.X
##RUN mkdir /openmalaria-schema-XX.X/build && cd /openmalaria-schema-XX.X/build && cmake .. && cmake --build . --parallel 4


RUN mkdir -p /opt/envs/
## INSTALL Python Environment
RUN python3.9 -m venv /opt/envs/mmmpy_local
COPY ../requirements_local.txt /requirements_local.txt
RUN . /opt/envs/mmmpy_local/bin/activate && python -m pip install -r /requirements_local.txt --extra-index-url=https://packages.idmod.org/api/pypi/pypi-production/simple
RUN python3.9 -m pip install pandas

## Install R
ENV R_VERSION=4.4.1
RUN curl -O https://cdn.rstudio.com/r/centos-8/pkgs/R-${R_VERSION}-1-1.x86_64.rpm \
    && dnf install -y R-${R_VERSION}-1-1.x86_64.rpm


# Set Environment Helpfully
ENV PATH=/opt/R/4.4.1/bin/:$PATH
ENV LD_LIBRARY_PATH=/usr/lib64/mpich/lib/

RUN dnf install -y \
    openssl-devel \
    fontconfig-devel \
    freetype-devel \
    libpng-devel \
    libtiff-devel \
    libjpeg-devel \
    libxml2-devel \
    harfbuzz-devel \
    fribidi-devel

## Install R packages
RUN echo 'local({r <- getOption("repos"); r["CRAN"] <- "https://cloud.r-project.org/"; options(repos = r)})' > /opt/R/4.4.1/lib/R/etc/Rprofile.site
COPY ../requirements_R.txt /requirements_R.txt
RUN Rscript /requirements_R.txt
