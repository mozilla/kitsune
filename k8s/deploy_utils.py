from env import TEMPLATE_DIR
import io
import jinja2
import os
import tempfile
import yaml


def get_kubectl():
    return os.environ.get('KUBECTL_BIN', 'kubectl')


def render_template(config, template_name):
    loader = jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
    tenv = jinja2.Environment(loader=loader)
    template = tenv.get_template(template_name)
    return template.render(config)


def k8s_apply(ctx, template_text, apply):
    namespace = ctx.config['K8S_NAMESPACE']

    f = tempfile.NamedTemporaryFile(prefix='k8s', suffix='yaml', delete=False)
    f.write(template_text.encode('utf-8'))
    f.write("\n".encode('utf-8'))
    f.flush()

    print("Rendering template to:", f.name)
    cmd = '{} apply -n {} -f {}'.format(get_kubectl(), namespace, f.name)
    print("Command:", cmd)
    if apply:
        ctx.run(cmd, echo=True)
    else:
        print("Please specify --apply to perform changes")


def k8s_delete_resource(ctx, resource_name, apply):
    namespace = ctx.config['K8S_NAMESPACE']
    cmd = '{} delete -n {} --ignore-not-found {}'.format(
        get_kubectl(), namespace, resource_name)
    print("Command:", cmd)
    if apply:
        ctx.run(cmd, echo=True)
    else:
        print("Please specify --apply to perform changes")
