FROM ubuntu:22.04

# Create program install folder
ENV PROGRAM_PATH /home/FloorPlanTo3D
RUN mkdir -p ${PROGRAM_PATH}

# Prevent prompt for timezone
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# Install required dependencies
RUN apt-get update && \
	apt-get install -y \
	curl \
	bzip2 \
	libfreetype6 \
	libgl1-mesa-dev \
	libglu1-mesa \
	libxi6 \
    libsm6 \
	xz-utils \
	libxrender1 \
    nano \
	dos2unix \
	clang \
    make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev git \
    libncursesw5-dev tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev \
	software-properties-common  && \
	apt-get -y autoremove && \
	rm -rf /var/lib/apt/lists/*


RUN curl -fsSL https://pyenv.run | bash
ENV HOME /root
ENV PYENV_ROOT $HOME/.pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH
RUN CC=clang pyenv install 3.6.13 && pyenv global 3.6.13

    
# Setup python
RUN python3.6 -m pip install --upgrade pip

# Setup dependencies
COPY ./requirements.txt ${PROGRAM_PATH}/requirements.txt
RUN python3.6 -m pip install --ignore-installed -r ${PROGRAM_PATH}/requirements.txt

COPY ./weights ${PROGRAM_PATH}/weights
COPY ./mrcnn ${PROGRAM_PATH}/mrcnn
COPY ./application.py ./MeshBuilder.py ./Wall.py ${PROGRAM_PATH}/

EXPOSE 8081

WORKDIR ${PROGRAM_PATH}
ENTRYPOINT python3.6 application.py