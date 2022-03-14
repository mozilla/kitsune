from env import TEMPLATE_DIR
import jinja2
import os
import tempfile

from invoke.config import DataProxy


def get_kubectl():
    return os.environ.get("KUBECTL_BIN", "kubectl")


def todict(obj, classkey=None):
    if isinstance(obj, dict):
        data = {}
        for (k, v) in list(obj.items()):
            data[k] = todict(v, classkey)
        return data
    elif isinstance(obj, DataProxy):
        data = dict(obj)
        for (k, v) in list(obj.items()):
            data[k] = todict(v, classkey)
        return data
    return obj


def render_template(config, template_name, app=None):
    loader = jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
    tenv = jinja2.Environment(loader=loader)
    template = tenv.get_template(template_name)
    config = todict(config)

    if app:
        config["kubernetes"].update(**config["kubernetes"]["apps"][app])
    return template.render(config)


def k8s_apply(ctx, template_text, apply, record=False):
    namespace = ctx.config["kubernetes"]["namespace"]
    with tempfile.NamedTemporaryFile(prefix="k8s", suffix=".yaml", delete=False) as f:
        f.write(template_text.encode("utf-8"))
        f.write("\n".encode("utf-8"))
        f.flush()

    print("Rendering template to:", f.name)
    if record:
        cmd = "{} apply -n {} -f {} --record".format(get_kubectl(), namespace, f.name)
    else:
        cmd = "{} apply -n {} -f {}".format(get_kubectl(), namespace, f.name)
    print("Command:", cmd)
    if apply:
        ctx.run(cmd, echo=True)
    else:
        print("Please specify --apply to perform changes")


def k8s_delete_resource(ctx, resource_name, apply):
    namespace = ctx.config["kubernetes"]["namespace"]
    cmd = "{} delete -n {} --ignore-not-found {}".format(get_kubectl(), namespace, resource_name)
    print("Command:", cmd)
    if apply:
        ctx.run(cmd, echo=True)
    else:
        print("Please specify --apply to perform changes")
