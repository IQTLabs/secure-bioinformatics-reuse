# Installation notes

## Emacs
    sudo snap install emacs --classic

## Conda
    diff Miniconda3-latest-Linux-x86_64.sh.sha256sum.actual Miniconda3-latest-Linux-x86_64.sh.sha256sum.expected
    bash Miniconda3-latest-Linux-x86_64.sh
    conda config --set auto_activate_base false

## Docker
    sudo apt-get update
    sudo apt-get install \
         apt-transport-https \
	 ca-certificates \
	 curl \
	 gnupg \
	 lsb-release
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo \
        "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install docker-ce docker-ce-cli containerd.io
    sudo docker run hello-world
    sudo groupadd docker
    sudo usermod -aG docker $USER
    newgrp docker 
    docker run hello-world
    sudo systemctl enable docker.service
    sudo systemctl enable containerd.service

## DTrace
    sudo apt install systemtap-sdt-dev

## Sysdig
    sudo apt install sysdig
