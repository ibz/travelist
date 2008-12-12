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
               d['args'].append(arg.resolve(context))
           for key, value in self.kwargs.items():
               d['kwargs'][key] = d[key] = value.resolve(context)
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
   if argslist:
       for arg in argslist:
           if '=' in arg:
               k, v = arg.split('=', 1)
               kwargs[str(k).strip()] = parser.compile_filter(v.strip())
           else:
               args.append(parser.compile_filter(arg))
   return CallNode(path, *args, **kwargs)

register.tag('call', do_call)
