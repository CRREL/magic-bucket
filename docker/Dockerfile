FROM pdal/dependencies:latest
MAINTAINER Peter Gadomski <peter.j.gadomski@erdc.dren.mil>

ENV CC gcc
ENV CXX g++

ADD rivlib-2_5_3-x86_64-linux-gcc55.zip /
RUN unzip /rivlib-2_5_3-x86_64-linux-gcc55.zip
RUN rm /rivlib-2_5_3-x86_64-linux-gcc55.zip

RUN git clone https://github.com/PDAL/PDAL \
    && cd PDAL \
    && git checkout f61435 \
    && mkdir build \
    && cd build \
    && cmake \
        -DBUILD_PLUGIN_CPD=OFF \
        -DBUILD_PLUGIN_GREYHOUND=ON \
        -DBUILD_PLUGIN_HEXBIN=ON \
        -DBUILD_PLUGIN_ICEBRIDGE=ON \
        -DBUILD_PLUGIN_MRSID=ON \
        -DBUILD_PLUGIN_NITF=ON \
        -DBUILD_PLUGIN_OCI=OFF \
        -DBUILD_PLUGIN_PCL=OFF \
        -DBUILD_PLUGIN_PGPOINTCLOUD=ON \
        -DBUILD_PLUGIN_SQLITE=ON \
        -DBUILD_PLUGIN_RIVLIB=ON \
        -DBUILD_RIVLIB_TESTS=OFF \
        -DBUILD_PLUGIN_PYTHON=ON \
        -DCMAKE_INSTALL_PREFIX=/usr \
        -DENABLE_CTEST=OFF \
        -DWITH_LAZPERF=ON \
        -DWITH_LASZIP=ON \
        -DWITH_TESTS=OFF \
        -DCMAKE_BUILD_TYPE=Release \
        -DRiVLib_DIR=/rivlib-2_5_3-x86_64-linux-gcc55/cmake \
        .. \
    && make -j4 \
    && make install \
    && rm -rf /PDAL

RUN curl https://sh.rustup.rs -sSf | sh -s -- -y --no-modify-path
RUN /root/.cargo/bin/cargo install --git https://github.com/gadomski/ape

RUN pip install --upgrade pip
RUN pip install boto3 slackclient

ADD rimtatls-2_5-linux-x86_64.tar.gz /
RUN ln -s /rimtatls-linux-x86_64/rimtatls /usr/bin/rimtatls

ADD magic_bucket /magic_bucket
ADD main.py /
CMD ["./main.py"]

ARG SLACK_TOKEN
ENV SLACK_TOKEN ${SLACK_TOKEN}
