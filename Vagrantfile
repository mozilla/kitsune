# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "precise64"
  config.vm.box_url = "http://files.vagrantup.com/precise64.box"
  config.vm.provision :shell, :path => "bootstrap.sh"
  config.vm.network :private_network, ip: "192.168.33.11"
  config.vm.synced_folder ".", "/kitsune", :nfs => true
  config.vm.synced_folder ".", "/vagrant", :disabled => true

  config.vm.provider :virtualbox do |vb|
    vb.customize ["modifyvm", :id, "--memory", "2048"]
  end 
end
