import jinja2

import glad
from glad.config import Config, ConfigOption
from glad.generator import JinjaGenerator
from glad.generator.util import (
    strip_specification_prefix,
    collect_alias_information,
    find_extensions_with_aliases,
    jinja2_contextfilter
)
from glad.parse import ParsedType, EnumType
from glad.sink import LoggingSink

def enum_type(enum, feature_set):
    return 'GLenum'

def enum_value(enum, feature_set):
    if enum.alias and enum.value is None:
        enum = feature_set.find_enum(enum.alias)

    # basically an alias to another enum (value contains another enum)
    # resolve it here and adjust value accordingly.
    referenced = feature_set.find_enum(enum.value)
    if referenced is None:
        pass
    elif referenced.parent_type is not None:
        # global value is a reference to a enum type value
        return '{}::{} as GLenum'.format(referenced.parent_type, enum.value)
    else:
        enum = referenced

    value = enum.value
    if value.endswith('"'):
        value = value[:-1] + r'\0"'
        return value

    # if enum.value.startswith('EGL_CAST'):
    #     # EGL_CAST(type,value) -> value as type
    #     type_, value = enum.value.split('(', 1)[1].rsplit(')', 1)[0].split(',')
    #     return '{} as {}'.format(value, type_)

    if enum.type == 'float' and value.endswith('F'):
        value = value[:-1]

    for old, new in (('(', ''), (')', ''), ('f', ''),
                     ('U', ''), ('L', '')):
        value = value.replace(old, new)

    return value


def to_clover_type(type):
    t = type.type
    if type.is_pointer > 0:
        t = t + '*'
    return t

def to_clover_params(command, mode='full'):
    if len(command.params) == 0:
        return 'void'
    if mode == 'names':
        return ', '.join(identifier(param.name) for param in command.params)
    elif mode == 'types':
        return ', '.join(to_clover_type(param.type) for param in command.params)
    elif mode == 'full':
        return ', '.join(
            '{type} {name}'.format(name=identifier(param.name), type=to_clover_type(param.type))
            for param in command.params
        )

    raise ValueError('invalid mode: ' + mode)

def identifier(name):
    if name in ['type']:
        return name + '_'
    return name

class CloverConfig(Config):
    ALIAS = ConfigOption(
        converter=bool,
        default=False,
        description='Automatically adds all extensions that ' +
                    'provide aliases for the current feature set.'
    )
    MX = ConfigOption(
        converter=bool,
        default=False,
        description='Enables support for multiple GL contexts'
    )

def clover_recase(name):
    name = name[0].lower() + name[1:]
    return name

class CloverGenerator(JinjaGenerator):
    DISPLAY_NAME = 'Clover'

    TEMPLATES = ['glad.generator.clover']
    Config = CloverConfig

    def __init__(self, *args, **kwargs):
        JinjaGenerator.__init__(self, *args, **kwargs)

        self.environment.filters.update(
            feature=lambda x: 'feature = "{}"'.format(x),
            enum_type=jinja2_contextfilter(lambda ctx, enum: enum_type(enum, ctx['feature_set'])),
            enum_value=jinja2_contextfilter(lambda ctx, enum: enum_value(enum, ctx['feature_set'])),
            type=to_clover_type,
            params=to_clover_params,
            param_types=lambda value: to_clover_params(value, 'types'),
            identifier=identifier,
            no_prefix=jinja2_contextfilter(lambda ctx, value: strip_specification_prefix(value, ctx['spec'])),
            no_prefix_func=jinja2_contextfilter(lambda ctx, value: clover_recase(strip_specification_prefix(value, ctx['spec'])))
        )

    @property
    def id(self):
        return 'clover'

    def select(self, spec, api, version, profile, extensions, config, sink=LoggingSink(__name__)):
        if extensions is not None:
            extensions = set(extensions)

            if config['ALIAS']:
                extensions.update(find_extensions_with_aliases(spec, api, version, profile, extensions))

        return JinjaGenerator.select(self, spec, api, version, profile, extensions, config, sink=sink)

    def get_template_arguments(self, spec, feature_set, config):
        args = JinjaGenerator.get_template_arguments(self, spec, feature_set, config)

        args.update(
            version=glad.__version__,
            aliases=collect_alias_information(feature_set.commands)
        )

        return args

    def get_templates(self, spec, feature_set, config):
        return [
            ('gl.cl', 'glad-{}/gl.cl'.format(feature_set.name))
        ]

    def modify_feature_set(self, spec, feature_set, config):
        return feature_set
