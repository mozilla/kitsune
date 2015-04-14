require "yaml"

# Load up our vagrant config files -- vagrantconfig.yaml first
_config = YAML.load(File.open(File.join(File.dirname(__FILE__),
                    "vagrantconfig.yaml"), File::RDONLY).read)

# Local-specific/not-git-managed config -- vagrantconfig_local.yaml
begin
    extra = YAML.load(File.open(File.join(File.dirname(__FILE__),
                      "vagrantconfig_local.yaml"), File::RDONLY).read)
    if extra
        _config.merge!(extra)
    end
rescue Errno::ENOENT # No vagrantconfig_local.yaml found -- that's OK; just
                     # use the defaults.
end

CONF = _config
MOUNT_POINT = '/home/vagrant/kitsune'

Vagrant::Config.run do |config|
    config.vm.box = "ubuntu/trusty32"
    config.vm.box_url = "https://atlas.hashicorp.com/ubuntu/boxes/trusty32/versions/14.04/providers/virtualbox.box"

    Vagrant.configure("1") do |config|
        config.vm.customize ["modifyvm", :id, "--memory", CONF['memory']]
    end

    Vagrant.configure("2") do |config|
        config.vm.provider "virtualbox" do |v|
          v.name = "KITSUNE_VM"
          v.customize ["modifyvm", :id, "--memory", CONF['memory']]
        end
    end

    config.vm.network :hostonly, "33.33.33.77"
    config.vm.forward_port 8000, 8000

    config.vm.share_folder("vagrant-root", MOUNT_POINT, ".")
    config.vm.provision "shell", path: "bin/vagrant_provision.sh"
end

