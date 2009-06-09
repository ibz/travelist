from django import template

import settings

register = template.Library()

class CallNode(template.Node):
    def __init__(self, template_name, *args, **kwargs):
        self.template_name = template_name
        self.args = args
        self.kwargs = kwargs

    def render(self, context):
        try:
            template_name = self.template_name.resolve(context)
            t = template.loader.get_template(template_name)
            d = {'args': [], 'kwargs': {}}
            for arg in self.args:
                d['args'].append(arg.resolve(context) if not isinstance(arg, (str, unicode)) else arg)
            for k, v in self.kwargs.items():
                d['kwargs'][k] = d[k] = v.resolve(context) if not isinstance(v, (str, unicode)) else v
            context.update(d)
            result = t.render(context)
            context.pop()
            return result
        except:
            if settings.TEMPLATE_DEBUG:
                raise
            else:
                return ""

def do_call(parser, token):
    bits = token.contents.split()
    if 'with' in bits:
        pos = bits.index('with')
        argslist = bits[pos + 1:]
        bits = bits[:pos]
    else:
        argslist = []
    if len(bits) != 2:
        raise template.TemplateSyntaxError("%r tag takes one argument: the name of the template to be included" % bits[0])
    path = parser.compile_filter(bits[1])
    args = []
    kwargs = {}
    def process_arg(k, v):
        if k:
            kwargs[str(k)] = v
        else:
            args.append(v)
    if argslist:
        str_arg = None
        for arg in argslist:
            if not str_arg:
                if "=" in arg:
                    k, v = arg.split("=", 1)
                else:
                    k, v = None, arg
                if v[0] == "\"":
                    str_arg = v[1:]
                else:
                    process_arg(k, parser.compile_filter(v))
            else:
                str_arg += " " + arg
                if str_arg[-1] == "\"":
                    str_arg = str_arg[:-1]
                    process_arg(k, str(str_arg))
                    str_arg = None
    print kwargs
    return CallNode(path, *args, **kwargs)

register.tag('call', do_call)
